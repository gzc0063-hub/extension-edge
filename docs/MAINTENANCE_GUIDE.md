# Extension Edge - Maintenance Guide

## Maintenance Mindset

Extension Edge is a deterministic Extension planning tool. Keep changes conservative, reviewable, and traceable to IPM-0028A or the product label.

Core rules:

- Test before deployment.
- Keep data changes in CSV files when possible.
- Keep decision logic in `engine.py`, not in `app.py`.
- Missing data should trigger manual review rather than a guessed recommendation.
- The product label remains the legal authority.

## Annual IPM Update Workflow

When a new IPM-0028A guide is released:

1. Save the new PDF source guide.
2. Compare Table 1 product rows against `data/herbicides.csv`.
3. Compare Tables 2 and 3 against `data/efficacy.csv`.
4. Compare Table 4 restriction values against the encoded grazing, hay, dairy, and slaughter fields.
5. Check the mowing narrative for changes.
6. Update `GUIDE_VERSION` in `engine.py`.
7. Run the audit helper if PDF extraction is available.
8. Run tests.
9. Smoke-test the app in a browser and on a phone-sized viewport.
10. Update `CHANGES.md`.

## Data Files

`data/herbicides.csv`

- One row per product/scenario entry from Table 1.
- Keep `unique_id` stable.
- Use the guide's trade-name and active-ingredient wording where possible.
- Use `unknown` only when the guide and label summary are silent.

`data/efficacy.csv`

- Long format: `unique_id`, `weed_id`, `rating`, `scenario`.
- Omit blank/no-data cells.
- Encode hyphenated ratings conservatively using the lower value.

`data/restrictions.csv`

- Reserved supplementary table.
- Currently not used for core recommendations.

## PDF Source Audit

The helper script is:

```text
tools/audit_source_pdf.py
```

It extracts source PDF text and checks whether product names, active ingredients, IDs, and efficacy links are internally consistent.

The script requires `pypdf`; encrypted PDFs may also require `cryptography`.

Example:

```bash
python tools/audit_source_pdf.py "C:\path\to\IPM-0028A.pdf"
```

## Reference PDF Generation

The three handoff documents can be regenerated as PDFs with:

```bash
python tools/render_reference_pdfs.py
```

Current deliverables:

- `docs/DR_RUSSELL_REVIEW_BRIEF.md/.pdf`
- `docs/WEB_DEVELOPER_HANDOFF.md/.pdf`
- `docs/MAINTENANCE_GUIDE.md/.pdf`

## Pre-Deploy Checklist

- `python -m py_compile app.py` passes.
- `pytest tests/ -v` passes.
- `from engine import load_database; load_database()` succeeds.
- The Streamlit app opens locally.
- The single-page form works on a narrow/mobile viewport.
- The PDF report downloads from the recommendation section.
- The generated report uses Extension Edge and farmer-facing labels.
- The Extension Edge name and Gourav Chahal spelling are used in all user-facing files.
- If Supabase report storage is enabled, a test recommendation creates one metadata row and one PDF backup.

## Common Fixes

Duplicate wording in narrative:

- Check `explainer.py`.
- Timing fields often already start with "Apply"; do not prepend another "Apply".

Internal code appears in app or report:

- Add or adjust the display label in `labels.py`.
- Use the label helper in `app.py`, `explainer.py`, or `pdf_report.py`.

CSV parsing fails:

- Check for commas inside unquoted CSV values.
- Wrap those values in double quotes.

No public link available:

- Push the project to GitHub.
- Deploy through Streamlit Community Cloud.
- Share the Streamlit Cloud URL, not the local `localhost` URL.

Analytics or report backups missing:

- Confirm Streamlit Cloud secrets include `[report_storage]`.
- Confirm `supabase_schema.sql` was run in the Supabase SQL editor.
- Confirm the `extension-edge-reports` bucket exists and is private.
- Submit a new recommendation; storage runs when the report is generated.
