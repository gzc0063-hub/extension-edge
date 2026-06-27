"""
Hybrid LLM Data Extraction Pipeline for ACES IPM Guides
-------------------------------------------------------
This script defines the Pydantic schemas required to force an LLM
to extract agronomic data from the ACES PDFs with 100% adherence to
the required JSON structure.

To use this:
1. Parse the PDF using a tool like LlamaParse to get markdown tables.
2. Pass the markdown to an LLM (e.g., OpenAI gpt-4o) using these Pydantic models via Structured Outputs.
3. The LLM will return perfectly formatted JSON that can be dropped into `web/src/data/`.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class EfficacyRating(BaseModel):
    weed_name: str = Field(..., description="Common name of the weed (e.g., Palmer Amaranth)")
    rating: str = Field(..., description="Rating code: E (Excellent), G (Good), F (Fair), P (Poor), N (None)")

class RowCropHerbicide(BaseModel):
    unique_id: str = Field(..., description="Generate an ID like IPM-CORN-PRE-01")
    trade_name: str = Field(..., description="Trade name of the herbicide (e.g., Dual Magnum)")
    active_ingredient: str = Field(..., description="Active ingredient (e.g., S-metolachlor)")
    herbicide_group: str = Field(..., description="WSSA Site of Action group number(s)")
    application_type: str = Field(..., description="One of: BURNDOWN, PRE, POST")

    # Agronomic Constraints
    soil_texture_restriction: Optional[str] = Field(None, description="e.g., 'Do not apply to coarse soils'")
    plantback_restriction_months: Optional[int] = Field(None, description="Longest rotational crop restriction in months")
    seed_trait_required: Optional[str] = Field(None, description="e.g., 'xtend', 'enlist', 'roundup_ready', or 'conventional'")

    # Operational Constraints
    phi_days: Optional[int] = Field(None, description="Pre-harvest interval in days")
    rup_flag: bool = Field(..., description="True if Restricted Use Pesticide")
    rate_per_acre: str = Field(..., description="Broadcast rate per acre (e.g., '1-2 pt')")

    # Efficacy
    efficacy: List[EfficacyRating] = Field(..., description="List of weeds and their control ratings")

    comments_and_warnings: str = Field(..., description="Any critical footnotes or warnings from the table")

class ExtractedGuide(BaseModel):
    crop: str
    herbicides: List[RowCropHerbicide]

# Example usage (Pseudocode):
# from openai import OpenAI
# client = OpenAI(api_key="YOUR_KEY")
# response = client.beta.chat.completions.parse(
#     model="gpt-4o",
#     messages=[
#         {"role": "system", "content": "You are a precision agronomist extracting chemical tables."},
#         {"role": "user", "content": pdf_markdown_text}
#     ],
#     response_format=ExtractedGuide
# )
# with open('web/src/data/extracted_weeds.json', 'w') as f:
#     f.write(response.choices[0].message.content)
