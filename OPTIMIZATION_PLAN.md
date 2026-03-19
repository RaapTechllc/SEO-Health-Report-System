# Optimization Plan: Project "A-Grade"

**Objective:** Elevate the SEO Health Report system from a promising prototype (Grade B+) to a market-ready, enterprise-grade solution (Grade A).

**Success Metric:** `Stripe.com` (and similar gold-standard sites) must score >90/100.

---

## Phase 1: Scoring Calibration (The "Stripe Test")

**Diagnosis:** The current scoring algorithm penalizes modern, high-performing React/Next.js websites.
*   *Issue:* "Low text-to-HTML ratio" is flagged as poor. (Modern apps are heavy on JS/Markup).
*   *Issue:* "Multiple H1 tags" is flagged as a critical error. (HTML5 `<section>` allows multiple H1s).
*   *Issue:* Readability scores penalize technical language.

**Action Items:**
1.  **Refine `seo-content-authority` Scoring:**
    *   Adjust `text_ratio` threshold for JS-heavy sites.
    *   Update Heading checks to respect HTML5 semantic nesting.
    *   Calibrate "Readability" metrics to account for industry-specific terminology.
2.  **Smart Weighting:**
    *   Reduce weight of "Meta Keywords" (obsolete) to 0.
    *   Increase weight of "Core Web Vitals" and "Structured Data".

## Phase 2: AI Visibility & Data Fidelity

**Diagnosis:** The AI Visibility component failed to return data for Stripe, likely due to API key handling or rate limiting, resulting in a Score of 0 for that section.
*   *Issue:* `ai_responses` array was empty in the JSON output.
*   *Issue:* PageSpeed Insights failed with "Rate Limited".

**Action Items:**
1.  **Fix `ai-visibility-audit`:**
    *   Debug `query_ai_systems.py`: Ensure it correctly falls back to mocks if keys are missing, OR explicitly warns the user.
    *   Implement "Gemini First" querying as the primary default.
    *   Add robust retry logic for API calls.
2.  **API Resilience:**
    *   Implement caching for PageSpeed API calls to prevent rate limits during development.
    *   Add better error messages for missing keys (don't fail silently).

## Phase 3: The "Grokopedia" Engine

**Diagnosis:** We need to move beyond standard SEO checks to "Answer Engine Optimization" (AEO).

**Action Items:**
1.  **LLM Parseability Check:**
    *   Create a new check that converts the page to Markdown (what an LLM sees) and grades the *cleanliness* of that Markdown.
    *   Check for "Fact Density": How many extractable facts exist in the first 1000 tokens?
2.  **Knowledge Graph Validator:**
    *   Deepen the `check_knowledge.py` script to verify not just existence, but *consistency* of data across Wikidata, Crunchbase, and LinkedIn.

## Phase 4: Premium User Experience

**Diagnosis:** The UI is clean but lacks the "Executive Polish" requested (PDFs, animations).

**Action Items:**
1.  **Visual PDF Generation:**
    *   Utilize `gemini_integration.py` (Imagen 3.0) to generate cover images for reports.
    *   Implement `generate_premium_report.py` to output a boardroom-ready PDF.
2.  **Dashboard Enhancements:**
    *   Add "Trend Lines" (Mocked for now, but ready for DB) to show score improvement over time.
    *   Add "Competitor Face-off" visualization.

---

## Execution Roadmap

| Step | Task | Target Grade (Stripe) |
| :--- | :--- | :--- |
| **1** | **Calibrate Scoring Logic** (Fix weights & modern SEO rules) | **B- -> A-** |
| **2** | **Restore AI Visibility** (Fix API connections & Gemini) | **A- -> A** |
| **3** | **Enhance Technical Depth** (PageSpeed & Backlinks) | **A -> A+** |
| **4** | **Final UI Polish** (PDFs & Charts) | **User Wow Factor** |
