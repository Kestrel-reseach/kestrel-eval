# Project Kestrel Prototype 1 — Step C5 B-LLM Selection & Pareto Frontier Report

**Date**: 2026-11-20
**Phase**: Phase C — Step C5 (R7 Candidate Selection & Pareto Frontier)
**Branch**: `suite-v2`
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`
**Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*

---

## 1. Executive Summary & Selection Decision

Based on full measurement across all 1,250 validation items under the frozen scoring specification, **`Qwen2.5-1.5B-Instruct` (4-bit NF4)** is officially selected as **B-LLM** for Project Kestrel Prototype 1.

### Key Decision Drivers:
1. **Decisive Quality Hurdle**: `Qwen2.5-1.5B` achieves **58.96% accuracy** vs. **47.44%** for `Qwen2.5-0.5B` (**+11.52 pp**, 95% paired bootstrap CI: **[+8.40, +14.56] pp**, $p < 0.0001$).
2. **Real Multi-Step Reasoning Capacity**: On GSM8K math word problems, `Qwen2.5-1.5B` achieves **64.50%** vs **33.50%** for `0.5B` (**+31.00 pp**).
3. **Memory Integrity (Gate G-M)**: `Qwen2.5-1.5B` cuts the stale-fact error rate nearly in half from **41.00%** (0.5B) down to **22.00%** (**-19.00 pp** reduction in hallucinations).
4. **Resident VRAM Compliance (Gate G-R)**: At a 2048-token context, `Qwen2.5-1.5B` consumes **1,416.0 MB** NVML process VRAM (and 1,166.0 MB PyTorch allocated), **strictly within the 1,536.0 MB (1.5 GB) assistant GPU budget**.
5. **Energy-Quality Trade-Off**: `1.5B` consumes **120.40 Net Joules per correct task** (vs 68.80 J for 0.5B). This +75.0% energy investment delivers +24.3% more correct tasks, eliminating severe capability bottlenecks.

---

## 2. Pareto Frontier Analysis

Both candidate models define non-dominated points on the Pareto frontier:

| Metric | `Qwen2.5-0.5B-Instruct` (NF4) | `Qwen2.5-1.5B-Instruct` (NF4) | Trade-Off Analysis |
| :--- | :---: | :---: | :--- |
| **Overall Accuracy** | 47.44% [44.67, 50.21] | **58.96%** [56.23, 61.69] | 1.5B dominates on quality (+11.52 pp) |
| **Math Accuracy** | 33.50% [26.96, 40.04] | **64.50%** [57.87, 71.13] | 1.5B dominates on reasoning (+31.00 pp) |
| **Science MCQ** | 47.50% [40.58, 54.42] | **62.50%** [55.79, 69.21] | 1.5B dominates on science (+15.00 pp) |
| **Knowledge MCQ** | 36.33% [30.89, 41.78] | **48.67%** [43.01, 54.32] | 1.5B dominates on MMLU (+12.33 pp) |
| **Code Generation** | 19.00% [11.31, 26.69] | 18.00% [10.47, 25.53] | Parity within 95% CI (-1.00 pp) |
| **Knowledge QA (BM25)** | 66.33% [60.99, 71.68] | 65.00% [59.60, 70.40] | Parity within 95% CI (-1.33 pp) |
| **Memory Probe** | 69.33% [61.95, 76.71] | **82.67%** [76.61, 88.72] | 1.5B dominates on history (+13.33 pp) |
| **Stale Fact Error Rate** | 41.00% (41 errors) | **22.00%** (22 errors) | 1.5B dominates on G-M (-19.00 pp) |
| **NVML Process VRAM** | **632.0 MB** | **1416.0 MB** | 0.5B is lighter; both fit <= 1.5 GB budget |
| **PyTorch Allocated VRAM** | **460.2 MB** | **1166.0 MB** | 0.5B is lighter |
| **Net Joules / Correct Task** | **68.80 J** | 120.40 J | 0.5B dominates on energy efficiency |
| **Latency p50** | **212.6 ms** | 622.9 ms | 0.5B has lower latency |
| **Throughput (ms / token)** | **34.48 ms/tok** | 45.14 ms/tok | 0.5B is 1.31x faster per token |

---

## 3. Justification for B-LLM Selection

1. **Rejection of 0.5B as B-LLM**:
   - Although `Qwen2.5-0.5B` achieves high energy efficiency (68.80 J/correct), its 33.5% math accuracy and 41% stale-fact error rate are severely impaired. Selecting 0.5B would compromise the baseline against which Prototype 1 (P1) is judged, allowing trivial modifications to claim artificial victories.
2. **Selection of 1.5B as B-LLM**:
   - `Qwen2.5-1.5B-Instruct` provides a realistic, robust, and competitive assistant baseline.
   - It operates well within the 1.5 GB resident GPU budget (1,416 MB process used, 1,166 MB allocated).
   - Its hidden dimension ($d = 1,536$) provides Member B with rich internal representations for training the verifier head in Step 3.

---

## 4. Frozen Gate Baselines Established for B-LLM (`Qwen2.5-1.5B`)

With `Qwen2.5-1.5B-Instruct` selected as B-LLM, the empirical gate hurdles are formally established:

- **Gate G-Q Hurdle** (800 items: math, science, code, knowledge QA):
  $$\text{Baseline Accuracy} = \mathbf{58.38\%} \quad (467 / 800)$$
  *Target*: P1 must achieve $\ge 63.38\%$ (+5.0 pp, paired bootstrap excludes 0) at $\le 120.40\text{ J/correct}$, or match $58.38\%$ at $\le 60.20\text{ J/correct}$ (50% energy savings).

- **Gate G-M Hurdle** (100 stale fact items in memory probe):
  $$\text{Baseline Stale Error Rate} = \mathbf{22.00\%} \quad (22 / 100)$$
  *Target*: P1 stale fact error rate must be at most half of baseline: $\le \mathbf{11.00\%}$ (at most 11 errors).

- **Gate G-R Hurdle** (Hardware VRAM):
  $$\text{Baseline Process VRAM} = \mathbf{1,416.0\text{ MB}} \le 1,536.0\text{ MB}$$
  *Target*: P1 assistant resident VRAM must remain $\le 1.5\text{ GB}$ (1,536 MB).
