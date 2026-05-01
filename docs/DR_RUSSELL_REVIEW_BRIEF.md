# Extension Edge - Review Brief for Dr. David Russell

## Purpose

Extension Edge is a deterministic planning aid for Alabama pasture and forage growers. It helps a grower pre-screen herbicide options using the 2026 ACES IPM-0028A forage weed-control guide, then reminds them to confirm the final application against the product label.

## Source and Attribution

The information in the tool is drawn from Alabama Cooperative Extension System IPM-0028A, Pasture & Forage Crops Weed Control Recommendations for 2026. The guide is revised by Dr. David Russell, Assistant Extension Professor (Weed Science), Department of Crop, Soil & Environmental Sciences, Auburn University.

Dr. Russell contact information shown in the app:

- Phone: 256-353-8702
- Email: dpr0013@auburn.edu
- Role: Assistant Extension Professor (Weed Science)

Tool development credit shown in the app:

- Developed by Gourav Chahal, PhD student
- Supervision: Dr. David Russell and Dr. Andrew Price, USDA ARS

## What the Tool Does

The grower enters a field situation on a single phone-friendly webpage:

- Forage or crop situation
- Up to three priority weeds, selected from an alphabetized searchable list
- Mowing and hay-cut timing
- Livestock class and dairy hold period, if applicable
- Legume presence
- Off-farm hay or manure movement
- Nearby sensitive broadleaf crops
- Slaughter timing
- Restricted Use Pesticide access

The tool then screens labeled products through deterministic hard filters and ranks surviving products by efficacy on the selected weeds.

## Compliance Posture

Extension Edge does not use AI, machine learning, external APIs, or probabilistic recommendations in the decision path. The same inputs and same source data always produce the same output.

The label-compliance stance is conservative:

- Label restrictions are hard filters.
- Missing relevant data routes to manual review.
- The tool does not invent tank mixes.
- The tool does not replace the pesticide label.
- Every PDF record includes field ID, timestamp, engine version, guide version, selected inputs, recommendation, rejection reasons, and manual-review items.

## Source Data Summary

Current data encoded from IPM-0028A:

- 54 herbicide registry rows from Table 1
- 478 efficacy ratings from Tables 2 and 3
- Table 4 grazing, hay, dairy, and slaughter restrictions encoded into the herbicide registry where applicable
- Mowing guidance encoded from the narrative section on integrating mowing and herbicides

## Recent Interface Changes

The old step-by-step wizard was replaced with one scrollable form for iPhone and Android users. Farmer-facing labels are used instead of internal codes. For example, the app shows Established bermudagrass instead of `bermuda_est`.

The app now uses the name Extension Edge.

## Review Requests

Recommended review focus:

- Confirm the grower-facing intro and disclaimer are appropriate.
- Confirm the source attribution and role/contact information are correct.
- Confirm that hard-filter behavior is appropriate for Extension decision support.
- Confirm that wording around planning aid, label-first use, and county Extension consultation is acceptable.
- Confirm any product-specific restrictions or Table 4 interpretations that should be adjusted.

## Deployment Note

The app is ready to deploy through Streamlit Community Cloud once the project is pushed to a GitHub repository. After deployment, Dr. Russell can open the public Streamlit link on a phone or computer.
