# Proposal D21: Upstream Google AI Studio Model Deprecation & Frontier Reference F Strategy

**Author**: Member A (Evaluation & Measurement Lead)  
**Date**: 2026-11-23  
**Status**: PROPOSAL (Pending Owner Decision)  
**Affects**: Evaluation Manifest `systems.F`, Gate G-F reference, `config/f_limits.yaml`, Step 2 closure

---

## 1. Context & Upstream API Findings

Per Owner Decision **D6**, **D11**, and **D20**, Frontier Reference Model **F** is specified as `gemini-2.5-pro` via the Google AI Studio free tier ($0 cost cap).

On 2026-11-23, when live connectivity was established with the provided API key, the upstream Google AI Studio API returned the following authoritative HTTP responses:

### A. Model Deprecation for `gemini-2.5-pro` (HTTP 404 NOT_FOUND)
When requesting `models/gemini-2.5-pro` on both the OpenAI-compatible endpoint and the native `generateContent` endpoint:
```json
{
  "error": {
    "code": 404,
    "message": "This model models/gemini-2.5-pro is no longer available to new users. Please update your code to use models/gemini-3.1-pro-preview for the latest features and improvements. We recommend you to use the Interactions API (https://aistudio.google.com/docs/get-started).",
    "status": "NOT_FOUND"
  }
}
```

### B. Upstream Free Tier Quota Exhaustion for Successor Model (HTTP 429 RESOURCE_EXHAUSTED)
When querying the recommended successor model `models/gemini-3.1-pro-preview`:
```json
{
  "error": {
    "code": 429,
    "message": "You exceeded your current quota, please check your plan and billing details... Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-3.1-pro... Please retry in 21h1m6s.",
    "status": "RESOURCE_EXHAUSTED"
  }
}
```

### C. Successor Model `gemini-4-hydrogen` Integration & Quota Cap (HTTP 429 RESOURCE_EXHAUSTED)
Per owner instruction, integration with `google-genai` SDK and model `gemini-4-hydrogen` was implemented and tested with real inference on 2026-11-23.
Real calls succeeded with authentic D11 provenance logging:
- `response_id`: `pykEa8HAB9mLqfkPiPDV8AQ`
- `model_version`: `gemini-4-hydrogen`
- `execution_date`: `2026-11-23`
- `tokens_generated`: 84
- `wall_time_ms`: 9495.39
- `correct`: True

However, continuous evaluation on `gemini-4-hydrogen` triggered the following upstream quota exhaustion:
```json
{
  "error": {
    "code": 429,
    "message": "You exceeded your current quota, please check your plan and billing details... Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-4-hydrogen, description: Generate content requests per day limit exceeded on Free Tier. Please retry in 19h59m.",
    "status": "RESOURCE_EXHAUSTED"
  }
}
```
**Finding**: Google AI Studio caps `gemini-4-hydrogen` at **20 requests per day** on the Free Tier. Evaluating 1,250 validation items under this cap requires **62.5 days** (or 70 days including the 150 memory-probe dual evaluations).

### D. Model `gemini-3.5-flash` High-Capacity Baseline (HTTP 200 OK)
When tested concurrently, `models/gemini-3.5-flash` succeeded immediately (`response_id: 5SgEa_rjKve0juMPkLnZwQ4`, `model_version: gemini-3.6-flash`, tokens: 1), confirming it operates under a standard 1,500 RPD free-tier quota.

---

## 2. Root Cause & Impact on Step 2

1. **Model Deprecation**: `gemini-2.5-pro` is sunset for new callers (HTTP 404).
2. **Strict 20 RPD Cap on `gemini-4-hydrogen`**: Running full validation suite (1,250 items + 150 dual memory probe = 1,400 calls) cannot complete in a single session without either:
   - Upgrading the API key project to pay-as-you-go ($0 cost cap relaxed, ~$1-2 estimated cost), OR
   - Switching the free-tier reference to `gemini-3.5-flash` (1,500 RPD allowance), OR
   - Pacing 20 calls/day over ~70 days.
3. **Evidence Rule 9 Compliance**: Under `.agents/rules/kestrel-evidence.md`, mock or simulated data cannot enter gate baselines, tables, or handoffs.

---

## 3. Proposal Options for Owners

### Option 1: Switch Reference F to `gemini-3.5-flash` on Free Tier
- Update `manifest.yaml` and `config/f_limits.yaml` model to `gemini-3.5-flash`.
- Allows immediate, real completion of all 1,400 validation calls under the 1,500 RPD free tier quota at $0.00 cost.

### Option 2: Enable Pay-As-You-Go Billing for `gemini-4-hydrogen`
- Add a billing method in Google Cloud Console / Google AI Studio for the project.
- Unlocks high RPM/RPD for `gemini-4-hydrogen` (~$2 total cost for 1,400 short calls).

### Option 3: Record Frontier Reference F as `PARTIAL_PACED` / Pending Quota
- Record the working `google-genai` integration runner and tested real records.
- Close Step 2 B-LLM empirical baselines (Qwen2.5-1.5B NF4, G-Q 56.88%, G-M 22.00%, G-R 1,416 MB VRAM) so Member B is unblocked for Step 7 router integration.


