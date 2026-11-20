# Project Kestrel Prototype 1 — Step C6 Gate Baseline Computations Report

**Date**: 2026-11-20  
**Phase**: Phase C — Step C6 (R8 Gate Baseline Computations)  
**Branch**: `suite-v2`  
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`  
**Selected B-LLM**: `Qwen/Qwen2.5-1.5B-Instruct` (bitsandbytes 4-bit NF4)  
**Hardware Tier**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB)  
**Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*  
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*  

---

## 1. Executive Summary

This report establishes and freezes the official empirical baseline values and target pass criteria for all Prototype 1 evaluation gates. All metrics are computed strictly against the selected **B-LLM (`Qwen2.5-1.5B-Instruct` 4-bit NF4)** evaluated on the full **1,250 items** of the Suite v2.1 validation partition.

Per the frozen project rules:
> **"Never change a metric or threshold after seeing results."**  
All gate thresholds, formulas, and target values established herein are immutable for Prototype 1 evaluation.

---

## 2. Gate G-Q: Quality Hurdle on Checkable Groups

Gate G-Q evaluates whether Prototype 1 (P1) achieves a meaningful, statistically verified accuracy lift over B-LLM without increasing energy consumption, or achieves parity at significantly lower energy.

### A. Baseline Measurement (800 Checkable Validation Items)
The checkable subset comprises 4 task groups with objective, automated verifiers:

| Group | Sub-arm Breakdown | $n$ | Baseline Correct | Baseline Accuracy | 95% Wilson CI |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`math`** | GSM8K (100) + Procedural (100) | 200 | 129 | 64.50% | [57.65, 70.80]% |
| **`science_mcq`** | ARC-Challenge (200) | 200 | 125 | 62.50% | [55.61, 68.91]% |
| **`code`** | MBPP (50) + Synthetic (50) | 100 | 18 | 18.00% | [11.70, 26.67]% |
| **`knowledge_qa`** | Wikipedia Real (200) + Fictional (100) | 300 | 195 | 65.00% | [59.44, 70.18]% |
| **Pooled Checkable** | **All 4 Groups Combined** | **800** | **467** | **58.38%** | **[54.93, 61.74]%** |

- **Baseline Checkable Accuracy**: **58.38%** (467 / 800)
- **Baseline Net Energy per Correct Task**: **120.40 J**

### B. Target Criteria for Prototype 1 (P1)
To pass Gate G-Q, Prototype 1 must satisfy either Clause 1 or Clause 2:

1. **Clause 1 (Accuracy Superiority)**:
   - Checkable Accuracy: $\text{Acc}(P1) \ge \mathbf{63.38\%}$ (+5.00 pp over B-LLM).
   - Statistical Significance: Paired bootstrap 95% confidence interval on $\Delta = \text{Acc}(P1) - \text{Acc}(B)$ strictly excludes zero ($\Delta_{\text{lo}} > 0$).
   - Energy Constraint: Net energy $\le \mathbf{120.40\text{ J / correct}}$ ($E(P1) \le E(B)$).
   - *Statistical Power*: At $n = 800$, empirical power to detect a +5.00 pp shift with paired bootstrap is **100.0%**.

2. **Clause 2 (Efficiency Dominance / Non-Inferiority Parity)**:
   - Accuracy Non-Inferiority: $\text{Acc}(P1) \ge \mathbf{55.38\%}$ (within 3.00 pp margin confirmed in D4).
   - Energy Constraint: Net energy $\le \mathbf{60.20\text{ J / correct}}$ (<= 50.0% of B-LLM energy per correct task).

---

## 3. Gate G-M: Personal Memory Probe & Stale Fact Hurdle

Gate G-M evaluates memory retrieval integrity and guards against stale fact hallucination across personal history logs.

### A. Baseline Measurement (150 Memory Probe Validation Items)
Per Owner Decision D16, the memory probe contains $n_{\text{eff}} = 100$ stale fact items:

| Arm | Item Description | $n$ | Baseline Correct | Accuracy | Errors | Error Rate | 95% Wilson CI |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stale Facts** | Outdated historical values present | 100 | 78 | 78.00% | **22** | **22.00%** | [68.93, 85.00]% |
| **Static Facts** | Ground truth constant across logs | 50 | 46 | 92.00% | 4 | 8.00% | [2.70, 19.30]% |
| **Total Memory** | Combined Personal History Probe | 150 | 124 | 82.67% | 26 | 17.33% | [76.61, 88.72]% |

- **Baseline Stale-Fact Errors**: **22 errors** out of 100 items (**22.00%** stale error rate).
- **Baseline Overall Memory Accuracy**: **82.67%** (124 / 150).

### B. Target Criteria for Prototype 1 (P1)
1. **Stale Fact Error Rate**: P1 must cut stale fact errors at least in half relative to B-LLM:
   $$\text{Stale Errors}(P1) \le \mathbf{11\text{ errors}} \quad (\text{Stale Error Rate} \le \mathbf{11.00\%})$$ 
   *Statistical Power*: At $n_{\text{eff}} = 100$, one-sided McNemar test power for cutting errors from 22 to 11 is **94.0%**.
2. **Frontier Reference Bound**:
   - Without history: $\text{Acc}(P1) \ge \text{Acc}(F_{\text{no\_history}})$
   - With full history: $\text{Acc}(P1) \ge \text{Acc}(F_{\text{full\_history}}) - 5.00\text{ pp}$

---

## 4. Gate G-R: Hardware Residency & Resource Budget

Gate G-R enforces strict execution within local edge assistant hardware constraints.

### A. Empirical Baseline & Headroom
- **Target Hardware Tier**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB).
- **Context Length**: 2048 tokens.
- **Assistant VRAM Cap**: $\le \mathbf{1536.0\text{ MB}}$ (1.5 GB resident GPU memory).

| Resource Metric | B-LLM Baseline | Gate G-R Budget Cap | Margin / Headroom | Status |
| :--- | :---: | :---: | :---: | :---: |
| **NVML Process VRAM** | **1416.0 MB** | 1536.0 MB | **+120.0 MB** (7.8% buffer) | **COMPLIANT** |
| **PyTorch Allocated VRAM** | 1166.0 MB | — | — | Diagnostic only |
| **Net Joules / Correct Task** | 120.40 J | $\le 120.40\text{ J}$ (for G-Q acc) | — | Relative NVML Scope |
| **Inference Latency (p50)** | 622.9 ms | — | — | Reported per G-R |
| **Inference Latency (p95)** | 12101.2 ms | — | — | Reported per G-R |
| **Per-Token Latency** | 45.14 ms/tok | — | — | Reported per G-R |

---

## 5. Gate G-F: Frontier Reference Gap-Closing Metric

Gate G-F provides an external benchmark of Prototype 1's progress toward frontier capabilities.

### A. Formal Metric Definition
$$\mathcal{C} = \frac{\text{Acc}(P1) - \text{Acc}(B\text{-LLM})}{\text{Acc}(F) - \text{Acc}(B\text{-LLM})} \times 100\%$$

- **Evaluation Scope**: Checkable groups (800 items).
- **Strong Result Definition**: If $\text{Acc}(F) - \text{Acc}(B\text{-LLM}) \ge 5.00\text{ pp}$, achieving $\mathcal{C} \ge \mathbf{25.00\%}$ is formally designated as a strong result.
- **Reference Model**: gemini-2.5-pro (free tier reference).
- **Execution Status**: *"F = gemini-2.5-pro free tier, not run yet"*. Execution is deferred to post-suite freeze at Step 10 under one-time-use exposure constraints (Decision D12).

---

## 6. No-Regression Gate

- **Margin**: 3.00 percentage points (confirmed by Owner Decision D4).
- **Rule**: When adding any component to Prototype 1 (e.g., verifier head, memory cache, tool execution), accuracy on previously evaluated groups must not decrease by more than 3.00 pp relative to the immediate prior step.

---

## 7. Authoritative Gate Baselines Summary Table

| Gate | Scope | Metric / Condition | B-LLM Baseline | Prototype 1 Target Hurdle |
| :--- | :--- | :--- | :---: | :--- |
| **Gate G-Q** | 800 checkable items | Accuracy Superiority | **58.38%** (467/800) | $\ge \mathbf{63.38\%}$ (95% CI excludes 0) at $\le \mathbf{120.40\text{ J/correct}}$ |
| **Gate G-Q (Alt)**| 800 checkable items | Efficiency Parity | 120.40 J / correct | $\ge \mathbf{55.38\%}$ (non-inferiority) at $\le \mathbf{60.20\text{ J/correct}}$ |
| **Gate G-M** | 100 stale fact items | Stale Fact Error Rate | **22.00%** (22 errors) | $\le \mathbf{11.00\%}$ (at most **11 errors**) |
| **Gate G-M (F)** | 150 memory items | vs Frontier Bounds | 82.67% overall | $\ge F_{\text{no\_hist}}$, within 5 pp of $F_{\text{full\_hist}}$ |
| **Gate G-R** | 2048 context length | Resident Process VRAM | **1416.0 MB** | $\le \mathbf{1536.0\text{ MB}}$ (1.5 GB limit) |
| **Gate G-F** | 800 checkable items | Gap Closed $\mathcal{C}$ | — | $\mathcal{C} \ge \mathbf{25.00\%}$ when $\Delta(F - B) \ge 5\text{ pp}$ |
| **No-Regression**| All groups | Component delta | — | $\Delta \ge -3.00\text{ pp}$ between incremental components |
