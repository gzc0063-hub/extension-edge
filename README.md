# Extension Edge

A deterministic, label-compliant herbicide recommendation tool for Alabama pasture and forage producers, derived entirely from **ACES IPM-0028A — *Pasture & Forage Crops: Weed Control Recommendations for 2026***.

> **Screening aid only.** The product label is the law. Always confirm recommendations with your county Extension office before applying any herbicide.

---

## What it does

Presents one phone-friendly form for a producer's field situation (forage type, target weeds, livestock, mowing/cutting timing, off-farm hay/manure, slaughter plans, and RUP applicator status) and returns one of four states:

| Status | Meaning |
|---|---|
| `RECOMMEND` | A product passes every label gate and rates Good or Excellent on every selected weed. |
| `RECOMMEND_WITH_WARNINGS` | Top product passes all hard gates but carries cautionary information from the guide. |
| `NO_SINGLE_PRODUCT` | No single product covers all selected weeds at G/E. Top three partial options are shown. |
| `NO_LEGAL_RECOMMENDATION` | Every product was rejected by a hard gate. The reasoning is itemized. |

A producer-ready PDF spray record is generated alongside the on-screen recommendation.

---

## Architecture

```
extension-edge/
├── app.py                  # Streamlit single-page grower form
├── validator.py            # Input completeness/legality validation
├── engine.py               # Hard-filter pipeline (9 gates)
├── scorer.py               # Priority-weighted lexicographic ranking
├── explainer.py            # Deterministic template text generator
├── pdf_report.py           # ReportLab spray record
├── report_store.py         # Optional Supabase analytics/PDF backups
├── requirements.txt
├── README.md
├── docs/
│   ├── DR_RUSSELL_REVIEW_BRIEF.md
│   ├── WEB_DEVELOPER_HANDOFF.md
│   ├── MAINTENANCE_GUIDE.md
│   └── REPORT_STORAGE_SETUP.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   ├── herbicides.csv      # 54 products, IPM-001…IPM-054
│   ├── efficacy.csv        # 478 ratings: unique_id, weed_id, rating
│   └── restrictions.csv    # Reserved supplementary restrictions table
└── tests/
    └── test_engine.py      # pytest suite
```

**Pipeline:**

```
user input
  └─► validator.validate()         reject if incomplete
        └─► engine.apply_hard_filters()    9 gates, zero tolerance
              └─► engine.flag_unknowns()   missing data → MANUAL_REVIEW
                    └─► scorer.rank_by_efficacy()
                          └─► scorer.select_best()
                                └─► explainer.render()
                                      └─► pdf_report.build()
```

No AI calls. Recommendation decisions are deterministic: same inputs always produce the same output. Optional Supabase storage can be configured for report backups and usage summaries.

---

## Documentation

The project includes current handoff and operations documents:

| Document | Use it for |
|---|---|
| [`docs/DR_RUSSELL_REVIEW_BRIEF.md`](docs/DR_RUSSELL_REVIEW_BRIEF.md) | Review brief for Dr. David Russell, including purpose, source attribution, compliance posture, and review requests. |
| [`docs/WEB_DEVELOPER_HANDOFF.md`](docs/WEB_DEVELOPER_HANDOFF.md) | Web developer handoff for Streamlit UI, data flow, labels, PDF behavior, and deployment. |
| [`docs/MAINTENANCE_GUIDE.md`](docs/MAINTENANCE_GUIDE.md) | Maintenance workflow for annual IPM updates, source audits, data updates, testing, and deployment. |
| [`docs/REPORT_STORAGE_SETUP.md`](docs/REPORT_STORAGE_SETUP.md) | Optional Supabase setup for usage counts, county summaries, and private PDF report backups. |

PDF copies of each document are also stored in `docs/` for sharing with reviewers.

When optional Supabase secrets are configured, each submitted recommendation is backed up with county-level analytics metadata and a private PDF report copy. See [`docs/REPORT_STORAGE_SETUP.md`](docs/REPORT_STORAGE_SETUP.md).

---

## Local install and run

```bash
# Clone
git clone https://github.com/<your-username>/extension-edge.git
cd extension-edge

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate

# Install
pip install -r requirements.txt

# Launch
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Tests

```bash
pytest tests/ -v
```

The suite covers the five critical scenarios from the specification:

| # | Scenario | Expected |
|---|---|---|
| 1 | Lactating dairy violation (Crossbow, 14-day wait, hold = 3 d) | `REJECTED` — "Dairy wait 14 > 3" |
| 2 | Legume injury (Surmount + white clover present) | `REJECTED` — "Kills legumes" |
| 3 | Missing restriction data (`lactating_dairy_days = unknown` + dairy on field) | `MANUAL_REVIEW` |
| 4 | Conflicting weeds (horsenettle + dewberry, no legumes) | `NO_SINGLE_PRODUCT` |
| 5 | No valid herbicide (forage sorghum + lactating dairy + legumes + sensitive crops) | `NO_LEGAL_RECOMMENDATION` |

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (public).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. **New app** → select the `extension-edge` repo → branch `main` → main file `app.py`.
4. Click **Deploy**. No secrets are required for the recommendation engine.
5. Public URL: `https://<your-username>-extension-edge.streamlit.app`

Every push to `main` redeploys automatically within seconds.

To enable report analytics and PDF backups, add the optional Streamlit secrets described in [`docs/REPORT_STORAGE_SETUP.md`](docs/REPORT_STORAGE_SETUP.md).

---

## Data update procedure

When ACES publishes the next edition of IPM-0028A:

1. Open the new guide PDF.
2. Update `data/herbicides.csv` row by row, preserving each `unique_id`.
3. Update `data/efficacy.csv` for any rating changes.
4. Update `data/restrictions.csv` if a future feature starts using supplementary restrictions outside the herbicide registry.
5. Bump the guide-version constant in `engine.py`.
6. Run `pytest tests/ -v` and confirm all tests still pass.
7. Commit and push. The live app redeploys automatically.

**Never** edit decision logic to accommodate a new product. Edit the data, never the engine.

---

## Compliance posture

- **Zero tolerance for label violations.** All restrictions are hard filters, never warnings.
- **Missing data = manual review.** The engine never assumes safety when the guide is silent on a field.
- **No tank-mix invention.** Only pre-mixed combination products explicitly listed in IPM-0028A appear in the recommendation set.
- **No AI in the decision path.** All decisions are rule-based and deterministic.
- **Audit trace.** Every exclusion message cites the guide table or section. Every recommendation is stamped with engine version, guide version, timestamp, and Field ID.

---

## Limitations

- Alabama only. The tool encodes ACES recommendations and is not valid in other states.
- The product label is the law. The tool is a screening aid, not a substitute for the label.
- Pesticide registrations change. If a registration is canceled, the rate listed in IPM-0028A is no longer valid until the next revision.
- The tool cannot account for site-specific conditions like soil pH extremes, drought stress, or unusual cropping rotations.
- Trade names identify products only; ACES does not endorse any product.

---

## Source

- **Guide:** ACES IPM-0028A — *Pasture & Forage Crops: Weed Control Recommendations for 2026*
- **Guide revision:** Dr. David Russell, Assistant Extension Professor (Weed Science), Auburn University
- **Tool development:** Gourav Chahal, PhD student, under the supervision of Dr. David Russell and Dr. Andrew Price, USDA ARS
- **Engine version:** 2.0 (deterministic, AI-free)

---

## License

This project encodes recommendations from a publicly available Alabama Cooperative Extension System publication. Source code is released under the MIT License. The encoded recommendations are the work product of ACES and are used here for decision support only; consult the original publication for authoritative guidance.
