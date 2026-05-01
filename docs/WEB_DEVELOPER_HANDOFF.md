# Extension Edge - Web Developer Handoff

## App Overview

Extension Edge is a Streamlit app for Alabama pasture and forage herbicide planning. The frontend is intentionally simple, responsive, and form-focused so it works well from a phone link in the field.

Main entry point:

- `app.py`

Supporting modules:

- `validator.py` validates user input.
- `engine.py` applies deterministic hard-filter gates.
- `scorer.py` ranks products by efficacy.
- `explainer.py` writes deterministic recommendation text.
- `pdf_report.py` builds the downloadable PDF record.
- `report_store.py` optionally stores usage analytics and private PDF report backups.
- `labels.py` stores farmer-facing labels for internal codes.

## User Interface Requirements

The current UI is a single-page form. Keep this structure unless a future stakeholder explicitly asks for a wizard again.

Important frontend behavior:

- Use Auburn colors: navy `#0C2340`, orange `#E87722`, and ACES green `#2F6B3F`.
- Keep the page mobile-first and scrollable.
- Do not show internal enum codes to growers.
- Use labels from `labels.py`.
- Weed choices should remain alphabetized and searchable.
- Keep the PDF download button near the primary recommendation.
- Keep source attribution visible near the top of the page.

## Data Flow

The UI collects values into `st.session_state.ui_data`. The app converts that dictionary into `UserInput`, then runs:

```python
validate(ui)
filter_by_forage(...)
apply_hard_filters(...)
flag_unknowns(...)
rank_by_efficacy(...)
select_best(...)
render(...)
build_pdf(...)
```

Do not put recommendation logic into Streamlit controls. The interface should only collect inputs, call the pipeline, and render outputs.

When report storage is configured, `report_store.save_report(...)` runs after the PDF bytes are created. It stores one row per submitted recommendation and uploads one PDF backup using the same field ID shown in the app report.

## Farmer-Facing Labels

Use `labels.py` for display:

- `forage_label(...)`
- `weed_label(...)`
- `livestock_label(...)`
- `legume_label(...)`
- `rup_label(...)`

This prevents strings like `perennial_grass`, `white_clover`, or `LACTATING_DAIRY` from appearing in the app or report.

## PDF Report

PDF output is generated in `pdf_report.py` using ReportLab. The PDF should:

- Use the Extension Edge name.
- Show friendly labels.
- Avoid duplicated words when composing recommendation timing text.
- Include the PDF download near the primary recommendation in the app UI.
- Preserve audit metadata: field ID, timestamp, engine version, guide version.

## Local Run

```bash
cd C:\Users\gzc0063\forage-advisor\weed-advisor
venv\Scripts\Activate.ps1
streamlit run app.py
```

Default local URL:

```text
http://localhost:8501
```

## Verification

Before handing off or deploying:

```bash
python -m py_compile app.py
pytest tests/ -v
```

The current test suite covers the engine. Manual browser testing is still needed for layout and mobile usability.

## Deployment

Recommended deployment path:

1. Push this folder to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Create a new app using the GitHub repo, branch `main`, and main file `app.py`.
4. Share the resulting Streamlit URL with Dr. Russell.

No API keys or secrets are required for recommendations. Optional Supabase secrets can be added in Streamlit Cloud to enable usage counts, county summaries, and PDF backups. See `docs/REPORT_STORAGE_SETUP.md`.
