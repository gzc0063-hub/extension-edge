from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WEB_DATA = ROOT / "web" / "src" / "data"
PDF_DIR = DATA / "pdf_guides"
AUDIT = ROOT / "audit"
PDF_TEXT_DIR = AUDIT / "pdf_text"
PDF_TABLE_DIR = AUDIT / "pdf_tables"


DATASET_GUIDES = {
    "herbicides.json": "IPM-0028-A_PastureForageCropsWeedControl-2026_031626L-G.pdf",
    "efficacy.json": "IPM-0028-A_PastureForageCropsWeedControl-2026_031626L-G.pdf",
    "soybean_weeds.json": "IPM-0413_Soybean2025_121324L-G.pdf",
    "cotton_weeds.json": "IPM-0415_Cotton2025_121624L-G.pdf",
    "cotton_insects.json": "IPM-0415-A_Cotton-Insect-Control-2026_021126a-G.pdf",
    "corn_weeds.json": "IPM-0428_Corn2025_011725L.pdf",
    "peanut_weeds.json": "IPM-0360_Peanuts2025_121624L-G.pdf",
}

REQUIRED_FIELDS = {
    "herbicides.json": ["unique_id", "trade_name", "forage_type", "application_type", "rate_per_acre"],
    "efficacy.json": ["unique_id", "weed_id", "rating"],
    "soybean_weeds.json": ["unique_id", "trade_name", "application_type", "rate_per_acre", "efficacy"],
    "cotton_weeds.json": ["unique_id", "trade_name", "application_type", "rate_per_acre", "efficacy"],
    "corn_weeds.json": ["unique_id", "trade_name", "application_type", "rate_per_acre", "efficacy"],
    "peanut_weeds.json": ["unique_id", "trade_name", "application_type", "rate_per_acre", "efficacy"],
    "cotton_insects.json": ["unique_id", "trade_name", "pest_target", "rate_per_acre"],
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        filtered = (line for line in handle if not line.lstrip().startswith("#"))
        return list(csv.DictReader(filtered))


def normalize_text(value: str) -> str:
    value = value.lower()
    value = value.replace("\u2019", "'").replace("\u2018", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def summarize_json(name: str, rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        return {"row_count": None, "error": "dataset is not a list"}

    required = REQUIRED_FIELDS.get(name, [])
    unique_ids = [row.get("unique_id") for row in rows if isinstance(row, dict) and row.get("unique_id")]
    duplicate_ids = sorted([key for key, count in Counter(unique_ids).items() if count > 1])
    missing_required: dict[str, list[int]] = {}
    all_fields: set[str] = set()
    weed_keys: set[str] = set()

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        all_fields.update(row.keys())
        for field in required:
            if row.get(field) in (None, ""):
                missing_required.setdefault(field, []).append(index)
        efficacy = row.get("efficacy")
        if isinstance(efficacy, dict):
            weed_keys.update(str(key) for key in efficacy.keys())

    return {
        "row_count": len(rows),
        "field_names": sorted(all_fields),
        "duplicate_unique_ids": duplicate_ids,
        "missing_required": missing_required,
        "efficacy_weed_count": len(weed_keys),
        "efficacy_weeds": sorted(weed_keys),
    }


def scrape_pdf(pdf_path: Path) -> dict[str, Any]:
    reader = PdfReader(str(pdf_path))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(f"--- PAGE {index} ---\n{page}" for index, page in enumerate(page_texts, start=1))
    text_path = PDF_TEXT_DIR / f"{pdf_path.stem}.txt"
    text_path.write_text(text, encoding="utf-8")

    table_count = 0
    table_rows = 0
    table_path = PDF_TABLE_DIR / f"{pdf_path.stem}.json"
    tables: list[dict[str, Any]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            for table_index, table in enumerate(page.extract_tables(), start=1):
                table_count += 1
                table_rows += len(table)
                tables.append({"page": page_index, "table": table_index, "rows": table})
    table_path.write_text(json.dumps(tables, indent=2), encoding="utf-8")

    normalized = normalize_text(text)
    return {
        "file": pdf_path.name,
        "pages": len(page_texts),
        "text_chars": len(text),
        "tables": table_count,
        "table_rows": table_rows,
        "text_output": str(text_path.relative_to(ROOT)),
        "table_output": str(table_path.relative_to(ROOT)),
        "mentions_herbicide": "herbicide" in normalized,
        "mentions_insect": "insect" in normalized,
        "mentions_weed": "weed" in normalized,
    }


def main() -> int:
    AUDIT.mkdir(exist_ok=True)
    PDF_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    PDF_TABLE_DIR.mkdir(parents=True, exist_ok=True)

    json_summaries: dict[str, Any] = {}
    for path in sorted(WEB_DATA.glob("*.json")):
        json_summaries[path.name] = summarize_json(path.name, load_json(path))

    csv_summaries = {}
    for path in sorted(DATA.glob("*.csv")):
        rows = load_csv(path)
        csv_summaries[path.name] = {
            "row_count": len(rows),
            "field_names": list(rows[0].keys()) if rows else [],
            "duplicate_unique_ids": sorted(
                [key for key, count in Counter(row.get("unique_id") for row in rows if row.get("unique_id")).items() if count > 1]
            ),
        }

    csv_json_parity = {}
    for csv_name, json_name in {
        "herbicides.csv": "herbicides.json",
        "efficacy.csv": "efficacy.json",
        "restrictions.csv": "restrictions.json",
    }.items():
        csv_rows = csv_summaries.get(csv_name, {}).get("row_count")
        json_rows = json_summaries.get(json_name, {}).get("row_count")
        csv_json_parity[f"{csv_name}->{json_name}"] = {
            "csv_rows": csv_rows,
            "json_rows": json_rows,
            "matches": csv_rows == json_rows,
        }

    pdf_summaries = [scrape_pdf(path) for path in sorted(PDF_DIR.glob("*.pdf"))]
    represented_pdfs = set(DATASET_GUIDES.values())
    all_pdf_names = {item["file"] for item in pdf_summaries}

    report = {
        "json": json_summaries,
        "csv": csv_summaries,
        "csv_json_parity": csv_json_parity,
        "pdf_guides": pdf_summaries,
        "dataset_to_pdf": DATASET_GUIDES,
        "pdfs_represented_by_current_app_data": sorted(represented_pdfs & all_pdf_names),
        "pdfs_not_represented_by_current_app_data": sorted(all_pdf_names - represented_pdfs),
        "datasets_without_source_pdf_mapping": sorted(set(json_summaries) - set(DATASET_GUIDES) - {"restrictions.json"}),
    }

    report_path = AUDIT / "all_crop_source_audit.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({
        "report": str(report_path.relative_to(ROOT)),
        "json_files": len(json_summaries),
        "pdf_guides": len(pdf_summaries),
        "pdfs_not_represented_by_current_app_data": report["pdfs_not_represented_by_current_app_data"],
        "csv_json_parity": csv_json_parity,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
