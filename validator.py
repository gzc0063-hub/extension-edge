"""
validator.py — Validates user input completeness and legality before
the engine evaluates any rules. Catches malformed input early so the
engine never has to defend against missing fields.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


# Allowed enum values — kept in sync with the herbicides.csv schema.
FORAGE_TYPES = {
    "bermuda_est", "perennial_grass", "sorghum", "legume",
    "fescue_conv", "dormant_bermuda", "pasture_renovation", "winter_grain",
}
LIVESTOCK = {"NONE", "BEEF", "LACTATING_DAIRY", "OTHER"}
RUP_STATUS = {"any", "no_unrestricted_only"}


@dataclass
class UserInput:
    field_id: str
    forage: str
    weeds: List[str]                          # ordered by priority

    livestock: str = "NONE"                   # NONE / BEEF / LACTATING_DAIRY / OTHER
    hold_days: Optional[int] = None           # used only for LACTATING_DAIRY

    legumes_present: bool = False
    legumes: List[str] = field(default_factory=list)  # e.g., ["white_clover", "red_clover"]

    next_cut_days: Optional[int] = None       # days until next hay cut
    days_since_mow: Optional[int] = None

    slaughter_30d: bool = False
    hay_off_farm: bool = False
    manure_off: bool = False
    sensitive_crops_nearby: bool = False
    rup_status: str = "any"

    # Optional metadata for the PDF
    farm_name: str = ""
    operator_name: str = ""
    location: str = ""


def validate(ui: UserInput) -> List[str]:
    """Return a list of human-readable errors. Empty list means valid."""
    errors: List[str] = []

    if not ui.field_id:
        errors.append("Field ID is required.")

    if not ui.forage:
        errors.append("Forage type is required.")
    elif ui.forage not in FORAGE_TYPES:
        errors.append(
            f"Forage '{ui.forage}' not recognized. Allowed: {sorted(FORAGE_TYPES)}"
        )

    if not ui.weeds:
        errors.append("Select at least one target weed.")
    elif len(ui.weeds) != len(set(ui.weeds)):
        errors.append("Duplicate weeds in priority list.")

    if ui.livestock not in LIVESTOCK:
        errors.append(f"Livestock '{ui.livestock}' not recognized. Allowed: {sorted(LIVESTOCK)}")

    if ui.livestock == "LACTATING_DAIRY":
        if ui.hold_days is None:
            errors.append("Lactating dairy selected but animal hold days not specified.")
        elif ui.hold_days < 0:
            errors.append("Hold days cannot be negative.")

    if ui.legumes_present and not ui.legumes:
        errors.append("Legumes marked present but no legume species selected.")

    if ui.next_cut_days is not None and ui.next_cut_days < 0:
        errors.append("Days until next cut cannot be negative.")

    if ui.days_since_mow is not None and ui.days_since_mow < 0:
        errors.append("Days since last mow cannot be negative.")

    if ui.rup_status not in RUP_STATUS:
        errors.append(f"RUP status '{ui.rup_status}' not recognized.")

    return errors
