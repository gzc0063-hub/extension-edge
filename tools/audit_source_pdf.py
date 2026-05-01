from __future__ import annotations

"""Audit project CSVs against the IPM-0028A source PDF.

This is a maintenance-only helper, not part of the Streamlit app runtime.
It requires `pypdf` and, for protected PDFs, `cryptography` in the active
Python environment.
"""

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "audit"


def normalize(value: str) -> str:
    value = value.lower()
    value = value.replace("\u2019", "'").replace("\u2018", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize(value))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        filtered = (line for line in handle if not line.lstrip().startswith("#"))
        return list(csv.DictReader(filtered))


def split_names(value: str) -> list[str]:
    names: list[str] = []
    for chunk in re.split(r"\s*(?:,|/|\bor\b|\band\b)\s*", value):
        chunk = chunk.strip(" .;:")
        if len(chunk) >= 3:
            names.append(chunk)
    return names


def present(term: str, normalized_pages: list[str], compact_pages: list[str]) -> bool:
    if not term or term.lower() in {"unknown", "none", "true", "false"}:
        return True
    norm = normalize(term)
    if not norm:
        return True
    if any(norm in page for page in normalized_pages):
        return True
    squashed = compact(term)
    return bool(squashed and any(squashed in page for page in compact_pages))


def pages_for(term: str, normalized_pages: list[str], compact_pages: list[str]) -> list[int]:
    norm = normalize(term)
    squashed = compact(term)
    pages: list[int] = []
    for idx, page in enumerate(normalized_pages, start=1):
        if norm and norm in page:
            pages.append(idx)
            continue
        if squashed and squashed in compact_pages[idx - 1]:
            pages.append(idx)
    return pages


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: audit_source_pdf.py <source-pdf>", file=sys.stderr)
        return 2

    pdf_path = Path(sys.argv[1])
    OUT.mkdir(exist_ok=True)

    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    normalized_pages = [normalize(page) for page in pages]
    compact_pages = [compact(page) for page in pages]
    full_text = "\n\n".join(f"--- PDF PAGE {idx} ---\n{text}" for idx, text in enumerate(pages, start=1))
    (OUT / "source_pdf_text.txt").write_text(full_text, encoding="utf-8")

    herbicides = load_csv(DATA / "herbicides.csv")
    efficacy = load_csv(DATA / "efficacy.csv")
    restrictions = load_csv(DATA / "restrictions.csv")

    missing_trade_names: list[dict[str, str]] = []
    missing_active_ingredients: list[dict[str, str]] = []
    found_trade_pages: dict[str, list[int]] = {}

    for row in herbicides:
        trade_terms = split_names(row.get("trade_name", ""))
        if not trade_terms:
            trade_terms = [row.get("trade_name", "")]
        found_any_trade = False
        page_hits: list[int] = []
        for term in trade_terms:
            hit_pages = pages_for(term, normalized_pages, compact_pages)
            if hit_pages:
                found_any_trade = True
                page_hits.extend(hit_pages)
        if found_any_trade:
            found_trade_pages[row["unique_id"]] = sorted(set(page_hits))
        else:
            missing_trade_names.append(
                {
                    "unique_id": row.get("unique_id", ""),
                    "trade_name": row.get("trade_name", ""),
                    "guide_page_ref": row.get("guide_page_ref", ""),
                }
            )

        active_terms = [
            term
            for term in split_names(row.get("active_ingredient", ""))
            if term not in {"plus", "dimethylamine salt"}
        ]
        if active_terms and not any(present(term, normalized_pages, compact_pages) for term in active_terms):
            missing_active_ingredients.append(
                {
                    "unique_id": row.get("unique_id", ""),
                    "trade_name": row.get("trade_name", ""),
                    "active_ingredient": row.get("active_ingredient", ""),
                }
            )

    unique_ids = {row["unique_id"] for row in herbicides}
    efficacy_ids = {row["unique_id"] for row in efficacy}
    restriction_ids = {row["unique_id"] for row in restrictions if row.get("unique_id")}

    ratings_by_id = Counter(row["unique_id"] for row in efficacy)
    weeds_by_id: dict[str, set[str]] = defaultdict(set)
    missing_weed_terms: set[str] = set()
    for row in efficacy:
        weed = row.get("weed_id", "")
        weeds_by_id[row["unique_id"]].add(weed)
        readable = weed.replace("_", " ")
        if readable and not present(readable, normalized_pages, compact_pages):
            missing_weed_terms.add(weed)

    mowing_rules_text = (ROOT / "engine.py").read_text(encoding="utf-8")
    mowing_keys = sorted(set(re.findall(r'"([a-z0-9_]+)"\s*:\s*(?:ANNUAL_RULE|PERENNIAL_RULE|WOODY_RULE)', mowing_rules_text)))
    missing_mowing_terms = [
        key for key in mowing_keys if key != "_default" and not present(key.replace("_", " "), normalized_pages, compact_pages)
    ]

    summary = {
        "source_pdf": str(pdf_path),
        "pdf_pages": len(pages),
        "herbicide_rows": len(herbicides),
        "efficacy_rows": len(efficacy),
        "restrictions_rows": len(restrictions),
        "herbicide_unique_ids": len(unique_ids),
        "efficacy_unique_ids": len(efficacy_ids),
        "efficacy_ids_not_in_herbicides": sorted(efficacy_ids - unique_ids),
        "herbicide_ids_without_efficacy": sorted(unique_ids - efficacy_ids),
        "restriction_ids_not_in_herbicides": sorted(restriction_ids - unique_ids),
        "duplicate_herbicide_ids": sorted([key for key, count in Counter(row["unique_id"] for row in herbicides).items() if count > 1]),
        "missing_trade_names": missing_trade_names,
        "missing_active_ingredients": missing_active_ingredients,
        "missing_weed_terms_in_pdf_text": sorted(missing_weed_terms),
        "missing_mowing_terms_in_pdf_text": missing_mowing_terms,
        "trade_name_pdf_pages": found_trade_pages,
        "efficacy_rating_count_by_id": dict(sorted(ratings_by_id.items())),
        "efficacy_weeds_by_id": {key: sorted(value) for key, value in sorted(weeds_by_id.items())},
    }

    (OUT / "source_pdf_audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({k: summary[k] for k in [
        "pdf_pages",
        "herbicide_rows",
        "efficacy_rows",
        "restrictions_rows",
        "herbicide_unique_ids",
        "efficacy_unique_ids",
        "efficacy_ids_not_in_herbicides",
        "herbicide_ids_without_efficacy",
        "restriction_ids_not_in_herbicides",
        "duplicate_herbicide_ids",
        "missing_trade_names",
        "missing_active_ingredients",
    ]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
