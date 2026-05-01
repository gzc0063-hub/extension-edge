"""Farmer-facing display labels for internal engine codes."""

from __future__ import annotations


APP_NAME = "Extension Edge"

FORAGE_LABELS = {
    "bermuda_est": "Established bermudagrass",
    "perennial_grass": "Established perennial grass pasture or hayfield",
    "sorghum": "Forage sorghum",
    "legume": "Alfalfa, clover, lespedeza, or other legume forage",
    "fescue_conv": "Fescue conversion",
    "dormant_bermuda": "Dormant bermudagrass pasture",
    "pasture_renovation": "Pasture renovation",
    "winter_grain": "Winter grazing or grain crop",
}

LIVESTOCK_LABELS = {
    "NONE": "No livestock on this field",
    "BEEF": "Beef or non-lactating animals",
    "LACTATING_DAIRY": "Lactating dairy animals",
    "OTHER": "Other livestock",
}

LEGUME_LABELS = {
    "white_clover": "White clover",
    "red_clover": "Red clover",
    "alfalfa": "Alfalfa",
    "annual_lespedeza": "Annual lespedeza",
}

RUP_LABELS = {
    "any": "Can use Restricted Use Pesticides if labeled",
    "no_unrestricted_only": "Show only unrestricted products",
}


def title_case_code(value: str) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


def forage_label(value: str) -> str:
    return FORAGE_LABELS.get(value, title_case_code(value))


def livestock_label(value: str) -> str:
    return LIVESTOCK_LABELS.get(value, title_case_code(value))


def legume_label(value: str) -> str:
    return LEGUME_LABELS.get(value, title_case_code(value))


def weed_label(value: str) -> str:
    return title_case_code(value)


def rup_label(value: str) -> str:
    return RUP_LABELS.get(value, title_case_code(value))
