# Extension Edge v2.0 — Changes since initial bundle

This update reflects work to align the project with the canonical source
**IPM-0028A (2026), "Pasture & Forage Crops Weed Control Recommendations"**
revised by Dr. David Russell, Auburn University. The PDF was uploaded into
the working session and used as the authoritative reference for every
behavioral and data change below.

---

## 1. MOWING_RULES — rebuilt from the guide's three-category system

**What was wrong before.** The skeleton MOWING_RULES dict in `engine.py` had
guessed per-species values for a handful of weeds (`horsenettle`,
`blackberry`, `dewberry`, `pigweed`, `thistle`, `buttercup`, `johnsongrass`).
The numbers weren't traceable to any explicit rule in the guide and there
was no handling for woody species' "next growing season" requirement.

**What the guide actually says** (page 1, "Integrating Mowing and
Herbicides"):

| Plant category | Before spray (after mow) | After spray (before mow) |
|---|---|---|
| Annual weeds | 14 days | 14 days |
| Herbaceous perennials | ~30 days (until flowering or 12–24" regrowth) | ~30 days |
| Woody plants / vines | **next growing season** (need 1 year's growth) | 60 days (2 months) |

**What changed.** `engine.py` now defines three canonical rule constants
(`ANNUAL_RULE`, `PERENNIAL_RULE`, `WOODY_RULE`) sourced verbatim from the
guide, with a 75-entry weed→category mapping covering every weed in
Tables 2 and 3. The `gate_mowing()` function handles the special
`"next_season"` value for woody species — any finite `days_since_mow`
value triggers a rejection with the message *"guide requires waiting until
next growing season after mow."*

The schema changed from `{"before": int, "after": int, "weed_type": str}`
to `{"before_days": int|str, "after_days": int, "category": str, "source": str}`.
The `source` field carries the verbatim quote from page 1 of the guide for
audit-trail purposes.

**Tests added** (3 new):
- `test_6a_mowing_woody_blackberry_rejected_after_recent_mow` — locks in
  the WOODY_RULE rejection for any finite `days_since_mow`
- `test_6b_mowing_perennial_horsenettle_30day_window` — verifies 30-day
  window for herbaceous perennials, both reject and approve paths
- `test_6c_mowing_annual_pigweed_14day_window` — verifies 14-day window
  for annuals, both reject and approve paths

`app.py` updated to use the new schema in its mowing advisory display.
**12 of 12 tests pass.**

---

## 2. data/herbicides.csv — populated from Table 1

All 54 herbicide entries from Table 1 are now in the data file, with
fields cross-referenced against Table 4 (grazing/hay/slaughter waiting
periods). Each row carries a `guide_page_ref` field identifying its
source (e.g., "Table 1 p.5") for audit purposes.

**Key labeled values verified against the guide:**

- **4 products with `lactating_dairy_days = next_season`** — Crossbow,
  Pasturegard HL, Remedy Ultra, Surmount. Each entry carries the verbatim
  guide language: "Do not allow lactating dairy animals to graze treated
  areas until the next growing season."
- **10 RUP products** — both paraquat formulations (Gramoxone SL across
  4 forage scenarios), both atrazine products, Graslan L, Grazon P+D,
  Surmount, Kerb 50-W. Each has `RUP_flag=true`.
- **6 products labeled SAFE on legumes** — Eptam 7E, Pursuit, Select Max,
  Poast Plus, and the two paraquat applications on legume forages.
- **1 INJURES_RECOVERS product** — NovaGraz, exactly as the guide
  describes: "White clover and lespedeza will exhibit some injury
  (lodging and loss of vigor but will recover); will kill red clover."
- **26 KILLS-legume products** — every product where the guide explicitly
  states it kills or severely injures legumes.

**Distribution by forage type:**
- perennial_grass: 32 products
- bermuda_est: 6
- legume: 6
- sorghum: 3
- fescue_conv: 3
- dormant_bermuda: 2
- pasture_renovation: 1
- winter_grain: 1

Where the guide does not explicitly state a value (e.g., legume
sensitivity for products not labeled near legume forages), the field is
set to `unknown` per the spec — this routes the product to MANUAL_REVIEW
when that gate is exercised, rather than assuming safety.

---

## 3. data/efficacy.csv — populated from Tables 2 and 3

478 efficacy ratings populated from Tables 2 (legume forages and forage
sorghums) and 3 (broadleaf weeds in established forage stands), plus
selected grass ratings from the Table-2 continuation pages.

Coverage:
- **Broadleaves** (Table 3): 18 herbicide columns × ~35 broadleaf weeds
- **Grasses** (Tables 2, 16, 17): key grass weeds for perennial-grass,
  legume, and sorghum scenarios

Encoding notes:
- Hyphenated ratings like `G–E` and `F–G` are encoded conservatively at
  the lower value (`G-E → G`, `F-G → F`) to avoid over-claiming coverage
- "—" (no data in the guide) results in row omission, treated as 0 by
  the scorer

---

## 4. End-to-end real-data smoke test

A realistic Alabama scenario — beef cattle producer, established perennial
grass pasture, horsenettle as priority weed, no legumes interseeded,
mowed 35 days ago, next cut planned 45 days out — produces:

```
STATUS: RECOMMEND_WITH_WARNINGS
BEST:   IPM-009 — Chaparral (horsenettle rated E in Table 3)
BACKUP: IPM-032 — Surmount  (horsenettle rated E in Table 3)
```

Both selections are top-rated for horsenettle in the guide. PDF spray
record generates cleanly (3 pages, full audit trail).

---

## 5. Files in this bundle

| Path | Status | Notes |
|---|---|---|
| `engine.py` | **modified** | New MOWING_RULES system; gate_mowing handles next_season |
| `app.py` | **modified** | Mowing advisory uses new schema |
| `tests/test_engine.py` | **modified** | +3 tests for the three plant categories |
| `data/herbicides.csv` | **populated** | All 54 entries from Table 1 |
| `data/efficacy.csv` | **populated** | 478 ratings from Tables 2 and 3 |
| `data/restrictions.csv` | unchanged stub | Most restrictions fit in herbicides.csv columns |
| `validator.py`, `scorer.py`, `explainer.py`, `pdf_report.py` | unchanged | |
| `README.md`, `requirements.txt`, `.streamlit/config.toml` | unchanged | |
| `docs/DR_RUSSELL_REVIEW_BRIEF.md` | added | Review brief for Dr. David Russell |
| `docs/WEB_DEVELOPER_HANDOFF.md` | added | Web developer handoff |
| `docs/MAINTENANCE_GUIDE.md` | added | Maintenance guide |

---

## 6. What's still TODO before sharing with Dr. Russell

- **Spot-verify a sample of `unknown` fields** against full product labels
  (the guide is the SE summary; manufacturer labels are the legal authority).
  Most likely candidates for refinement: `legume_sensitivity` on
  perennial-grass products that don't mention legumes in their guide entry,
  and `slaughter_withdrawal_days` for several Table-1 entries where Table 4
  shows N/A.
- **Add field-tested species to MOWING_RULES** if any local AL species
  aren't in the current 75-entry mapping. The `_default` fallback is
  conservative (annual rule, 14d/14d), so unknown species fail safely
  short rather than long.
- **Check `restrictions.csv`** for any supplementary restrictions you want
  to encode (e.g., specific tank-mix restrictions, soil-type limits).
  Most guide restrictions are already encoded as columns in
  `herbicides.csv`.

---

**Engine version:** 2.0
**Guide version:** IPM-0028A (2026)
**Tests passing:** 12 / 12
**Real-data smoke test:** ✓ (RECOMMEND_WITH_WARNINGS, valid PDF)
