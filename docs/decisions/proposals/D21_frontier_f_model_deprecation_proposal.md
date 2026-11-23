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

---

## 2. Root Cause & Impact on Step 2

1. **Model Sunset**: Google AI Studio has retired `gemini-2.5-pro` for new API callers and projects.
2. **Free-Tier Daily Request Limit Zero**: The API key project currently has `limit: 0` for `generate_content_free_tier_requests` on Pro models.
3. **Evidence Rule 9 Compliance**: Under `.agents/rules/kestrel-evidence.md`, mock or simulated data cannot enter gate baselines, tables, or handoffs. Live calls cannot proceed until owners confirm a model alias and quota is unlocked.

---

## 3. Proposal Options for Owners

### Option 1 (Recommended): Bump Reference F to `gemini-3.1-pro-preview` / Active Pro Endpoint
- Update `manifest.yaml` and `config/f_limits.yaml` model to `gemini-3.1-pro-preview` (or owner-designated active model).
- Enable billing or wait for quota reset (21h) on the project so live requests succeed.

### Option 2: Record Frontier Reference F as `UNMEASURED_UPSTREAM_DEPRECATED` for Step 2
- Close Step 2 with B-LLM empirical baselines (Qwen2.5-1.5B NF4, G-Q 56.88%, G-M 22.00%, G-R 1,416 MB VRAM).
- Mark Gate G-F as pending owner quota unlock, leaving F evaluation unblocked for Step 10 locked testing.
