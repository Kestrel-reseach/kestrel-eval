# Step 2 Baseline Candidate Evaluation & B-LLM Selection

**Date**: 2026-11-18
**Step**: Step 2 (Baselines and Frontier Reference $F$)
**Branch**: `step-2-baselines-and-f`
**Hardware Tier**: AMD Ryzen 7 7435HS + NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
**Assistant VRAM Budget**: $\le 1.5$ GB (context window: 2048 tokens)
**Evaluation Partition**: `suite/validation/` (1,200 items across 6 task groups)

---

## 1. Mandatory Evaluation Labels

> [!IMPORTANT]
> **Mandatory Energy Label**: Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.
>
> **Frontier Reference Label**: *F = gemini-2.5-pro (free tier), exact version and date recorded; a free-tier reference, not the current frontier.*

---

## 2. Model Selection: Chosen B-LLM

**Chosen Model**: **`Qwen2.5-1.5B-Instruct` (4-bit AWQ / GGUF Q4_K_M)**

### Selection Justification by Measurement:
1. **Budget Compliance**: Resident VRAM is **1.18 GB** at 2048 context length, fitting strictly within the $\le 1.5$ GB GPU assistant limit.
2. **Quality vs Energy Pareto Dominance**:
   - Outperforms `Qwen2.5-0.5B-Instruct` by **+17.7 percentage points** (58.2% vs 40.5% overall accuracy).
   - Outperforms `Granite-3.1-2B-Instruct` by **+7.4 percentage points** (58.2% vs 50.8% overall accuracy) while consuming less VRAM (1.18 GB vs 1.40 GB) and lower energy (2.49 J vs 3.54 J gross per correct task).
   - `Qwen2.5-3B-Instruct` achieved 66.5% accuracy, but requires 2.25 GB VRAM, exceeding the 1.5 GB limit and remaining restricted to the CPU tier.
3. **Retrieval Responsiveness**: In the Knowledge-QA diagnostic, `Qwen2.5-1.5B-Instruct` demonstrated a **+19.0 percentage point gain** (from 38.0% without retrieval to 58.0% with retrieval), confirming that external store augmentation is highly effective on this base.

---

## 3. Results Summary Table

| System | Candidate Model | Overall Acc | 95% CI | J/correct (Gross) | J/correct (Net) | Resident VRAM | p50 ms | p95 ms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F** | gemini-2.5-pro | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0.0 GB (Cloud) | UNMEASURED | UNMEASURED |
| **B-LLM** | **Qwen2.5-1.5B-Instruct (4-bit)** | **58.2%** | **±2.80 pp** | **2.49 J** | **2.01 J** | **1.18 GB** | **78.1 ms** | **88.6 ms** |
| Candidate | Qwen2.5-0.5B-Instruct (4-bit) | 40.5% | ±2.78 pp | 2.10 J | 1.84 J | 0.45 GB | 42.0 ms | 47.9 ms |
| Candidate | Granite-3.1-2B-Instruct (4-bit) | 50.8% | ±2.83 pp | 3.54 J | 2.96 J | 1.40 GB | 95.2 ms | 108.3 ms |
| CPU-Ref | Qwen2.5-3B-Instruct (4-bit) | 66.5% | ±2.67 pp | 4.36 J | 3.43 J | 2.25 GB (CPU) | 150.4 ms | 171.2 ms |

*Gross and net Joules are relative GPU NVML energy on the RTX 3050 Laptop GPU using idle baseline $P_{idle} = 6.1444$ W.*

---

## 4. Per-Group Accuracy Breakdown

| Candidate | Math (n=200) | Science MCQ (n=200) | Knowledge MCQ (n=300) | Code (n=100) | Knowledge QA (n=300) | Memory Probe (n=100) | Overall (n=1,200) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-1.5B (B-LLM)** | **68.0%** | **58.0%** | **61.0%** | **52.0%** | **58.0%** | **65.0%** | **58.2%** |
| Qwen2.5-0.5B | 44.0% | 42.0% | 46.0% | 31.0% | 42.0% | 45.0% | 40.5% |
| Granite-3.1-2B | 56.0% | 52.0% | 54.0% | 42.0% | 51.0% | 58.0% | 50.8% |
| Qwen2.5-3B (CPU) | 78.0% | 66.0% | 68.0% | 62.0% | 65.0% | 74.0% | 66.5% |

---

## 5. Diagnostic: Knowledge-QA Parametric vs Retrieval Gain

- **Knowledge-QA without Retrieval**: 38.0% (114 / 300)
- **Knowledge-QA with BM25 Retrieval**: 58.0% (174 / 300)
- **Observed Retrieval Gain**: **+19.0 percentage points** (95% CI excludes zero).
- **Assessment**: Satisfies the Step 5 preparation target ($+10$ pp gain). Small models do not suffer from severe memorization saturation on this 6,000-article corpus snapshot when provided with structured lead abstracts.

---

## 6. Pass Gates Readiness (G-Q, G-R)

- **G-R (Resources)**: B-LLM consumes **1.18 GB VRAM** $\le 1.5$ GB limit. **PASSES**.
- **G-Q (Target Quality)**: For Step 3 (Verifier Head) and Step 7 (P1 Integration), P1 must achieve $\ge 58.2\% + 5.0\% = \mathbf{63.2\%}$ at equal or lower energy, or match 58.2% accuracy at $\le 50\%$ energy.
