"""
test_engine.py — Pytest suite covering the 5 critical scenarios from
the deterministic rebuild specification, plus a happy-path test.

Tests use in-memory fixture data (not data/*.csv) so they remain stable
regardless of what the user has populated in the production CSVs.
"""

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest

# Make the project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator import UserInput
from engine import (
    filter_by_forage, apply_hard_filters, flag_unknowns,
    Status, VerdictKind, _to_bool,
)
from scorer import rank_by_efficacy, select_best


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------
def _row(**overrides):
    """Default row template — overrides take precedence."""
    base = {
        "unique_id": "IPM-T01",
        "trade_name": "TestProduct",
        "active_ingredient": "test",
        "forage_type": "bermuda_est",
        "application_type": "POST",
        "rate_per_acre": "2 pt/A",
        "timing_constraints": "POST",
        "RUP_flag": False,
        "lactating_dairy_days": "0",
        "beef_grazing_days": "0",
        "hay_phi_days": "7",
        "slaughter_withdrawal_days": "0",
        "legume_sensitivity": "SAFE",
        "off_farm_hay_restricted": False,
        "off_farm_manure_restricted": False,
        "volatilization_risk": False,
        "product_mow_wait_before_days": "none",
        "product_mow_wait_after_days": "none",
        "comments_structured": "",
        "guide_page_ref": "test",
    }
    base.update(overrides)
    return base


def _herbs(*rows):
    """Build a herbicides DataFrame from row dicts."""
    df = pd.DataFrame(rows)
    # Replicate the bool coercion from load_database
    for col in ("RUP_flag", "off_farm_hay_restricted",
                "off_farm_manure_restricted", "volatilization_risk"):
        if col in df.columns:
            df[col] = df[col].apply(_to_bool)
    # Force string dtype for everything else (matches CSV load)
    for col in df.columns:
        if col not in ("RUP_flag", "off_farm_hay_restricted",
                       "off_farm_manure_restricted", "volatilization_risk"):
            df[col] = df[col].astype(str)
    return df


def _eff(*triples):
    """Build an efficacy DataFrame from (unique_id, weed_id, rating) triples."""
    return pd.DataFrame(
        [{"unique_id": u, "weed_id": w, "rating": r, "scenario": ""} for u, w, r in triples]
    )


def _ui(**kwargs):
    """Build a UserInput with sensible defaults for tests."""
    defaults = dict(
        field_id="AL-TEST0001",
        forage="bermuda_est",
        weeds=["horsenettle"],
        livestock="NONE",
    )
    defaults.update(kwargs)
    return UserInput(**defaults)


# ---------------------------------------------------------------------------
# Test 1 — Lactating dairy violation
# ---------------------------------------------------------------------------
def test_1_lactating_dairy_violation_rejects():
    """Crossbow-like product with 14-day dairy wait, hold = 3 days → REJECTED."""
    herbs = _herbs(_row(
        unique_id="IPM-T01", trade_name="Crossbow-like",
        lactating_dairy_days="14", legume_sensitivity="SAFE",
    ))
    ui = _ui(livestock="LACTATING_DAIRY", hold_days=3)
    candidates = filter_by_forage(herbs, ui.forage)
    approved, rejected, review = apply_hard_filters(candidates, ui)

    assert approved == []
    assert len(rejected) == 1
    product, reason, gate = rejected[0]
    assert gate == "dairy"
    assert "14" in reason and "3" in reason


# ---------------------------------------------------------------------------
# Test 2 — Legume injury (KILLS)
# ---------------------------------------------------------------------------
def test_2_legume_kills_rejects():
    """Surmount-like product + white_clover present → REJECTED on legume gate."""
    herbs = _herbs(_row(
        unique_id="IPM-T02", trade_name="Surmount-like",
        legume_sensitivity="KILLS",
    ))
    ui = _ui(legumes_present=True, legumes=["white_clover"])
    candidates = filter_by_forage(herbs, ui.forage)
    approved, rejected, review = apply_hard_filters(candidates, ui)

    assert approved == []
    assert len(rejected) == 1
    _, reason, gate = rejected[0]
    assert gate == "legume"
    assert "legume" in reason.lower()


def test_2b_legume_injures_recovers_red_clover_rejects():
    """INJURES_RECOVERS + red_clover specifically → REJECTED."""
    herbs = _herbs(_row(
        unique_id="IPM-T02b", trade_name="ClopyralidLike",
        legume_sensitivity="INJURES_RECOVERS",
    ))
    ui = _ui(legumes_present=True, legumes=["red_clover"])
    _, rejected, _ = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    assert len(rejected) == 1
    assert rejected[0][2] == "legume"


def test_2c_legume_injures_recovers_white_clover_approves():
    """INJURES_RECOVERS + only white clover → APPROVED (recovers)."""
    herbs = _herbs(_row(
        unique_id="IPM-T02c", trade_name="ClopyralidLike",
        legume_sensitivity="INJURES_RECOVERS",
    ))
    ui = _ui(legumes_present=True, legumes=["white_clover"])
    approved, rejected, _ = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    assert len(approved) == 1
    assert rejected == []


# ---------------------------------------------------------------------------
# Test 3 — Missing restriction data routes to MANUAL_REVIEW
# ---------------------------------------------------------------------------
def test_3_unknown_dairy_data_routes_manual_review():
    """lactating_dairy_days=unknown + dairy on field → MANUAL_REVIEW."""
    herbs = _herbs(_row(
        unique_id="IPM-T03", trade_name="MysteryProduct",
        lactating_dairy_days="unknown",
    ))
    ui = _ui(livestock="LACTATING_DAIRY", hold_days=14)
    approved, rejected, review = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)

    assert approved == []
    assert rejected == []
    assert len(review) == 1
    _, reason, gate = review[0]
    assert gate == "dairy"
    assert "missing" in reason.lower()


def test_3b_unknown_legume_with_legumes_present_routes_review():
    """legume_sensitivity=UNKNOWN + legumes present → MANUAL_REVIEW."""
    herbs = _herbs(_row(
        unique_id="IPM-T03b", trade_name="UnknownLegumeSafety",
        legume_sensitivity="UNKNOWN",
    ))
    ui = _ui(legumes_present=True, legumes=["white_clover"])
    _, rejected, review = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    assert rejected == []
    assert len(review) == 1
    assert review[0][2] == "legume"


# ---------------------------------------------------------------------------
# Test 4 — Conflicting weeds → NO_SINGLE_PRODUCT
# ---------------------------------------------------------------------------
def test_4_no_single_product_for_conflicting_weeds():
    """Horsenettle + Dewberry, no product covers both at G/E → no best."""
    herbs = _herbs(
        _row(unique_id="IPM-T04a", trade_name="A_HorsenettleSpecialist"),
        _row(unique_id="IPM-T04b", trade_name="B_DewberrySpecialist"),
    )
    eff = _eff(
        ("IPM-T04a", "horsenettle", "E"),
        ("IPM-T04a", "dewberry",    "P"),
        ("IPM-T04b", "horsenettle", "P"),
        ("IPM-T04b", "dewberry",    "E"),
    )
    ui = _ui(weeds=["horsenettle", "dewberry"])
    approved, _, _ = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    safe, _ = flag_unknowns(approved)
    ranked = rank_by_efficacy(safe, ui.weeds, eff)
    best, backup, partial = select_best(ranked)

    assert best is None
    assert backup is None
    assert len(partial) == 2
    # Top of partial should be the horsenettle specialist (priority weed dominates)
    assert partial[0]["unique_id"] == "IPM-T04a"


# ---------------------------------------------------------------------------
# Test 5 — No legal recommendation: stacked failures
# ---------------------------------------------------------------------------
def test_5_no_legal_recommendation_when_all_filters_fail():
    """
    Forage = sorghum, lactating dairy with 0-day hold, white clover legume,
    sensitive crops nearby → all candidates rejected.
    """
    herbs = _herbs(
        _row(
            unique_id="IPM-T05a", trade_name="A_KillsLegumes",
            forage_type="sorghum", legume_sensitivity="KILLS",
            lactating_dairy_days="14",
        ),
        _row(
            unique_id="IPM-T05b", trade_name="B_VolatileSafe",
            forage_type="sorghum", legume_sensitivity="SAFE",
            lactating_dairy_days="0",
            volatilization_risk=True,
        ),
        _row(
            unique_id="IPM-T05c", trade_name="C_LongDairy",
            forage_type="sorghum", legume_sensitivity="SAFE",
            lactating_dairy_days="next_season",
        ),
    )
    ui = _ui(
        forage="sorghum",
        weeds=["pigweed"],
        livestock="LACTATING_DAIRY", hold_days=0,
        legumes_present=True, legumes=["white_clover"],
        sensitive_crops_nearby=True,
    )
    candidates = filter_by_forage(herbs, ui.forage)
    approved, rejected, review = apply_hard_filters(candidates, ui)

    assert approved == []
    assert len(rejected) == 3
    gates_hit = {gate for _, _, gate in rejected}
    # Each product should fail on a different (or shared) gate; at least
    # legume, volatilization, and dairy must each appear.
    assert "legume" in gates_hit
    assert "volatilization" in gates_hit
    assert "dairy" in gates_hit


# ---------------------------------------------------------------------------
# Test 6 — Mowing rules from IPM-0028A p.1 (3 plant categories)
# ---------------------------------------------------------------------------
def test_6a_mowing_woody_blackberry_rejected_after_recent_mow():
    """Blackberry (WOODY_RULE): any finite days_since_mow rejects — guide
    requires waiting until the next growing season."""
    herbs = _herbs(_row(unique_id="IPM-T06a", trade_name="WoodyControl"))
    ui = _ui(weeds=["blackberry"], days_since_mow=180)  # six months — still rejected
    _, rejected, _ = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    assert len(rejected) == 1
    _, reason, gate = rejected[0]
    assert gate == "mowing"
    assert "next growing season" in reason.lower()


def test_6b_mowing_perennial_horsenettle_30day_window():
    """Horsenettle (PERENNIAL_RULE): 30 days before / 30 days after."""
    herbs = _herbs(_row(unique_id="IPM-T06b", trade_name="PerennialControl"))
    # 20 days post-mow — fails the 30-day before-spray window
    ui = _ui(weeds=["horsenettle"], days_since_mow=20)
    _, rejected, _ = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    assert len(rejected) == 1 and rejected[0][2] == "mowing"
    assert "30d" in rejected[0][1]

    # 35 days post-mow — passes
    ui_ok = _ui(weeds=["horsenettle"], days_since_mow=35, next_cut_days=45)
    approved, rejected_ok, _ = apply_hard_filters(filter_by_forage(herbs, ui_ok.forage), ui_ok)
    assert len(approved) == 1 and rejected_ok == []


def test_6c_mowing_annual_pigweed_14day_window():
    """Pigweed (ANNUAL_RULE): 14 days before / 14 days after."""
    herbs = _herbs(_row(unique_id="IPM-T06c", trade_name="AnnualControl"))
    # Cutting in 10 days — fails the 14-day after-spray window
    ui = _ui(weeds=["pigweed"], days_since_mow=20, next_cut_days=10)
    _, rejected, _ = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    assert len(rejected) == 1 and rejected[0][2] == "mowing"
    assert "14d" in rejected[0][1]

    # Cutting in 21 days — passes
    ui_ok = _ui(weeds=["pigweed"], days_since_mow=20, next_cut_days=21)
    approved, _, _ = apply_hard_filters(filter_by_forage(herbs, ui_ok.forage), ui_ok)
    assert len(approved) == 1


# ---------------------------------------------------------------------------
# Bonus: happy-path test
# ---------------------------------------------------------------------------
def test_happy_path_recommend():
    """
    Clean inputs and a product that passes every gate with G or better
    on the priority weed → produces a best+backup pair.
    """
    herbs = _herbs(
        _row(unique_id="IPM-H01", trade_name="GoodChoice"),
        _row(unique_id="IPM-H02", trade_name="AlsoGood"),
    )
    eff = _eff(
        ("IPM-H01", "buttercup", "E"),
        ("IPM-H02", "buttercup", "G"),
    )
    ui = _ui(
        weeds=["buttercup"],
        days_since_mow=30, next_cut_days=60,
    )
    approved, rejected, _ = apply_hard_filters(filter_by_forage(herbs, ui.forage), ui)
    safe, _ = flag_unknowns(approved)
    ranked = rank_by_efficacy(safe, ui.weeds, eff)
    best, backup, _ = select_best(ranked)

    assert rejected == []
    assert best is not None and best["unique_id"] == "IPM-H01"
    assert backup is not None and backup["unique_id"] == "IPM-H02"
