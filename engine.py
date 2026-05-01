"""
engine.py — Hard-filter pipeline and shared types.

Source of truth: ACES IPM-0028A (2026).
Engine version: 2.0 (deterministic, no AI runtime dependencies).

The engine runs every herbicide labeled for the producer's forage type
through 9 independent gates derived directly from the guide:

    1. Forage scenario      6. Off-farm hay
    2. Legume protection    7. Off-farm manure
    3. Lactating dairy      8. Volatilization
    4. Pre-slaughter        9. Mowing timing
    5. Hay PHI              (RUP gate is also enforced)

Outcomes per product:
    APPROVED       — passes every gate, eligible for ranking
    REJECTED       — violates at least one gate; itemized reason
    MANUAL_REVIEW  — guide is silent on a relevant field; never assumed safe
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd

# ---------------------------------------------------------------------------
# Engine + guide version (stamped on every Result and PDF for audit trace)
# ---------------------------------------------------------------------------
ENGINE_VERSION = "2.0"
GUIDE_VERSION = "IPM-0028A (2026)"

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
class Status:
    INVALID_INPUT           = "INVALID_INPUT"
    RECOMMEND               = "RECOMMEND"
    RECOMMEND_WITH_WARNINGS = "RECOMMEND_WITH_WARNINGS"
    NO_SINGLE_PRODUCT       = "NO_SINGLE_PRODUCT"
    NO_LEGAL_RECOMMENDATION = "NO_LEGAL_RECOMMENDATION"
    MANUAL_REVIEW           = "MANUAL_REVIEW"


class VerdictKind:
    APPROVE        = "APPROVE"
    REJECT         = "REJECT"
    MANUAL_REVIEW  = "MANUAL_REVIEW"


# ---------------------------------------------------------------------------
# Verdict and Result containers
# ---------------------------------------------------------------------------
@dataclass
class Verdict:
    kind: str
    reason: str = ""
    gate: str = ""

    @classmethod
    def approve(cls):
        return cls(kind=VerdictKind.APPROVE)

    @classmethod
    def reject(cls, reason: str, gate: str = ""):
        return cls(kind=VerdictKind.REJECT, reason=reason, gate=gate)

    @classmethod
    def review(cls, reason: str, gate: str = ""):
        return cls(kind=VerdictKind.MANUAL_REVIEW, reason=reason, gate=gate)


@dataclass
class Result:
    status: str
    field_id: str = ""
    timestamp: str = ""
    engine_version: str = ENGINE_VERSION
    guide_version: str = GUIDE_VERSION

    best: Optional[Dict[str, Any]] = None
    backup: Optional[Dict[str, Any]] = None
    partial_options: List[Dict[str, Any]] = field(default_factory=list)

    approved: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Tuple[Dict[str, Any], str, str]] = field(default_factory=list)
    review:   List[Tuple[Dict[str, Any], str, str]] = field(default_factory=list)

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    primary_reason: str = ""
    what_could_change: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mowing rules — derived directly from IPM-0028A (2026), p.1
# "Integrating Mowing and Herbicides".
#
# The guide defines three plant-category windows:
#
#   ANNUAL weeds:
#       "For most annual weeds, do not mow for two weeks either before or
#        after spraying. This ensures enough regrowth after mowing but before
#        spraying for the weed to be able to absorb sufficient herbicides."
#       => 14 days before / 14 days after
#
#   HERBACEOUS PERENNIALS:
#       "For herbaceous perennials, spraying should be delayed after mowing
#        until flowering or when there is 12 to 24 inches of regrowth."
#       => 30 days before (conservative; flowering window) / 30 days after
#
#   WOODY PLANTS / VINES:
#       "After mowing blackberries or any woody species. You must have at
#        least one year's worth of growth to have enough foliage to take in
#        enough herbicide. Do not spray until the following growing season…
#        do not mow for at least 2 months after treatment or until woody
#        stems are dead."
#       => "next_season" before / 60 days after
#
# Individual weeds are mapped to one of these categories below. The category
# rule is the agronomic floor; the per-product fields product_mow_wait_*
# in herbicides.csv may impose additional restrictions, and both are checked.
# ---------------------------------------------------------------------------
ANNUAL_RULE = {
    "before_days": 14,
    "after_days": 14,
    "category": "annual",
    "source": "IPM-0028A p.1: 'For most annual weeds, do not mow for two weeks either before or after spraying.'",
}
PERENNIAL_RULE = {
    "before_days": 30,
    "after_days": 30,
    "category": "herbaceous_perennial",
    "source": "IPM-0028A p.1: 'For herbaceous perennials, spraying should be delayed after mowing until flowering or when there is 12 to 24 inches of regrowth.'",
}
WOODY_RULE = {
    "before_days": "next_season",
    "after_days": 60,
    "category": "woody",
    "source": "IPM-0028A p.1: 'You must have at least one year's worth of growth… Do not spray until the following growing season… do not mow for at least 2 months after treatment.'",
}

MOWING_RULES: Dict[str, Dict[str, Any]] = {
    # ---- ANNUAL grasses ----
    "barnyardgrass":            ANNUAL_RULE,
    "crabgrass":                ANNUAL_RULE,
    "fall_panicum":             ANNUAL_RULE,
    "foxtail":                  ANNUAL_RULE,
    "annual_foxtail":           ANNUAL_RULE,
    "goosegrass":               ANNUAL_RULE,
    "italian_ryegrass":         ANNUAL_RULE,
    "ryegrass":                 ANNUAL_RULE,
    "sandbur":                  ANNUAL_RULE,
    "signalgrass":              ANNUAL_RULE,
    "broadleaf_signalgrass":    ANNUAL_RULE,
    "texas_panicum":            ANNUAL_RULE,
    "johnsongrass_seedling":    ANNUAL_RULE,
    "little_barley":            ANNUAL_RULE,
    "wildoats":                 ANNUAL_RULE,

    # ---- ANNUAL broadleaves ----
    "spiny_amaranth":           ANNUAL_RULE,
    "spiny_pigweed":            ANNUAL_RULE,
    "redroot_pigweed":          ANNUAL_RULE,
    "pigweed":                  ANNUAL_RULE,
    "palmer_amaranth":          ANNUAL_RULE,
    "bitterweed":               ANNUAL_RULE,
    "bitter_sneezeweed":        ANNUAL_RULE,
    "common_ragweed":           ANNUAL_RULE,
    "ragweed":                  ANNUAL_RULE,
    "giant_ragweed":            ANNUAL_RULE,
    "lambsquarters":            ANNUAL_RULE,
    "henbit":                   ANNUAL_RULE,
    "horseweed":                ANNUAL_RULE,
    "marestail":                ANNUAL_RULE,
    "jimsonweed":               ANNUAL_RULE,
    "wild_mustard":             ANNUAL_RULE,
    "shepherdspurse":           ANNUAL_RULE,
    "smartweed":                ANNUAL_RULE,
    "perilla_mint":             ANNUAL_RULE,
    "wooly_croton":             ANNUAL_RULE,
    "showy_crotolaria":         ANNUAL_RULE,
    "prickly_sida":             ANNUAL_RULE,
    "field_dodder":             ANNUAL_RULE,
    "wild_lettuce":             ANNUAL_RULE,
    "ground_ivy":               ANNUAL_RULE,
    "mouseear_chickweed":       ANNUAL_RULE,
    "wild_carrot":              ANNUAL_RULE,
    "hophornbeam_copperleaf":   ANNUAL_RULE,
    "field_buttercup":          ANNUAL_RULE,
    "catchweed_bedstraw":       ANNUAL_RULE,

    # ---- HERBACEOUS PERENNIALS (broadleaves and biennials) ----
    "horsenettle":              PERENNIAL_RULE,
    "buttercup":                PERENNIAL_RULE,
    "thistle":                  PERENNIAL_RULE,
    "musk_thistle":             PERENNIAL_RULE,
    "bull_thistle":             PERENNIAL_RULE,
    "yellow_thistle":           PERENNIAL_RULE,
    "milk_thistle":             PERENNIAL_RULE,
    "canada_thistle":           PERENNIAL_RULE,
    "curly_dock":               PERENNIAL_RULE,
    "dogfennel":                PERENNIAL_RULE,
    "goldenrod":                PERENNIAL_RULE,
    "ironweed":                 PERENNIAL_RULE,
    "milkweed":                 PERENNIAL_RULE,
    "plantain":                 PERENNIAL_RULE,
    "buckhorn_plantain":        PERENNIAL_RULE,
    "pokeberry":                PERENNIAL_RULE,
    "red_sorrel":               PERENNIAL_RULE,
    "stinging_nettle":          PERENNIAL_RULE,
    "tropical_soda_apple":      PERENNIAL_RULE,
    "blue_vervain":             PERENNIAL_RULE,
    "wild_garlic":              PERENNIAL_RULE,
    "ground_cherry":            PERENNIAL_RULE,
    "lespedeza":                PERENNIAL_RULE,

    # ---- HERBACEOUS PERENNIAL grasses / sedges ----
    "johnsongrass":             PERENNIAL_RULE,
    "rhizome_johnsongrass":     PERENNIAL_RULE,
    "bahiagrass":               PERENNIAL_RULE,
    "pensacola_bahiagrass":     PERENNIAL_RULE,
    "centipede":                PERENNIAL_RULE,
    "dallisgrass":              PERENNIAL_RULE,
    "knotroot_foxtail":         PERENNIAL_RULE,
    "smutgrass":                PERENNIAL_RULE,
    "vaseygrass":               PERENNIAL_RULE,
    "nutsedge":                 PERENNIAL_RULE,
    "yellow_nutsedge":          PERENNIAL_RULE,
    "purple_nutsedge":          PERENNIAL_RULE,

    # ---- WOODY plants and vines ----
    "blackberry":               WOODY_RULE,
    "dewberry":                 WOODY_RULE,
    "multiflora_rose":          WOODY_RULE,
    "cherokee_rose":            WOODY_RULE,
    "macartney_rose":           WOODY_RULE,
    "poison_ivy":               WOODY_RULE,
    "pricklypear":              WOODY_RULE,
    "honey_locust":             WOODY_RULE,
    "locust":                   WOODY_RULE,
    "wisteria":                 WOODY_RULE,
    "maypop":                   WOODY_RULE,

    # ---- Default fallback ----
    # If a weed is not mapped above, the engine assumes the conservative
    # annual rule (14d/14d). For unknown woody/perennial species this may
    # under-restrict, so the producer should add the species to MOWING_RULES.
    "_default":                 ANNUAL_RULE,
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
DEFAULT_DATA_DIR = Path(__file__).parent / "data"


def load_database(data_dir: Path = DEFAULT_DATA_DIR) -> Dict[str, pd.DataFrame]:
    """Load the three CSVs into a dict of DataFrames. Comment lines (#) are ignored."""
    herbs = pd.read_csv(data_dir / "herbicides.csv",  comment="#", dtype=str).fillna("")
    eff   = pd.read_csv(data_dir / "efficacy.csv",    comment="#", dtype=str).fillna("")
    rest  = pd.read_csv(data_dir / "restrictions.csv", comment="#", dtype=str).fillna("")

    # Type coercion for boolean fields
    bool_cols = ["RUP_flag", "off_farm_hay_restricted", "off_farm_manure_restricted",
                 "volatilization_risk"]
    for col in bool_cols:
        if col in herbs.columns:
            herbs[col] = herbs[col].apply(_to_bool)

    return {"herbicides": herbs, "efficacy": eff, "restrictions": rest}


def _to_bool(value: Any) -> bool:
    """Permissive truthy parser for CSV fields."""
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in {"true", "t", "yes", "y", "1"}


def _parse_days(value: str) -> Tuple[str, Optional[int]]:
    """
    Parse a days field that may be int, 'next_season', 'unknown', or 'none'.
    Returns (kind, value) where kind is one of: int, next_season, unknown, none.
    """
    if value is None:
        return ("unknown", None)
    s = str(value).strip().lower()
    if s in {"unknown", ""}:
        return ("unknown", None)
    if s == "next_season":
        return ("next_season", None)
    if s == "none":
        return ("none", None)
    try:
        return ("int", int(s))
    except (ValueError, TypeError):
        return ("unknown", None)


# ---------------------------------------------------------------------------
# Individual gate functions — each returns a Verdict
# ---------------------------------------------------------------------------
def gate_legume(product, ui) -> Verdict:
    """Gate 2: legume protection."""
    if not ui.legumes_present:
        return Verdict.approve()

    sensitivity = (product.get("legume_sensitivity") or "").strip().upper()
    if sensitivity == "KILLS":
        return Verdict.reject("Kills legumes — legumes present in stand", gate="legume")
    if sensitivity == "INJURES_RECOVERS":
        if "red_clover" in (ui.legumes or []):
            return Verdict.reject("Kills red clover", gate="legume")
        # Other clovers recover — approve with warning handled at result level
        return Verdict.approve()
    if sensitivity == "UNKNOWN":
        return Verdict.review("Legume safety unknown in IPM-0028A", gate="legume")
    return Verdict.approve()  # SAFE


def gate_dairy(product, ui) -> Verdict:
    """Gate 3: lactating dairy waiting period vs operator's hold capacity."""
    if ui.livestock != "LACTATING_DAIRY":
        return Verdict.approve()

    kind, val = _parse_days(product.get("lactating_dairy_days"))
    if kind == "unknown":
        return Verdict.review("Lactating dairy waiting period missing", gate="dairy")
    if kind == "next_season":
        return Verdict.reject("Lactating dairy: cannot graze until next season", gate="dairy")
    if kind == "int" and val > (ui.hold_days or 0):
        return Verdict.reject(
            f"Dairy wait {val}d > operator hold {ui.hold_days}d", gate="dairy"
        )
    return Verdict.approve()


def gate_slaughter(product, ui) -> Verdict:
    """Gate 4: pre-slaughter withdrawal period."""
    if not ui.slaughter_30d:
        return Verdict.approve()

    kind, val = _parse_days(product.get("slaughter_withdrawal_days"))
    if kind == "unknown":
        return Verdict.review("Slaughter withdrawal data missing", gate="slaughter")
    if kind == "none":
        return Verdict.approve()
    if kind == "int" and val > 30:
        return Verdict.reject(f"Slaughter withdrawal {val}d > 30d horizon", gate="slaughter")
    return Verdict.approve()


def gate_hay(product, ui) -> Verdict:
    """Gate 5: hay PHI vs days until next cut."""
    if ui.next_cut_days is None:
        return Verdict.approve()

    kind, val = _parse_days(product.get("hay_phi_days"))
    if kind == "unknown":
        return Verdict.review("Hay PHI missing", gate="hay")
    if kind == "next_season":
        return Verdict.reject("Hay PHI = next season", gate="hay")
    if kind == "int" and val > ui.next_cut_days:
        return Verdict.reject(
            f"Hay PHI {val}d > {ui.next_cut_days}d until next cut", gate="hay"
        )
    return Verdict.approve()


def gate_off_farm_hay(product, ui) -> Verdict:
    """Gate 6: off-farm hay restriction."""
    if ui.hay_off_farm and product.get("off_farm_hay_restricted") is True:
        return Verdict.reject("Hay export restricted by label", gate="off_farm_hay")
    return Verdict.approve()


def gate_off_farm_manure(product, ui) -> Verdict:
    """Gate 7: off-farm manure restriction."""
    if ui.manure_off and product.get("off_farm_manure_restricted") is True:
        return Verdict.reject("Manure export restricted by label", gate="off_farm_manure")
    return Verdict.approve()


def gate_volatilization(product, ui) -> Verdict:
    """Gate 8: volatilization near broadleaf-sensitive crops."""
    if ui.sensitive_crops_nearby and product.get("volatilization_risk") is True:
        return Verdict.reject("Volatile near sensitive crops", gate="volatilization")
    return Verdict.approve()


def gate_rup(product, ui) -> Verdict:
    """RUP gate."""
    if product.get("RUP_flag") is True and ui.rup_status == "no_unrestricted_only":
        return Verdict.reject("Restricted Use Pesticide; unrestricted-only requested", gate="rup")
    return Verdict.approve()


def gate_mowing(product, ui) -> Verdict:
    """
    Gate 9: mowing timing window.
    Checks both the species-level rule from MOWING_RULES (agronomic floor
    from IPM-0028A p.1) and the product-level rule from herbicides.csv
    (label-specific overlay). Stricter constraint wins.
    """
    if ui.days_since_mow is None and ui.next_cut_days is None:
        return Verdict.approve()

    # ---- Species-level rule (priority weed dominates) ----
    if ui.weeds:
        rule = MOWING_RULES.get(ui.weeds[0], MOWING_RULES["_default"])
        before = rule["before_days"]
        after = rule["after_days"]
        cat = rule.get("category", "unknown")

        # "next_season" — woody/vine species rejected if any recent mow
        if before == "next_season":
            if ui.days_since_mow is not None:
                return Verdict.reject(
                    f"Woody/vine ({ui.weeds[0]}): mowed {ui.days_since_mow}d ago — "
                    f"guide requires waiting until next growing season after mow",
                    gate="mowing",
                )
        elif isinstance(before, int):
            if ui.days_since_mow is not None and ui.days_since_mow < before:
                return Verdict.reject(
                    f"Mowed {ui.days_since_mow}d ago; {cat} guidance requires {before}d before spray",
                    gate="mowing",
                )

        if isinstance(after, int) and ui.next_cut_days is not None and ui.next_cut_days < after:
            return Verdict.reject(
                f"Cut in {ui.next_cut_days}d; {cat} guidance requires {after}d after spray",
                gate="mowing",
            )

    # ---- Product-level rule (label-specific addition) ----
    pb_kind, pb_val = _parse_days(product.get("product_mow_wait_before_days"))
    pa_kind, pa_val = _parse_days(product.get("product_mow_wait_after_days"))

    if pb_kind == "int" and ui.days_since_mow is not None and ui.days_since_mow < pb_val:
        return Verdict.reject(
            f"Mowed {ui.days_since_mow}d ago; product label requires {pb_val}d before",
            gate="mowing",
        )
    if pa_kind == "int" and ui.next_cut_days is not None and ui.next_cut_days < pa_val:
        return Verdict.reject(
            f"Cut in {ui.next_cut_days}d; product label requires {pa_val}d after",
            gate="mowing",
        )

    return Verdict.approve()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
GATES = [
    ("legume",          gate_legume),
    ("dairy",           gate_dairy),
    ("slaughter",       gate_slaughter),
    ("hay",             gate_hay),
    ("off_farm_hay",    gate_off_farm_hay),
    ("off_farm_manure", gate_off_farm_manure),
    ("volatilization",  gate_volatilization),
    ("rup",             gate_rup),
    ("mowing",          gate_mowing),
]


def filter_by_forage(herbicides_df: pd.DataFrame, forage: str) -> List[Dict[str, Any]]:
    """Gate 1: forage scenario. Returns list of product dicts labeled for this forage."""
    matched = herbicides_df[herbicides_df["forage_type"].str.strip() == forage]
    return matched.to_dict(orient="records")


def apply_hard_filters(candidates: List[Dict[str, Any]], ui) -> Tuple[
    List[Dict[str, Any]],
    List[Tuple[Dict[str, Any], str, str]],
    List[Tuple[Dict[str, Any], str, str]],
]:
    """
    Run every product through every gate. First non-APPROVE verdict wins.
    Returns (approved, rejected, review).
    """
    approved: List[Dict[str, Any]] = []
    rejected: List[Tuple[Dict[str, Any], str, str]] = []
    review:   List[Tuple[Dict[str, Any], str, str]] = []

    for product in candidates:
        verdict = Verdict.approve()
        for gate_name, gate_fn in GATES:
            v = gate_fn(product, ui)
            if v.kind != VerdictKind.APPROVE:
                verdict = v
                break

        if verdict.kind == VerdictKind.REJECT:
            rejected.append((product, verdict.reason, verdict.gate))
        elif verdict.kind == VerdictKind.MANUAL_REVIEW:
            review.append((product, verdict.reason, verdict.gate))
        else:
            approved.append(product)

    return approved, rejected, review


def flag_unknowns(approved: List[Dict[str, Any]]) -> Tuple[
    List[Dict[str, Any]],
    List[Tuple[Dict[str, Any], str, str]],
]:
    """
    Catch products that survived gates but have unmapped efficacy or restriction data.
    These are routed to MANUAL_REVIEW out of caution.
    """
    safe: List[Dict[str, Any]] = []
    review: List[Tuple[Dict[str, Any], str, str]] = []
    for p in approved:
        missing = []
        for must_have in ("legume_sensitivity", "lactating_dairy_days", "hay_phi_days"):
            if not p.get(must_have):
                missing.append(must_have)
        if missing:
            review.append((p, f"Missing required fields: {', '.join(missing)}", "data_quality"))
        else:
            safe.append(p)
    return safe, review


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
