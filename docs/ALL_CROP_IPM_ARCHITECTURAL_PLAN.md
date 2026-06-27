# All-Crop Integrated Pest Management (IPM) Tool: Architectural Plan & Expert Review

## 1. Executive Summary
This document outlines the architectural plan for expanding the "Extension Edge" tool from a pasture/forage weed control screening aid into a comprehensive, generalized **All-Crop IPM Tool**. This new tool will cover all crops and all pest types (weeds, insects, diseases) based strictly on the latest Alabama Cooperative Extension System (ACES) IPM guides.

**Core Mandates:**
1. **Zero Tolerance for Misinterpretation:** The tool must remain a screening aid. Recommendations must be strictly derived from ACES IPM guides. The product label remains the law.
2. **Hybrid Intelligence (Restricted AI):** Core filtering and recommendations will remain deterministic. AI (LLM/RAG) will only be used to provide supplementary "recommendation notes" or summarize guide text, without altering the underlying recommendation logic or pesticide rates.
3. **Grower-Centric:** Designed primarily for growers, accessible on mobile and desktop.
4. **Hosting:** Architecture must support hosting on simple, cost-effective infrastructure like **GitHub Pages** (`username.github.io`).

---

## 2. Technical Architecture & Hosting Strategy

The current `Extension Edge` is built using Python and Streamlit. Streamlit requires a server (like Streamlit Community Cloud) and cannot be statically hosted on GitHub Pages. To meet the new hosting requirement while maintaining high performance and data security, we propose the following shift:

### Target Architecture: Client-Side Static Application
- **Frontend Framework:** React.js (via Next.js static export or Vite) or lightweight vanilla JavaScript/Web Components. This compiles down to pure HTML/CSS/JS, which can be natively hosted on GitHub Pages.
- **Data Management:**
  - Instead of standard CSVs processed by Python, the guide data (Crops, Pests, Products, Restrictions, Efficacy) will be compiled into lightweight JSON files or an in-browser database (like SQLite via WebAssembly/sql.js or IndexedDB).
  - The deterministic engine logic (currently Python) will be rewritten in TypeScript/JavaScript to run entirely in the user's browser.
- **AI/RAG Integration:**
  - AI features cannot run locally on the client without massive downloads.
  - We will implement a lightweight, stateless serverless backend (e.g., Cloudflare Workers, AWS Lambda, or Vercel Edge Functions) that holds the vector database of IPM guide text and communicates with an LLM API (like OpenAI).
  - The AI will **only** trigger to fetch specific paragraphs or generate a "Summary Note" citing exact page numbers. The core filtering happens *before* AI is involved.

### User Flow
1. **Selection Phase:** User selects Crop Group -> Specific Crop -> Target Pest(s) -> Application Timing (Pre-plant, Post-emergence, etc.).
2. **Context Phase:** User enters situational constraints (e.g., adjacent sensitive crops, grazing intervals, applicator license status).
3. **Deterministic Filtering (Client-side):** The browser instantly filters the JSON datasets based on hard rules. Products failing the constraints are rejected with citation.
4. **Recommendation Display:** Approved products are ranked.
5. **AI Augmentation (Optional/On-Demand):** The user clicks "Explain this treatment." The browser sends the product and pest to the serverless AI endpoint, which returns a structured note directly quoting the IPM guide.

---

## 3. Expert Panel Review

To ensure the highest quality, safety, and usability, this plan has been reviewed from five distinct professional perspectives.

### 3.1 Agronomist / Crop Specialist (40 Years Experience in Alabama)
**Review:**
"In my 40 years walking fields across Alabama, I've seen countless growers make expensive or illegal mistakes because a label was misunderstood or a guide wasn't cross-referenced. The shift from just forage to row crops (cotton, peanuts, soybeans) and specialty crops is massive.
**Key Concerns Addressed:**
- *Tank Mixes & Rotational Restrictions:* Row crops have complex rotational restrictions (e.g., planting cotton after corn herbicide programs). The deterministic engine must factor in 'next crop planned' as a hard gate.
- *Usability:* Growers will use this standing by the spray rig on a glare-heavy phone screen. The UI must be high-contrast, large-buttoned, and work offline if cell service drops in rural areas. The shift to a client-side (PWA/GitHub Pages) app is excellent because it can be cached for offline use.
**Verdict:** Strongly approve the deterministic core. Do not let AI hallucinate a tank mix. Keep it strict."

### 3.2 Extension Specialists (Entomology, Pathology, Weed Science)
**Review:**
- **Weed Science:** "The current engine handles herbicides well, but we must expand the data schema to handle distinct weed sizes. A herbicide might be 'Excellent' on 2-inch Palmer amaranth but 'Poor' on 6-inch."
- **Entomology:** "Insect thresholds are dynamic. The tool shouldn't just list insecticides; it must first ask the grower if the economic threshold (e.g., 3 corn earworms per sweep) has been met. The AI component could be useful here to summarize the scouting technique from the IPM guide."
- **Pathology:** "Fungicide efficacy is highly dependent on timing (preventative vs. curative) and resistance management. The system must track Fungicide Resistance Action Committee (FRAC) codes and visually warn users against back-to-back applications of the same mode of action."
**Verdict:** Approve, but the data schema (currently `herbicides.csv`) must be completely overhauled into a relational structure (`crops`, `pests`, `active_ingredients`, `products`, `restrictions`, `efficacy_by_timing`) to handle the nuances of insects and diseases.

### 3.3 Web Developer
**Review:**
"Migrating from Python/Streamlit to a static site on GitHub Pages is highly feasible but requires a complete rewrite of the logic.
**Technical Strategy:**
- We will use **TypeScript** and **React**.
- We will use **GitHub Actions** to automatically parse the ACES source data (CSVs or Excel files) and compile them into minified JSON chunks during the build process.
- **Offline Support:** We will wrap the GitHub Pages deployment in a Service Worker (Progressive Web App - PWA), allowing growers to install the tool to their phone's home screen and use it without cell service.
**Verdict:** The static hosting plan is sound. The AI component will require an external API, meaning the app won't be *100%* offline (the AI summary notes will require a connection, but the core filtering will work offline)."

### 3.4 Automation Engineer
**Review:**
"Maintaining this tool year-over-year as new IPM guides are released is the biggest risk. Currently, it's a manual CSV update.
**Automation Strategy:**
- We need to build a data ingestion pipeline. When ACES releases a new PDF guide, we should run a script (potentially using structured AI extraction, heavily verified by humans) that converts the PDF tables into our structured JSON format.
- **Testing:** The current `test_engine.py` has 5 scenarios. An all-crop tool will have thousands of edge cases. We need an automated test generator that checks every product against its known restrictions to ensure the JavaScript filtering engine is flawless.
**Verdict:** Approve. The CI/CD pipeline must include a step that prevents deployment if the automated constraint-checking tests fail."

---

## 4. Implementation Roadmap (Next Steps)

1. **Phase 1: Data Modeling**
   - Design the new relational data schema (JSON/TypeScript interfaces) capable of handling Herbicides, Insecticides, and Fungicides across multiple crops.
2. **Phase 2: Core Engine Rewrite**
   - Rewrite the Python filtering logic into strict, deterministic TypeScript functions.
   - Write comprehensive unit tests for the TypeScript engine.
3. **Phase 3: Frontend Development**
   - Build a mobile-first React UI. Implement the 'Step-by-Step' grower flow.
4. **Phase 4: AI 'Recommendation Note' Integration**
   - Setup a lightweight serverless function to handle RAG queries against the IPM guide text, ensuring it always cites the specific guide and page.
5. **Phase 5: GitHub Pages Deployment**
   - Setup GitHub Actions to build the site and deploy to the `gh-pages` branch. Configure PWA settings for offline access.