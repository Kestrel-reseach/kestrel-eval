# Project Kestrel Prototype 1 — Step C6 Gate Baseline Computations Report

**Date**: 2026-11-20  
**Phase**: Phase C — Step C6 (R8 Gate Baseline Computations)  
**Status**: **CONFIRMED & AUTHORITATIVE (DECISION D18 CONFIRMED 2026-11-21)**  
**Branch**: `feat/d18-candidate-baselines`  
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`  
**Leading Candidate**: `Qwen/Qwen2.5-1.5B-Instruct` (bitsandbytes 4-bit NF4)  
**Hardware Tier**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB)  
**Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*  
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*  

---

## 1. Executive Summary

This report establishes the empirical baseline values and target pass criteria for all Prototype 1 evaluation gates under **Owner Decision D18–D20**, following the Step 2 Correction Pass:
1. **Code Prompt Re-run**: MBPP prompts supplied with function entry point and first test assertion; synthetic code prompted with explicit top-level function directive. Code accuracy for 1.5B jumped from 18.0% to **48.0%** (MBPP: 36.0%, Synthetic: 60.0%).
2. **Scoring Spec v2.2 (Dev-02)**: Re-scored with conversational copula/award patterns, number unit/year stripping, hyphen normalization, MCQ option E support, and bold math extraction.
3. **Checkable Scope (800 items)**: Accurately scoped to the 4 checkable task groups (`math`, `science_mcq`, `knowledge_mcq`, `code`), resolving the earlier discrepancy.
4. **Candidate Status**: `meta-llama/Llama-3.2-1B-Instruct` is gated on Hugging Face and blocked without `HF_TOKEN`. All baseline values in `manifest.yaml` remain `PENDING_OWNER_CONFIRMATION` until co-owner review.

---

## 2. Gate G-Q: Quality Hurdle on Checkable Groups

Gate G-Q evaluates whether Prototype 1 (P1) achieves a meaningful, statistically verified accuracy lift over B-LLM without increasing energy consumption, or achieves parity at significantly lower energy.

### A. Baseline Measurement (800 Checkable Validation Items)
The checkable subset comprises 4 task groups with objective, automated verifiers:

| Group | Sub-arm Breakdown | $n$ | Baseline Correct | Baseline Accuracy | 95% Wilson CI |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`math`** | GSM8K (100) + Procedural (100) | 200 | 136 | 68.00% | [61.25, 74.07]% |
| **`science_mcq`** | ARC-Challenge (200) | 200 | 125 | 62.50% | [55.61, 68.91]% |
| **`knowledge_mcq`** | MMLU 10 Subjects (300) | 300 | 146 | 48.67% | [43.06, 54.30]% |
| **`code`** | MBPP (50) + Synthetic (50) | 100 | 48 | 48.00% | [38.46, 57.68]% |
| **Checkable Total** | **All 4 Checkable Groups** | **800** | **455** | **56.88%** | **[53.42, 60.27]%** |

- **Baseline Checkable Accuracy**: **56.88%** (455 / 800 items)
- **Baseline Net Energy per Correct Task**: **171.55 J / correct task** (Checkable net energy = 78,055.7 J across 455 correct items)
- **Baseline Gross Energy per Correct Task**: **208.17 J / correct task** (Checkable gross energy = 94,717.0 J)

### B. Target Criteria for Prototype 1 (P1)
To pass Gate G-Q, Prototype 1 must satisfy either Clause 1 or Clause 2:

1. **Clause 1 (Accuracy Superiority)**:
   - Checkable Accuracy: $\text{Acc}(P1) \ge \mathbf{61.88\%}$ (+5.00 pp over baseline).
   - Statistical Significance: Paired bootstrap 95% confidence interval on $\Delta = \text{Acc}(P1) - \text{Acc}(B)$ strictly excludes zero ($\Delta_{\text{lo}} > 0$).
   - Energy Constraint: Net energy $\le \mathbf{171.55\text{ J / correct}}$ ($E(P1) \le E(B)$).
   - *Statistical Power*: At $n = 800$, empirical power to detect a +5.00 pp shift with paired bootstrap is **100.0%**.

2. **Clause 2 (Efficiency Dominance / Non-Inferiority Parity)**:
   - Accuracy Non-Inferiority: $\text{Acc}(P1) \ge \mathbf{53.88\%}$ (within 3.00 pp margin confirmed in D4).
   - Energy Constraint: Net energy $\le \mathbf{85.78\text{ J / correct}}$ ($\le 50.0\%$ of B-LLM energy per correct task).

---

## 3. Gate G-M: Personal Memory Probe & Stale Fact Hurdle

Gate G-M evaluates memory retrieval integrity and guards against stale fact hallucination across personal history logs.

### A. Baseline Measurement (150 Memory Probe Validation Items)
Per Owner Decision D16, the memory probe contains $n = 100$ stale fact items across 36 personal entity clusters:

| Arm | Item Description | $n$ | Baseline Correct | Accuracy | Errors | Error Rate | 95% Wilson CI | 95% Cluster CI |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stale Facts** | Deprecated historical values present | 100 | 78 | 78.00% | **22** | **22.00%** | [15.00, 31.07]% | **[14.0, 30.0]%** |
| **Static Facts** | Constant facts across history logs | 50 | 46 | 92.00% | 4 | 8.00% | [2.70, 19.30]% | [2.0, 18.0]% |
| **Total Memory** | Combined Personal History Probe | 150 | 124 | 82.67% | 26 | 17.33% | [75.81, 87.89]% | [75.0, 88.0]% |

- **Baseline Stale-Fact Errors**: **22 errors** out of 100 items (**22.00%** stale error rate).
- **Baseline Overall Memory Accuracy**: **82.67%** (124 / 150).

### B. Target Criteria for Prototype 1 (P1)
1. **Stale Fact Error Rate**:
   $$\text{Stale Errors}(P1) \le \mathbf{11\text{ errors}} \quad (\text{Stale Error Rate} \le \mathbf{11.00\%})$$
   > [!IMPORTANT]
   > **PROVISIONAL STATUS**: Per Decision D16, Gate G-M is defined against **plain external memory**, which is constructed and evaluated in Step 6. The $\le 11.00\%$ target is **PROVISIONAL** relative to the Step 6 plain memory baseline.
   - *Statistical Power*: At $n = 100$ ($n_{\text{eff}} \approx 40$–$57$ accounting for cluster ICC 0.51), paired testing will be reported with cluster-adjusted bootstrap.
2. **Frontier Reference Bound**:
   - Without history: $\text{Acc}(P1) \ge \text{Acc}(F_{\text{no\_history}})$
   - With full history: $\text{Acc}(P1) \ge \text{Acc}(F_{\text{full\_history}}) - 5.00\text{ pp}$

---

## 4. Gate G-R: Hardware Residency & Resource Budget

Gate G-R enforces strict execution within local edge assistant hardware constraints.

### A. Empirical Baseline & Headroom
- **Target Hardware Tier**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB).
- **Context Length**: 2048 tokens.
- **Assistant VRAM Cap**: $\le \mathbf{1,536.0\text{ MB}}$ (1.5 GB resident GPU memory).

| Resource Metric | B-LLM Baseline | Gate G-R Budget Cap | Margin / Headroom | Status |
| :--- | :---: | :---: | :---: | :---: |
| **NVML Process VRAM** | **1,416.0 MB** | 1,536.0 MB | **+120.0 MB** (7.8% buffer) | **COMPLIANT** |
| **PyTorch Allocated VRAM** | 1,166.0 MB | — | — | Diagnostic only |
| **Checkable Net Joules / Correct** | 171.55 J | $\le 171.55\text{ J}$ (for G-Q acc) | — | Relative NVML Scope |
| **Inference Latency (p50)** | 622.9 ms | — | — | Reported per G-R |
| **Inference Latency (p95)** | 12,101.2 ms | — | — | Reported per G-R |
| **Per-Token Latency** | 45.14 ms/tok | — | — | Reported per G-R |

### B. Resolution of C1 Latency Contradiction (Token-Level vs Median End-to-End)
In Step C1 sanity benchmarks, 4-bit NF4 exhibited a lower median latency (`221.4 ms` vs `386.7 ms`) but a higher per-token latency (`35.81 ms/tok` vs `22.30 ms/tok`) compared to FP16.
- **Root Cause**:
  1. **Token Generation Throughput**: NF4 weights require on-the-fly dequantization during GEMM matrix multiplication, adding computation overhead per token generated (35.81 vs 22.30 ms/token).
  2. **Median (p50) End-to-End Latency**: The suite includes short multiple-choice items (science_mcq and knowledge_mcq) which terminate after 1–2 tokens via `eos_token_id`. For these items, memory bandwidth savings from 50% smaller weights speed up prompt pre-fill loading, yielding lower median end-to-end latency.
  3. **Long Generation (p95)**: On extended math and code generations, the dequantization penalty accumulates, resulting in higher p95 latency (`10,879.6 ms` for NF4 vs `6,561.4 ms` for FP16).

---

## 5. Gate G-F: Frontier Reference Gap-Closing Metric

- **Formula**: $\mathcal{C} = \frac{\text{Acc}(P1) - \text{Acc}(B\text{-LLM})}{\text{Acc}(F) - \text{Acc}(B\text{-LLM})} \times 100\%$
- **Scope**: Checkable groups (800 items).
- **Strong Result Threshold**: $\ge 25.00\%$.
- **Frontier Execution Status**: *"F = gemini-2.5-pro free tier, not run yet"*. External calls deferred until explicit owner instruction. Zero external calls made during this pass.

---

## 6. No-Regression Gate

- **Margin**: 3.00 percentage points (confirmed by Owner Decision D4).
- **Rule**: Accuracy on previously evaluated groups must not drop by more than 3.00 pp across pipeline stages. Report bootstrap confidence intervals.

---

## 7. Authoritative Gate Baselines Summary Table

| Gate | Scope | Metric / Condition | B-LLM Baseline | Prototype 1 Target Hurdle |
| :--- | :--- | :--- | :---: | :--- |
| **Gate G-Q** | 800 checkable items | Accuracy Superiority | **56.88%** (455/800) | $\ge \mathbf{61.88\%}$ (95% CI excludes 0) at $\le \mathbf{171.55\text{ J/correct}}$ |
| **Gate G-Q (Alt)**| 800 checkable items | Efficiency Parity | 171.55 J / correct | $\ge \mathbf{53.88\%}$ (non-inferiority) at $\le \mathbf{85.78\text{ J/correct}}$ |
| **Gate G-M** | 100 stale fact items | Stale Fact Error Rate | **22.00%** (22 errors) | $\le \mathbf{11.00\%}$ (at most **11 errors**) |
| **Gate G-M (F)** | 150 memory items | vs Frontier Bounds | 82.67% overall | $\ge F_{\text{no\_hist}}$, within 5 pp of $F_{\text{full\_hist}}$ |
| **Gate G-R** | 2048 context length | Resident Process VRAM | **1416.0 MB** | $\le \mathbf{1536.0\text{ MB}}$ (1.5 GB limit) |
| **Gate G-F** | 800 checkable items | Gap Closed $\mathcal{C}$ | — | $\mathcal{C} \ge \mathbf{25.00\%}$ when $\Delta(F - B) \ge 5\text{ pp}$ |
| **No-Regression**| All groups | Component delta | — | $\Delta \ge -3.00\text{ pp}$ between incremental components |
