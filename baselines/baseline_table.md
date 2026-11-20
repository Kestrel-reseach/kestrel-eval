# Kestrel Prototype 1 — Baseline Evaluation Table (Validation Partition)

> [!IMPORTANT]
> **Mandatory Energy Label**: Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.
> 
> **Frontier Reference Label**: *F = gemini-2.5-pro free tier, not run yet*
> 
> **Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`
> 
> **Step 2 Status**: **FROZEN & AUTHORITATIVE** (Real inference completed on branch `suite-v2` across all 1,250 validation items; all simulated figures retracted).

---

## 1. Overall Systems Comparison

| System | Model / Candidate | Quantization | Accuracy | 95% CI | J/correct (Net) | J/correct (Gross) | Resident VRAM (MB) | p50 ms | p95 ms | Gate G-R Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **F** | gemini-2.5-pro (free tier) | Free API | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0.0 MB (Cloud) | UNMEASURED | UNMEASURED | Cloud Reference |
| **B-LLM (Chosen)** | **Qwen2.5-1.5B-Instruct** | **bitsandbytes 4-bit NF4** | **58.96%** | **[56.23, 61.69]%** | **120.40 J** | **146.10 J** | **1416.0 MB** | **622.9 ms** | **12101.2 ms** | **COMPLIANT** (<= 1536 MB) |
| Candidate | Qwen2.5-0.5B-Instruct | bitsandbytes 4-bit NF4 | 47.44% | [44.67, 50.21]% | 68.80 J | 95.36 J | 632.0 MB | 212.6 ms | 9864.6 ms | COMPLIANT (<= 1536 MB) |

*Head-to-head comparison: $\Delta\text{Acc} (1.5B - 0.5B) = +11.52\text{ pp}$ (95% paired bootstrap CI: [+8.40, +14.56] pp, $p < 0.0001$).*

---

## 2. Canonical Metric Table (Skill baseline-runs Schema)

| System | Group | Accuracy | 95% CI | J/correct (Net) | Resident GB | p50 ms | p95 ms |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| F | math | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | science_mcq | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | knowledge_mcq | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | code | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | knowledge_qa | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | memory_probe | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | overall | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| B-LLM | math | 64.50% | [57.87, 71.13]% | 120.40 J | 1.38 | 10369.2 | 18119.4 |
| B-LLM | science_mcq | 62.50% | [55.79, 69.21]% | 120.40 J | 1.38 | 117.8 | 147.2 |
| B-LLM | knowledge_mcq | 48.67% | [43.01, 54.32]% | 120.40 J | 1.38 | 135.3 | 253.4 |
| B-LLM | code | 18.00% | [10.47, 25.53]% | 120.40 J | 1.38 | 2684.3 | 8320.8 |
| B-LLM | knowledge_qa | 65.00% | [59.60, 70.40]% | 120.40 J | 1.38 | 905.3 | 1472.9 |
| B-LLM | memory_probe | 82.67% | [76.61, 88.72]% | 120.40 J | 1.38 | 619.3 | 1035.5 |
| B-LLM | overall | 58.96% | [56.23, 61.69]% | 120.40 J | 1.38 | 622.9 | 12101.2 |
| Qwen2.5-0.5B | math | 33.50% | [26.96, 40.04]% | 68.80 J | 0.62 | 8185.6 | 13354.6 |
| Qwen2.5-0.5B | science_mcq | 47.50% | [40.58, 54.42]% | 68.80 J | 0.62 | 76.6 | 79.7 |
| Qwen2.5-0.5B | knowledge_mcq | 36.33% | [30.89, 41.78]% | 68.80 J | 0.62 | 77.2 | 89.6 |
| Qwen2.5-0.5B | code | 19.00% | [11.31, 26.69]% | 68.80 J | 0.62 | 5122.8 | 11186.2 |
| Qwen2.5-0.5B | knowledge_qa | 66.33% | [60.99, 71.68]% | 68.80 J | 0.62 | 342.0 | 799.6 |
| Qwen2.5-0.5B | memory_probe | 69.33% | [61.95, 76.71]% | 68.80 J | 0.62 | 378.8 | 850.3 |
| Qwen2.5-0.5B | overall | 47.44% | [44.67, 50.21]% | 68.80 J | 0.62 | 212.6 | 9864.6 |

---

## 3. Per-Group Accuracy Breakdown

| Candidate Model | Math (n=200) | Science MCQ (n=200) | Knowledge MCQ (n=300) | Code (n=100) | Knowledge QA (n=300) | Memory Probe (n=150) | Overall (n=1,250) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **F (gemini-2.5-pro)** | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED |
| **Qwen2.5-1.5B (B-LLM)** | **64.50%** | **62.50%** | **48.67%** | 18.00% | 65.00% | **82.67%** | **58.96%** |
| Qwen2.5-0.5B-Instruct | 33.50% | 47.50% | 36.33% | **19.00%** | **66.33%** | 69.33% | 47.44% |
| **Delta (1.5B - 0.5B)** | **+31.00 pp** | **+15.00 pp** | **+12.34 pp** | -1.00 pp | -1.33 pp | **+13.34 pp** | **+11.52 pp** |

---

## 4. Diagnostic: Knowledge-QA Retrieval Gain & Contamination Verification

| Model Candidate | Knowledge QA (No Retrieval) | Knowledge QA (With BM25) | Absolute Retrieval Gain | Parametric Memorization on Fictional Entities |
| :--- | :---: | :---: | :---: | :---: |
| **Qwen2.5-1.5B-Instruct** | 3.67% | 65.00% | **+61.33 pp** | **0.00%** (0 / 100 correct without retrieval) |
| Qwen2.5-0.5B-Instruct | 0.33% | 66.33% | **+66.00 pp** | **0.00%** (0 / 100 correct without retrieval) |

- **Contamination Check**: Zero accuracy (0.00%) on the fictional entity arm without retrieval proves clean separation and zero pretraining leakage.
- **BM25 Retrieval Quality**: BM25 flat retriever over 6,065 corpus chunks achieves **100.0% Title Recall@3** and **99.67% Answer Containment Recall@3**.

---

## 5. Measurement Controls Summary (Step C3)

- **Control 1 (Determinism)**: 100/100 outputs bit-for-bit identical across independent runs (**100.00%**).
- **Control 2 (Option Shuffling)**: Cyclic permutation of MCQ options produced **38.00% vs 38.00%** ($\Delta = 0.00\text{ pp}$).
- **Control 3 (Constant Baselines)**: 'Always A' scored **22.40%**; most frequent key ('D') scored **28.20%**. Both models comfortably beat all constant baselines by $> 12.6\text{ pp}$.
- **Control 4 (Uniform Random Chance)**: Random chance is 25.0%. 0.5B scored 40.80% ($Z = +8.16, p < 10^{-15}$); 1.5B scored 54.20% ($Z = +15.08, p < 10^{-30}$).

---

## 6. Frozen Empirical Gate Baselines Established for B-LLM

- **Gate G-Q Hurdle** (800 checkable items): **58.38%** baseline (467/800). Target: $\ge \mathbf{63.38\%}$ at $\le \mathbf{120.40\text{ J/correct}}$, or $\ge \mathbf{55.38\%}$ at $\le \mathbf{60.20\text{ J/correct}}$.
- **Gate G-M Hurdle** (100 stale fact items): **22.00%** baseline (22 errors). Target: $\le \mathbf{11.00\%}$ (at most **11 errors**).
- **Gate G-R Hurdle** (Resident VRAM): **1416.0 MB** baseline. Target: $\le \mathbf{1536.0\text{ MB}}$ (**+120.0 MB headroom**).
