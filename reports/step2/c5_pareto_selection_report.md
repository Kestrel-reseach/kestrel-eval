# Project Kestrel Prototype 1 — Step C5 B-LLM Selection Proposal & Pareto Analysis

**Date**: 2026-11-20  
**Phase**: Phase C — Step C5 (R7 Candidate Selection & Pareto Frontier)  
**Status**: **PROPOSAL (PENDING CO-OWNER CONFIRMATION PER DECISION D18)**  
**Branch**: `suite-v2`  
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`  
**Mandatory Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*  
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*  

---

## 1. Candidate Scope & Release Provenance

Per Owner Decision **D18** and **D19**, candidate evaluation encompasses the five Option A shortlist candidates plus time-boxed exploration of Qwen3.5:

| Candidate Model | Creator / Org | Release Date | License | HF Gating / Hub Status | Evaluation Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `Qwen/Qwen2.5-0.5B-Instruct` | Alibaba Group | Sept 2024 | Apache 2.0 | Ungated | **Evaluated (1,250 items)** |
| `Qwen/Qwen2.5-1.5B-Instruct` | Alibaba Group | Sept 2024 | Apache 2.0 | Ungated | **Evaluated (1,250 items)** |
| `meta-llama/Llama-3.2-1B-Instruct` | Meta AI | Sept 2024 | Llama 3.2 Community | **Gated (`manual`)** | **BLOCKED: HF_TOKEN unset** |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | Hugging Face | Oct 2024 | Apache 2.0 | Ungated | Shortlisted under D19 |
| `ibm-granite/granite-4.0-1b` | IBM Research | Oct 2024 | Apache 2.0 | Ungated | Shortlisted under D19 |
| `Qwen/Qwen3.5-0.8B` | Alibaba Group | March 2026 | Apache 2.0 | Ungated | Time-boxed exploration (D19) |

*Audit Notice*: `meta-llama/Llama-3.2-1B-Instruct` returned `401 Client Error: You are trying to access a gated repo.` when queried without an active `HF_TOKEN`. Per prompt protocol, execution pauses for co-owner token provision.

---

## 2. Pareto Frontier Analysis (800-Item Checkable Scope)

Trade-off analysis evaluated under Deviation Dev-02 scoring and post-code prompt fix:

| Metric | `Qwen2.5-0.5B-Instruct` (NF4) | `Qwen2.5-1.5B-Instruct` (NF4) | Delta (1.5B vs 0.5B) | Trade-Off Direction |
| :--- | :---: | :---: | :---: | :--- |
| **Checkable Scope Accuracy (800 items)** | **37.00%** (296/800) | **56.88%** (455/800) | **+19.88 pp** | 1.5B dominates on checkable accuracy |
| - 95% Wilson CI | [33.72, 40.40]% | [53.42, 60.27]% | Non-overlapping | Decisive separation |
| **Math Accuracy (200 items)** | 33.50% [27.32, 40.30] | **68.00%** [61.25, 74.07] | **+34.50 pp** | 1.5B dominates on reasoning |
| - GSM8K Public (100 items) | 24.00% | 63.00% | +39.00 pp | Zero-shot NF4 math capacity |
| - Synthetic Math (100 items) | 43.00% | 73.00% | +30.00 pp | Procedural math capacity |
| **Science MCQ (200 items)** | 47.50% [40.69, 54.40] | **62.50%** [55.61, 68.91] | **+15.00 pp** | 1.5B dominates on ARC |
| **Knowledge MCQ (300 items)** | 36.33% [31.10, 41.92] | **48.67%** [43.06, 54.30] | **+12.34 pp** | 1.5B dominates on MMLU |
| **Code Generation (100 items)** | 25.00% [17.55, 34.30] | **48.00%** [38.46, 57.68] | **+23.00 pp** | 1.5B dominates with fixed MBPP prompts |
| - MBPP Public (50 items) | 22.00% (11/50) | 36.00% (18/50) | +14.00 pp | Unit test pass rate |
| - Synthetic Code (50 items) | 28.00% (14/50) | 60.00% (30/50) | +32.00 pp | Procedural function pass rate |
| **Code Truncation Rate** | 1.00% (1/100) | **0.00%** (0/100) | -1.00 pp | 1.5B satisfies <1% rule |
| **Knowledge QA Diagnostic (300 items)**| 67.00% [61.49, 72.08] | **68.33%** [62.87, 73.34] | +1.33 pp | Parity within 95% CI |
| - Fictional Entity Arm (100 items) | 71.00% | 72.00% | +1.00 pp | BM25 retrieval without memorization |
| **Memory Probe (150 items)** | 69.33% [61.55, 76.15] | **82.67%** [75.81, 87.89] | **+13.34 pp** | 1.5B dominates on history |
| **Stale Fact Error Rate (100 items)** | 41.00% [31.87, 50.80] | **22.00%** [15.00, 31.07] | **-19.00 pp** | 1.5B halves stale hallucinations |
| - Cluster 95% CI (100 clusters) | [32.0, 50.0]% | [14.0, 30.0]% | Non-overlapping | Robust entity-cluster CI |
| **NVML Process VRAM (2048 ctx)** | **632.0 MB** | **1,416.0 MB** | +784.0 MB | Both fit under 1,536 MB budget |
| **PyTorch Allocated VRAM** | **460.2 MB** | **1,166.0 MB** | +705.8 MB | 120.0 MB headroom for 1.5B |
| **Checkable Net Joules / Correct Task** | **157.54 J** | **171.55 J** | +14.01 J | 0.5B has slightly lower net energy |
| **Total Wall Time (Checkable Scope)** | **2,180.5 s** (36.3 min) | 2,711.6 s (45.2 min) | +531.1 s | 0.5B runs faster |

---

## 3. Proposal Recommendation for Co-Owners

Member A submits the following recommendation for Co-Owner confirmation under **Decision D18**:
1. **Tentative Selection**: `Qwen2.5-1.5B-Instruct` (NF4) is proposed as B-LLM.
2. **Rationale**:
   - Accuracy on the checkable scope is **56.88%** (455/800) vs **37.00%** (296/800) for 0.5B (**+19.88 pp** gain).
   - Multi-step word problem reasoning is more than double (68% vs 33.5%).
   - Stale fact error rate is halved from 41% down to 22%.
   - Process VRAM (1,416.0 MB) fits within the 1,536 MB Gate G-R budget with 120.0 MB headroom.
3. **Formal Confirmation**: Per D18, this selection becomes final only after all candidates have been evaluated and the co-owners explicitly confirm. Manifest v2.2 maintains `PENDING_OWNER_CONFIRMATION` pending owner action.
