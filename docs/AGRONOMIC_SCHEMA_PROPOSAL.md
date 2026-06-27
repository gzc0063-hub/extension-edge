# Agronomic Schema Proposal: All-Crop IPM Tool

Following an analysis of the 2025/2026 ACES IPM guides for row crops (Corn, Cotton, Soybeans) and insects, it is clear that forcing all guides into the `Pasture Weed` data structure is agronomically incorrect.

Each guide requires its own unique JSON schema and filtering logic to accurately represent the zero-tolerance constraints defined by ACES.

## 1. Pasture & Forage Weed Schema (Currently Implemented)
- **Primary Constraints:** Forage Type, Lactating Dairy Wait, Beef Slaughter Wait, Legume Sensitivity.
- **Pest Metric:** Presence/Absence of specific weed species.
- **Timing:** PRE vs POST emergence.

## 2. Row Crop Insect Schema (e.g., Cotton Insect Control)
- **Primary Constraints:** Pre-Harvest Interval (PHI) in days, Resistance Management (Insecticide Mode of Action groups).
- **Pest Metric:** **Economic Threshold**. Instead of asking "Is this pest present?", the tool must ask "Has the scouting threshold been met?" (e.g., *10 small larvae per 100 plants*).
- **Timing:** Plant Growth Stage (Seedling, Whorl, Tasseling, Boll Formation).
- **Situational Modifiers:** Presence of beneficial arthropods.

### Proposed JSON Structure (`cotton_insects.json`)
```json
{
  "pest_group": "Bollworms/Tobacco Budworms",
  "growth_stage_relevance": ["blooming", "boll_development"],
  "economic_threshold": "10 small larvae (0.25 inch) per 100 plants",
  "products": [
    {
      "unique_id": "IPM-COTTON-INS-01",
      "trade_name": "VANTACOR",
      "active_ingredient": "chlorantraniliprole",
      "rate_per_acre": "1.2-2.5 oz",
      "phi_days": 21,
      "rup_flag": false,
      "beneficials_safe": true,
      "comments": "Use higher rates for larger larvae."
    }
  ]
}
```

## 3. Row Crop Weed Schema (e.g., Corn, Soybeans)
- **Primary Constraints:** Rotational Crop Interval (Plantback restriction in months for next season's crop), Herbicide Site of Action (SOA) for resistance management.
- **Timing:** Pre-Plant Incorporated (PPI), PRE, POST (often defined by crop height, e.g., "up to 12 inches").

## Next Implementation Steps for the Web App
1. **Dynamic UI:** The React `App.tsx` must be refactored. When a user selects "Cotton" -> "Insects", the UI must dynamically change the "Hard Constraints" section. It must remove "Lactating Dairy" and replace it with "Days until Harvest" and "Scouting Threshold Met?".
2. **Modular Engines:** We must split `engine.ts` into specific handler functions:
   - `evaluatePastureWeeds()`
   - `evaluateRowCropInsects()`
   - `evaluateRowCropWeeds()`

## 4. Row Crop Weed Schema Updates (Weed Scientist Perspective)
Following review of the Soybean Weed Control guide, additional constraints are mandatory for safe row crop weed management:
- **Seed Trait Technology (Critical):** Applying Dicamba (Engenia/XtendiMax) to non-Xtend soybeans will kill the crop. The UI must ask the grower what trait technology they planted (e.g., Conventional, Roundup Ready, Xtend, Enlist E3).
- **Herbicide Groups (Resistance Management):** The guide explicitly labels Herbicide Groups (e.g., 14, 15, 2, 4). The tool should ideally warn against stacking the same groups.
- **Maximum Seasonal Rates & Cutoff Dates:** (e.g., "Do not apply after June 30" or "Apply up to R1 stage").

### Updated JSON Structure (`soybean_weeds.json`)
```json
{
  "unique_id": "IPM-SOY-WEED-02",
  "trade_name": "Engenia",
  "active_ingredient": "BAPMA dicamba",
  "herbicide_group": "4",
  "seed_trait_required": "Xtend",
  "application_type": "POST",
  "cutoff_stage": "R1",
  "cutoff_date": "June 30",
  "phi_days": 7,
  "rate_per_acre": "12.8 fl.oz.",
  "comments": "RESTRICTED USE PRODUCT. Mandatory training required."
}
```

## 5. Row Crop Weed Schema Updates (Agronomist Additions)
Per direct guidance from the Agronomist, row crop weed control fundamentally requires evaluating soil conditions and long-term crop rotation plans. If these are ignored, it can result in severe crop injury or illegal chemical carryover.

### Additional Fields Required in Schema
- **`soil_texture_restriction`**: Text warning if the product cannot be used on Sand/Coarse or Clay/Fine soils, or requires specific Organic Matter percentages.
- **`plantback_restriction`**: Information detailing how many months the grower must wait before planting a specific *different* crop.
- **`application_type`**: Expanded to include `BURNDOWN` (Winter/Spring pre-plant applications).

### Engine Execution Rules
1. If the tool is screening PRE herbicides for row crops, it **must** ask the grower for their Soil Texture. If it is omitted, the engine **must** flag the recommendation with a "Check Label for Soil Restrictions" warning.
2. The tool **must** ask the grower what crop they intend to plant *next season*. The engine will display any `plantback_restriction` text so the grower is aware of carryover risks.
