# Project Kestrel Prototype 1 — Step C3 Evaluation Controls Report

**Date**: 2026-11-20
**Phase**: Phase C — Step C3 (R5 Evaluation Controls)
**Branch**: `suite-v2`
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`
**Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*

---

## 1. Executive Summary

Step C3 executed four formal evaluation controls to verify that baseline model measurements reflect genuine task performance rather than evaluation harness artifacts, positional bias, or stochastic non-determinism:
1. **Determinism Control (100 Stratified Items, Evaluated Twice on GPU)**: **100.0% bit-for-bit hash identity** (100/100 matches). The inference harness is strictly deterministic under greedy decoding.
2. **Shuffled-Option Position Control (100 MCQ Items, Permuted Choices)**:
   - Original Accuracy: **38.0%** (38/100)
   - Permuted Accuracy: **38.0%** (38/100)
   - Accuracy Delta: **+0.00 pp**
   - Positional Bias Rate: **27.0%** (27/100)
   - Confirms the model predominantly attends to semantic option text rather than positional letter bias.
3. **Constant Answer Baseline Controls**:
   - **Always 'A' Baseline (500 MCQ items)**: **22.4%** (95% CI: [18.75, 26.05])
   - **Most Frequent Key Baseline ('D')**: **28.2%** (95% CI: [24.26, 32.14])
   - **Degenerate Open-Ended Constants**: Constant '0' on math yields 0.0%, empty pass on code yields 0.0%, constant 'Unknown' yields 0.0% on QA and 0.0% on memory probe.
4. **Uniform Random Baseline Hypothesis Test**:
   - 4-choice chance expectation: **25.0%** (95% CI: [21.2, 28.8])
   - `Qwen2.5-0.5B-Instruct` MCQ accuracy: **40.80%** ($Z = 8.16, p < 10^{-15}$).
   - `Qwen2.5-1.5B-Instruct` MCQ accuracy: **54.20%** ($Z = 15.08, p < 10^{-30}$).
   - Both candidates perform massively above chance ($Z \gg 3.0$).

---

## 2. Determinism Audit Details

- **Test Set**: 100 items stratified proportionally across all 6 groups (20 math, 20 science, 20 knowledge MCQ, 10 code, 20 QA, 10 memory).
- **Execution Mode**: Evaluated in two independent generation passes on NVIDIA GeForce RTX 3050 Laptop GPU using bitsandbytes 4-bit NF4.
- **Verification Method**: SHA-256 digest of stripped decoded text compared per item.
- **Result**:
  $$\text{Match Rate} = \frac{100}{100} = 100.0\%$$
  Zero drift, zero non-deterministic token divergence.

---

## 3. Option Permutation & Positional Bias Audit

- **Methodology**: 100 validation MCQ items (50 ARC-Challenge, 50 MMLU) were cyclically shifted:
  $$A \to B, \quad B \to C, \quad C \to D, \quad D \to A$$
  The ground truth target letter is updated identically.
- **Results**:
  - Original 100-item accuracy: **38.0%**
  - Permuted 100-item accuracy: **38.0%**
  - Net Delta: **+0.00 pp**
  - Items where model picked old position: **27 / 100 (27.0%)**
- **Conclusion**: The model's predictions are governed by semantic relevance of the option string rather than fixed choice-letter heuristic.

---

## 4. Key Distribution & Constant Baseline Analysis

### A. Ground Truth MCQ Key Balance (n=500)
- Distribution: `{'A': 112, 'D': 141, 'C': 119, 'B': 127, 'E': 1}`

### B. Candidate Outperformance vs. Constant Baselines
- Always 'A' Baseline: **22.4%**
- Most Frequent Key ('D'): **28.2%**
- `Qwen2.5-0.5B-Instruct` MCQ: **40.80%** (+12.60 pp over best constant)
- `Qwen2.5-1.5B-Instruct` MCQ: **54.20%** (+26.00 pp over best constant)

---

## 5. Statistical Significance vs. Chance

| System | MCQ Items | Accuracy | Chance | Z-Score | Statistical Significance |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Random Uniform Choice** | 500 | 25.00% | 25.00% | 0.00 | Expected Null |
| **`Qwen2.5-0.5B-Instruct`** | 500 | 40.80% | 25.00% | +8.16 | $p < 10^{-15}$ (PASS) |
| **`Qwen2.5-1.5B-Instruct`** | 500 | 54.20% | 25.00% | +15.08 | $p < 10^{-30}$ (PASS) |

---

## 6. Audit Verdict

All four evaluation controls pass conclusively:
- [x] **Determinism**: 100/100 outputs identical.
- [x] **Positional Invariance**: Minimal accuracy change under choice cyclic permutation.
- [x] **Constant Baseline Separation**: Both candidates decisively exceed constant heuristics.
- [x] **Chance Null Rejection**: Rejects random null at $p < 10^{-15}$.
