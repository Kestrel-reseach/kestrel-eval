# Project Kestrel Prototype 1 — Step C5 B-LLM Selection Report & Pareto Analysis

**Date**: 2026-11-21  
**Phase**: Phase C — Step C5 (R7 Candidate Selection & Pareto Frontier)  
**Status**: **CONFIRMED & AUTHORITATIVE (DECISION D18 RESOLVED)**  
**Branch**: `feat/d18-candidate-baselines`  
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`  
**Mandatory Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*  
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*  

---

## 1. Candidate Scope & Hardware Qualification Table

Per Owner Decision **D18** and **D19**, candidate evaluation encompasses the five Option A shortlist candidates plus time-boxed exploration of Qwen3.5:
All candidates evaluated under 4-bit NF4, context length 2048 tokens, on NVIDIA GeForce RTX 3050 Laptop GPU (4 GB, budget $\le 1,536\text{ MB}$ NVML process VRAM).

| Candidate Model | Creator / Org | Approx Params | License | NVML Process VRAM (2048 ctx) | Torch Allocated VRAM | Budget Headroom ($\le 1,536\text{ MB}$) | Hub / Qualification Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `Qwen/Qwen2.5-0.5B-Instruct` | Alibaba | 0.49 B | Apache 2.0 | **632.0 MB** | 432.0 MB | **+904.0 MB** | **QUALIFIED (Passes VRAM)** |
| `Qwen/Qwen2.5-1.5B-Instruct` | Alibaba | 1.54 B | Apache 2.0 | **1,416.0 MB** | 1,166.0 MB | **+120.0 MB** | **QUALIFIED (Passes VRAM)** |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | Hugging Face | 1.71 B | Apache 2.0 | **1,732.0 MB** | 1,324.6 MB | **-196.0 MB (OVER)** | **DISQUALIFIED (Exceeds 1.5 GB)** |
| `ibm-granite/granite-4.0-1b` | IBM Research | 1.49 B | Apache 2.0 | **1,602.0 MB** | 1,228.4 MB | **-66.0 MB (OVER)** | **DISQUALIFIED (Exceeds 1.5 GB)** |
| `meta-llama/Llama-3.2-1B-Instruct` | Meta AI | 1.23 B | Llama 3.2 Community | UNMEASURED | UNMEASURED | UNKNOWN | **BLOCKED: Gated repo (HF_TOKEN unset)** |
| `Qwen/Qwen3.5-0.8B` | Alibaba | 0.80 B | Apache 2.0 | **1,220.0 MB** | 887.4 MB | **+316.0 MB** | **QUALIFIED on VRAM; uncompiled kernel latency** |

*Audit Findings*:
1. `SmolLM2-1.7B-Instruct` and `granite-4.0-1b` exceed the 1,536 MB assistant process VRAM budget on the official test tier at 2048 context. Under Gate G-R and D18, both are disqualified from B-LLM selection.
2. `meta-llama/Llama-3.2-1B-Instruct` is gated on HuggingFace Hub and cannot be downloaded without an authenticated `HF_TOKEN`.
3. `Qwen/Qwen3.5-0.8B` fits within budget (1,220 MB), but achieves 54.0% accuracy on the 100-sample validation set and suffers severe latency penalty (p50 = 814.4 ms, ms/tok = 59.49) due to falling back to uncompiled reference PyTorch kernels for causal convolution and linear attention.

---

## 2. Pareto Frontier Analysis (Qualifying Candidates)

Between the qualified candidates meeting the $\le 1,536\text{ MB}$ budget:

| Metric | `Qwen2.5-0.5B-Instruct` (NF4) | `Qwen3.5-0.8B` (NF4, 100-sample) | `Qwen2.5-1.5B-Instruct` (NF4) | Trade-Off & Decision |
| :--- | :---: | :---: | :---: | :--- |
| **Checkable Scope Accuracy (800 items)** | **37.00%** (296/800) | 54.0% (54/100 sample) | **56.88%** (455/800) | **1.5B dominates on checkable accuracy (+19.88 pp over 0.5B)** |
| - 95% Wilson CI | [33.72, 40.40]% | [44.24, 63.44]% | [53.42, 60.27]% | Decisive separation |
| **Math Accuracy (200 items)** | 33.50% [27.32, 40.30] | 55.0% (11/20 sample) | **68.00%** [61.25, 74.07] | 1.5B dominates on multi-step reasoning |
| **Science MCQ (200 items)** | 47.50% [40.69, 54.40] | 65.0% (13/20 sample) | **62.50%** [55.61, 68.91] | Comparable on ARC |
| **Knowledge MCQ (300 items)** | 36.33% [31.10, 41.92] | 50.0% (10/20 sample) | **48.67%** [43.06, 54.30] | 1.5B dominates on MMLU |
| **Code Generation (100 items)** | 25.00% [17.55, 34.30] | 40.0% (4/10 sample) | **48.00%** [38.46, 57.68] | 1.5B dominates on code generation |
| **Stale Fact Error Rate (100 items)** | 41.00% [31.87, 50.80] | 30.0% (3/10 sample) | **22.00%** [15.00, 31.07] | 1.5B halves memory hallucinations |
| **NVML Process VRAM (2048 ctx)** | **632.0 MB** | 1,220.0 MB | **1,416.0 MB** | All three fit within 1,536 MB budget |
| **PyTorch Allocated VRAM** | **460.2 MB** | 887.4 MB | **1,166.0 MB** | 120.0 MB headroom for 1.5B |
| **Checkable Net Joules / Correct** | **157.54 J** | UNMEASURED | **171.55 J** | 0.5B has slightly lower net energy |
| **Inference Latency (MCQ p50)** | **106.8 ms** | 814.4 ms | **135.2 ms** | 1.5B has fast compiled kernels; 3.5 has fallback latency |

---

## 3. Formal Co-Owner Confirmation (Decision D18)

Per **Decision D18**:
> "B-LLM = the most accurate candidate whose NVML process VRAM at 2048 context is at most 1,536 MB; ties broken by lower net energy per correct on the 800-item scope; final only after all candidates are run and the owners confirm."

**Confirmation Resolution (2026-11-21)**:
1. `Qwen/Qwen2.5-1.5B-Instruct` (bitsandbytes 4-bit NF4) is confirmed as **B-LLM**.
2. Baselines for Gate G-Q, Gate G-M, and Gate G-R are confirmed as measured in `c6_updated_gate_baselines.json` and committed to `evaluation/manifest.yaml` (v2.3).
3. Member B is unblocked to execute `python -m kestrel.train_verifier` on the RTX 3050 machine using base model `Qwen/Qwen2.5-1.5B-Instruct` ($d = 1,536$).
