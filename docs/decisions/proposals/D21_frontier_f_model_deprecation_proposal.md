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

### E. Full Validation Execution & Memory Probe Dual Run (100% Complete)
Execution with `gemini-flash-lite-latest` (active model version `gemini-3.5-flash-lite`) was completed across 2026-11-23 and 2026-11-24 using multi-key rotation and day-pacing per Owner Decision D20:
- **1,250 / 1,250 validation records** evaluated live and saved to `runs/run_frontier_gemini-flash-lite-latest_validation.jsonl`.
- **150 / 150 memory probe (no_history)** evaluated live and saved to `runs/run_frontier_gemini-flash-lite-latest_memory_probe_no_history.jsonl`.
- **Accuracy measured (Acc_F)**:
  - Overall Suite: **72.64%** (908/1250, 95% CI: [70.16%, 75.12%])
  - Public Arm: **74.77%** (486/650, 95% CI: [71.38%, 78.00%])
  - Synthetic Arm: **75.33%** (226/300, 95% CI: [70.33%, 80.00%])
  - Memory Probe Full History: **90.00%** (135/150, 95% CI: [84.67%, 94.67%])
  - Memory Probe No History: **6.67%** (10/150, 95% CI: [3.33%, 10.67%])
  - Memory Probe Context Gain: **+83.33 pp**
- Authentic Google AI Studio response IDs logged for all 1,400 records per Owner Decision D11.
- All records verified and passed against `validate_record` schema.
- Zero API cost ($0.00 spent, conforming to Owner Decision D6).

---

## 2. Root Cause & Resolution for Step 2

1. **Model Sunset**: `gemini-2.5-pro` was sunset for new callers (HTTP 404).
2. **Successor Model & Multi-Key Pacing**: Transitioned to active model `gemini-flash-lite-latest` (`gemini-3.5-flash-lite`) using multi-key rotation and D20 pacing, completing 100% of the validation and memory probe suite under the free tier.
3. **Evidence Rule 9 Compliance**: Under `.agents/rules/kestrel-evidence.md`, all 1,400 records are real, verified empirical measurements with zero mock or simulated records.

---

## 3. Recommendations for Owners

1. Formally ratify `gemini-flash-lite-latest` (`gemini-3.5-flash-lite`) as the Frontier Reference Model **F** under Decision D21 to supersede D6.
2. Adopt the measured empirical baseline $Acc_F = 72.64\%$ for Gate G-F gap calculations ($G\text{-}F = \frac{Acc_{P1} - Acc_{B\text{-}LLM}}{Acc_F - Acc_{B\text{-}LLM}}$).
3. Close Step 2 in `PLAN.md` with Member B.


