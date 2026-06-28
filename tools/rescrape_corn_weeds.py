from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "src" / "data" / "corn_weeds.json"

WEEDS = [
    "Barnyardgrass",
    "Broadleaf signalgrass",
    "Fall panicum",
    "Foxtail",
    "Goosegrass",
    "Johnsongrass (rhizome)",
    "Johnsongrass (seedling)",
    "Italian ryegrass",
    "Large crabgrass",
    "Annual sedge",
    "Purple nutsedge",
    "Yellow nutsedge",
    "Bristly starbur",
    "Carolina geranium",
    "Chickweed",
    "Common cocklebur",
    "Showy crotolaria",
    "Common ragweed",
    "Cutleaf eveningprimrose",
    "Henbit",
    "Horsenettle",
    "Horseweed",
    "Jimsonweed",
    "Lambsquarter",
    "Morningglory",
    "Palmer pigweed",
    "Smooth pigweed",
    "Prickly sida",
    "Common purslane",
    "Hemp sesbania",
    "Sicklepod",
    "Smartweed",
    "Tropic croton",
    "Velvetleaf",
    "Wild radish",
]

PRODUCT_BLOCKS = [
    {
        "page": 46,
        "application_types": ["BURNDOWN", "BURNDOWN", "BURNDOWN", "BURNDOWN", "BURNDOWN", "PRE", "PRE"],
        "products": [
            ("Aim", "14"),
            ("Clarity", "4"),
            ("Glyphosate", "9"),
            ("2,4-D", "4"),
            ("Gramoxone", "22"),
            ("Atrazine", "5"),
            ("Bicep II Magnum, etc.", "5 + 15"),
        ],
        "ratings": {
            "Barnyardgrass": ["N", "N", "E", "N", "F-G", "F", "G"],
            "Broadleaf signalgrass": ["N", "N", "G-E", "N", "F-G", "P", "G"],
            "Fall panicum": ["N", "N", "G", "N", "F-G", "P", "E"],
            "Foxtail": ["N", "N", "E", "N", "F-G", "F"],
            "Goosegrass": ["N", "N", "E", "N", "F-G", "F", "E"],
            "Johnsongrass (rhizome)": ["N", "N", "P", "N", "P", "N", "F"],
            "Johnsongrass (seedling)": ["N", "N", "E", "N", "G", "N", "G"],
            "Italian ryegrass": ["N", "N", "F-G", "N", "F", "G"],
            "Large crabgrass": ["N", "N", "G", "N", "F-G", "F-G", "E"],
            "Annual sedge": ["N", "N", "E", "N", "G", "P", "F"],
            "Purple nutsedge": ["N", "N", "F", "N", "P", "P", "P"],
            "Yellow nutsedge": ["N", "N", "F-G", "N", "P", "P", "P"],
            "Bristly starbur": ["P", "E", "G", "G", "G"],
            "Carolina geranium": ["G", "F", "F-G", "G-E", "G"],
            "Chickweed": ["G", "E", "G-E", "E", "G"],
            "Common cocklebur": ["E", "E", "G", "E", "G", "G-E", "G"],
            "Showy crotolaria": ["F", "G", "G", "G", "G", "G-E"],
            "Common ragweed": ["G", "E", "G", "E", "E", "E"],
            "Cutleaf eveningprimrose": ["F", "F", "P-F", "F", "G"],
            "Henbit": ["F", "F", "F", "G", "G"],
            "Horsenettle": ["F", "P", "P", "P", "P"],
            "Horseweed": ["P", "F-G", "P", "G", "F"],
            "Jimsonweed": ["G", "E", "G", "E", "G", "E"],
            "Lambsquarter": ["F-G", "E", "G", "E", "F-G", "E", "E"],
            "Morningglory": ["E", "E", "F-G", "G", "G", "G", "G"],
            "Palmer pigweed": ["G-E", "G-E", "G-E", "G-E", "G", "E", "E"],
            "Smooth pigweed": ["G", "G-E", "G-E", "G-E", "G", "E", "E"],
            "Prickly sida": ["F-G", "E", "G", "G", "F-G", "E", "G"],
            "Common purslane": ["G", "E", "G", "G", "G", "E"],
            "Hemp sesbania": ["E", "F", "G", "P-F", "E", "F"],
            "Sicklepod": ["P", "E", "G", "E", "G", "F-G", "F"],
            "Smartweed": ["G", "E", "G", "P-F", "E", "G-E"],
            "Tropic croton": ["G", "G", "G", "E", "G"],
            "Velvetleaf": ["E", "P", "G", "G", "G", "G"],
            "Wild radish": ["G-E", "G", "G", "G", "G"],
        },
    },
    {
        "page": 47,
        "application_types": ["PRE", "PRE", "PRE", "PRE", "POST", "POST", "POST"],
        "products": [
            ("Prowl H2O", "3"),
            ("Sharpen", "14"),
            ("Verdict", "14 + 15"),
            ("Zidua", "15"),
            ("2,4-D", "4"),
            ("Accent", "2"),
            ("Armezon / Impact", "27"),
        ],
        "ratings": {
            "Barnyardgrass": ["G", "P", "G", "E", "P", "G", "F-G"],
            "Broadleaf signalgrass": ["F", "P", "F", "G", "P", "G", "G"],
            "Fall panicum": ["G", "P", "G", "P", "G-E", "F"],
            "Foxtail": ["P", "P", "E"],
            "Goosegrass": ["G", "P", "G", "E", "P", "G-E", "F"],
            "Johnsongrass (rhizome)": ["P", "N", "P", "N", "E", "P"],
            "Johnsongrass (seedling)": ["F", "P", "F", "P", "E", "F"],
            "Italian ryegrass": ["F", "P", "E", "P", "G", "P"],
            "Large crabgrass": ["G", "P", "E", "P", "P", "G"],
            "Annual sedge": ["N", "P", "P", "P"],
            "Purple nutsedge": ["N", "N", "P", "P", "P", "P"],
            "Yellow nutsedge": ["N", "N", "P", "P", "P", "P"],
            "Common cocklebur": ["E", "F", "F", "P", "E", "F", "E"],
            "Horseweed": ["G-E", "E", "F", "F-G", "P"],
            "Morningglory": ["P", "F", "F", "E", "F-G", "F-G"],
            "Palmer pigweed": ["F", "E", "E", "G", "G", "P-F", "G"],
            "Smooth pigweed": ["G", "E", "E", "G", "E", "G", "E"],
            "Hemp sesbania": ["F", "F", "P", "F", "F-G"],
            "Sicklepod": ["P", "P", "G", "P-F", "P-F"],
            "Smartweed": ["F", "G"],
        },
    },
    {
        "page": 48,
        "application_types": ["POST"] * 7,
        "products": [
            ("Atrazine + Oil", "5"),
            ("Atrazine + Dual II Magnum", "5 + 15"),
            ("Basagran", "6"),
            ("Callisto", "27"),
            ("Capreno", "2 + 27"),
            ("Clarity, etc.", "4"),
            ("Glyphosate (RR only)", "9"),
        ],
        "ratings": {
            "Barnyardgrass": ["P", "F", "P", "F-G", "G", "P", "E"],
            "Broadleaf signalgrass": ["F", "P", "P", "F", "G", "P", "G"],
            "Fall panicum": ["F", "P", "P", "F-G", "P", "P", "E"],
            "Foxtail": ["F-G", "F-G", "P", "P", "P", "P", "E"],
            "Goosegrass": ["F-G", "F", "P", "P", "P", "P", "E"],
            "Johnsongrass (rhizome)": ["N", "N", "P", "P", "P", "P", "F-G"],
            "Johnsongrass (seedling)": ["N", "P", "P", "P", "F-G", "P", "E"],
            "Large crabgrass": ["F", "F", "P", "F-G", "G", "P", "G-E"],
            "Annual sedge": ["P", "P", "F", "P", "G"],
            "Purple nutsedge": ["P", "P", "P", "P-F", "P", "G"],
            "Yellow nutsedge": ["P", "F-G", "F", "P-F", "P", "G"],
            "Bristly starbur": ["G", "E", "E", "E"],
            "Carolina geranium": ["E", "E"],
            "Common cocklebur": ["E", "E", "E", "G-E", "G", "E", "E"],
            "Showy crotolaria": ["G", "G", "P", "P", "G", "G"],
            "Common ragweed": ["G", "G", "F", "P", "E", "E"],
            "Horsenettle": ["P", "P", "P", "P"],
            "Horseweed": ["P", "P", "N", "P", "G", "G"],
            "Jimsonweed": ["E", "E", "E", "G-E", "E", "E"],
            "Lambsquarter": ["E", "E", "P", "G-E", "E", "E", "E"],
            "Morningglory": ["E", "E", "P", "F-G", "G", "E", "E"],
            "Palmer pigweed": ["E", "E", "P", "G", "E", "G", "G-E"],
            "Smooth pigweed": ["E", "E", "P", "G", "E", "G", "G-E"],
            "Prickly sida": ["E", "E", "G", "P", "F-G", "G", "G"],
            "Common purslane": ["E", "E", "P", "E", "G"],
            "Hemp sesbania": ["F-G", "F-G", "P", "E", "F"],
            "Sicklepod": ["G", "G", "P", "P", "F-G", "G", "G-E"],
            "Smartweed": ["G-E", "G-E", "G-E", "G-E", "E", "G-E"],
            "Tropic croton": ["G", "G", "P", "G", "G"],
            "Velvetleaf": ["E", "E", "G-E", "F-G", "F"],
            "Wild radish": ["F", "G-E", "G"],
        },
    },
    {
        "page": 49,
        "application_types": ["POST", "POST", "POST", "POST", "POST", "POST", "PDS"],
        "products": [
            ("Halex GT (RR only)", "15 + 9 + 27"),
            ("Laudis", "27"),
            ("Liberty 280 (LibertyLink only)", "10"),
            ("Permit", "2 + 2"),
            ("Realm Q", "2 + 27"),
            ("Status", "4 + 19"),
            ("Gramoxone SL", "22"),
        ],
        "ratings": {
            "Barnyardgrass": ["E", "F", "N", "P", "G", "P", "G"],
            "Broadleaf signalgrass": ["E", "G", "G", "P", "F-G", "P", "G"],
            "Fall panicum": ["E", "G", "P", "G", "P", "G"],
            "Foxtail": ["E", "G", "P", "P", "G"],
            "Goosegrass": ["E", "F", "G", "P", "G", "P", "G"],
            "Johnsongrass (rhizome)": ["E", "P", "P", "P", "F-G", "P", "P"],
            "Johnsongrass (seedling)": ["E", "P-F", "G", "P", "E", "P", "G"],
            "Italian ryegrass": ["E", "G", "P", "P", "N", "G"],
            "Large crabgrass": ["E", "G", "G", "P", "G", "P", "G"],
            "Annual sedge": ["G", "G", "E", "G", "N", "F"],
            "Purple nutsedge": ["P", "G", "F", "N", "F"],
            "Yellow nutsedge": ["P", "E", "N", "F"],
            "Common cocklebur": ["E", "G", "E", "G-E", "E", "E", "G"],
            "Common ragweed": ["G", "G", "G"],
            "Horseweed": ["F-G", "G-E", "P", "G-E", "P"],
            "Lambsquarter": ["G", "E", "E", "P-F", "G", "E", "F-G"],
            "Morningglory": ["G", "G", "E", "F", "G", "E", "G"],
            "Palmer pigweed": ["E", "G", "F-G", "F", "G", "E", "G"],
            "Smooth pigweed": ["E", "G", "G", "G", "G", "E", "G"],
            "Prickly sida": ["E", "F-G", "F", "F-G", "E", "E", "F-G"],
            "Hemp sesbania": ["G", "E", "F-G", "P-F"],
            "Sicklepod": ["E", "F-G", "E", "P", "F-G", "E", "G"],
            "Smartweed": ["G", "G-E", "F-G"],
            "Velvetleaf": ["E", "F", "E"],
            "Wild radish": ["F", "G-E", "G"],
        },
    },
    {
        "page": 50,
        "application_types": ["HARVEST_AID", "HARVEST_AID", "HARVEST_AID"],
        "products": [("2,4-D", "4"), ("Glyphosate", "9"), ("Aim", "14")],
        "ratings": {
            "Barnyardgrass": ["N", "G", "P"],
            "Broadleaf signalgrass": ["N", "E", "N"],
            "Fall panicum": ["P", "E", "N"],
            "Goosegrass": ["P", "E", "N"],
            "Johnsongrass (rhizome)": ["N", "E", "N"],
            "Johnsongrass (seedling)": ["N", "E", "N"],
            "Italian ryegrass": ["N", "G", "N"],
            "Large crabgrass": ["N", "E", "N"],
            "Purple nutsedge": ["P", "F-G", "N"],
            "Yellow nutsedge": ["P", "F", "N"],
            "Common cocklebur": ["E", "G", "G"],
            "Showy crotolaria": ["G", "G", "F"],
            "Common ragweed": ["E", "G", "F"],
            "Jimsonweed": ["E", "G", "G"],
            "Lambsquarter": ["E", "G", "G-E"],
            "Morningglory": ["E", "F-G", "E"],
            "Palmer pigweed": ["E", "G-E", "G-E"],
            "Smooth pigweed": ["E", "G-E", "G-E"],
            "Prickly sida": ["G", "G", "F"],
            "Common purslane": ["G", "G", "G"],
            "Hemp sesbania": ["E", "F"],
            "Sicklepod": ["G", "G-E", "P"],
            "Smartweed": ["P-F", "G-E", "G"],
            "Tropic croton": ["G", "G", "G"],
            "Velvetleaf": ["G", "G", "E"],
            "Wild radish": ["G", "F-G"],
        },
    },
]


def weed_key(name: str) -> str:
    key = name.lower()
    key = key.replace("2,4-d", "24d")
    key = re.sub(r"[^a-z0-9]+", "_", key)
    return key.strip("_")


def normalize_rating(rating: str) -> str:
    rating = rating.replace("\u2013", "-").replace("\u2014", "-").replace("\ufffd", "-")
    rating = rating.replace("P-F", "P").replace("F-G", "F").replace("G-E", "G")
    return rating.strip().upper()


def main() -> int:
    records = []
    seen: dict[str, int] = {}

    for block in PRODUCT_BLOCKS:
        for index, (product, group) in enumerate(block["products"]):
            timing = block["application_types"][index]
            efficacy = {}
            for weed, ratings in block["ratings"].items():
                if index < len(ratings):
                    rating = normalize_rating(ratings[index])
                    if rating in {"E", "G", "F", "P", "N"}:
                        efficacy[weed_key(weed)] = rating

            if not efficacy:
                continue

            slug = weed_key(product).upper()
            seen[slug] = seen.get(slug, 0) + 1
            suffix = f"-{seen[slug]}" if seen[slug] > 1 else ""
            records.append(
                {
                    "unique_id": f"IPM-CORN-T12-{slug}{suffix}",
                    "trade_name": product,
                    "active_ingredient": "See source guide/label",
                    "herbicide_group": group,
                    "application_type": timing,
                    "soil_texture_restriction": None,
                    "plantback_restriction": "See source guide/label",
                    "phi_days": None,
                    "rup_flag": False,
                    "rate_per_acre": "See source guide/label",
                    "efficacy": dict(sorted(efficacy.items())),
                    "comments": f"Rescraped from Corn 2025 Table 12 weed response matrix, page {block['page']}. Ratings: E >90%, G 80-90%, F 70-80%, P <70%, N no control. Verify label and source guide for rate, timing, crop stage, RUP status, and restrictions before use.",
                }
            )

    OUT.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "records": len(records), "weed_keys": len({key for row in records for key in row["efficacy"]})}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
