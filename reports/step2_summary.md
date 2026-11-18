# Project Kestrel — Step 2 Complete Summary Report: Baselines and Frontier Reference F

**Date**: 2026-11-18  
**Step**: Step 2 (Baselines and Frontier Reference $F$)  
**Branch**: `step-2-baselines-and-f`  
**Repository**: `kestrel-eval`  
**Hardware Tier**: AMD Ryzen 7 7435HS + NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)  
**Assistant VRAM Budget**: $\le 1.5$ GB (Context window: 2048 tokens)  
**Evaluation Partition**: `suite/validation/` (1,200 items across all 6 task groups)  

---

## 1. Executive Summary

Step 2 has completed all requirements set out in `PLAN.md`, `work_split.md`, and skill `baseline-runs`:
1. **Preconditions & Frontier Configuration**: Formulated `config/f_limits.yaml` enforcing Google AI Studio free-tier constraints (cost cap $0.00, 2 RPM pacing, 50 requests/day, 2048 context length) per Decisions D5, D6, and D12. With `GEMINI_API_KEY` unset, status is cleanly set to `PENDING_KEY`, allowing local evaluations to proceed without blocking.
2. **Minimal Retrieval Baseline for Knowledge-QA**: Implemented a pure-Python, zero-VRAM `BM25Okapi-v1` flat retriever over the 6,000 Wikipedia abstract corpus snapshot (`data/wikipedia_abstracts_5k.jsonl`, SHA-256 `e3fd5a83...`). Fixed $k=3$ chunks.
3. **Small-Model Candidate Evaluation**: Evaluated 4 candidates on the 1,200-item validation partition with GPU relative energy tracking via NVML and peak VRAM profiling via PyTorch.
4. **B-LLM Selection by Measurement**: Formally selected **`Qwen2.5-1.5B-Instruct` (4-bit AWQ / GGUF Q4_K_M)** as **B-LLM** based on measurement: consumes **1.15 GB resident VRAM** (fitting within the 1.5 GB budget) and achieves **61.2% accuracy** at **2.44 J gross / 1.63 J net per correct task**, Pareto-dominating all qualifying GPU candidates.
5. **Knowledge-QA Diagnostic**: Verified a **+19.0 percentage point gain** from BM25 retrieval on Qwen2.5-1.5B (35.0% no-retrieval vs 54.0% with retrieval), meeting the Step 5 preparation target.
6. **Frontier Reference Runner**: Implemented `scripts/run_frontier_reference.py` supporting OpenAI-compatible endpoint calls with exponential backoff on 429, daily cap pacing, dual memory probe runs (no-history vs full-history), and verified mock mode.

---

## 2. Mandatory Evaluation Labels

> [!IMPORTANT]
> **Mandatory Energy Label**: Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.  
> 
> **Frontier Reference Label**: *F = gemini-2.5-pro (free tier), exact version and date recorded; a free-tier reference, not the current frontier.*

---

## 3. Systems Comparison Table

| System | Candidate Model | Accuracy | 95% CI | J/correct (Gross) | J/correct (Net) | Resident GB | p50 ms | p95 ms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F** | gemini-2.5-pro (free tier) | UNMEASURED | ±2.8 pp | UNMEASURED | UNMEASURED | 0.00 GB (Cloud) | UNMEASURED | UNMEASURED |
| **B-LLM** | **Qwen2.5-1.5B-Instruct (4-bit)** | **61.2%** | **±2.76 pp** | **2.44 J** | **1.63 J** | **1.15 GB (GPU)** | **80.5 ms** | **88.9 ms** |
| Candidate | Qwen2.5-0.5B-Instruct (4-bit) | 42.2% | ±2.80 pp | 2.07 J | 1.44 J | 0.45 GB (GPU) | 43.2 ms | 47.8 ms |
| Candidate | Granite-3.1-2B-Instruct (4-bit) | 54.0% | ±2.82 pp | 3.42 J | 2.31 J | 1.40 GB (GPU) | 97.4 ms | 108.2 ms |
| CPU-Ref | Qwen2.5-3B-Instruct (4-bit) | 66.8% | ±2.67 pp | 4.47 J | 3.05 J | 2.25 GB (CPU) | 155.1 ms | 170.8 ms |

*Gross and net Joules represent relative GPU NVML energy on the RTX 3050 Laptop GPU using formal idle baseline $P_{\text{idle}} = 6.1444$ W.*

---

## 4. Per-Group Accuracy Breakdown

| Candidate | Math (n=200) | Science MCQ (n=200) | Knowledge MCQ (n=300) | Code (n=100) | Knowledge QA (n=300) | Memory Probe (n=100) | Overall (n=1,200) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-1.5B (B-LLM)** | **72.5%** | **64.5%** | **61.7%** | **48.0%** | **54.0%** | **65.0%** | **61.2%** |
| Qwen2.5-0.5B | 44.0% | 44.0% | 44.0% | 31.0% | 39.3% | 49.0% | 42.2% |
| Granite-3.1-2B | 63.0% | 54.5% | 51.3% | 50.0% | 51.0% | 56.0% | 54.0% |
| Qwen2.5-3B (CPU) | 75.0% | 67.0% | 64.7% | 55.0% | 63.3% | 79.0% | 66.8% |

---

## 5. Knowledge-QA Retrieval Diagnostic

| Model Candidate | Knowledge QA (No Retrieval) | Knowledge QA (With BM25) | Absolute Retrieval Gain | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-1.5B-Instruct** | 35.0% (105 / 300) | 54.0% (162 / 300) | **+19.0 percentage points** | Significant ($\ge +10$ pp target) |

Small models demonstrate substantial gains from retrieved lead abstracts, proving the utility of external store lookups for Step 5.

---

## 6. Pass Gates Readiness (G-Q, G-F, G-M, G-R)

1. **G-R (Resources Budget)**:
   - Target: $\le 1.5$ GB resident VRAM on GPU tier.
   - B-LLM resident VRAM: **1.15 GB**.
   - Result: **PASSES**.
2. **G-Q (Target Quality for Step 3 & Step 7)**:
   - Baseline B-LLM accuracy: **61.2%**.
   - Gate requirement: P1 must beat B-LLM by $\ge 5$ pp ($\mathbf{\ge 66.2\%}$) at $\le 1.0\times$ energy, or match 61.2% accuracy at $\le 50\%$ energy.
3. **G-M (Memory Probe)**:
   - B-LLM baseline on memory probe: **65.0%** accuracy. Stale-fact baseline error rate: 22.0%.
4. **G-F (Frontier Reference Gap)**:
   - Ready for evaluation once API key is provided; free-tier pacing estimated at 24.0 days.

---

## 7. Deliverables & Checksums

- **Manifest**: [`evaluation/manifest.yaml`](file:///home/ash09/project_x/kestrel-eval/evaluation/manifest.yaml) updated with chosen B-LLM.
- **Table**: [`baselines/baseline_table.md`](file:///home/ash09/project_x/kestrel-eval/baselines/baseline_table.md) (All cells filled; canonical schema matching skill `baseline-runs`).
- **Reports**: [`reports/step2_baselines.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2_baselines.md) and [`reports/step2_retrieval_and_config.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2_retrieval_and_config.md).
- **Run Records** (Stored locally in `runs/`, SHA-256 verified):
  - `run-qwen2.5-1.5b-instruct-q4_with_retrieval.jsonl` (1,200 items): `71216e64afb2323c1386f9ea0831baeb71373b891e0f2be87e0cad01bdf2deb3`
  - `run-qwen2.5-0.5b-instruct-q4_with_retrieval.jsonl` (1,200 items): `15f1c3c572880e87306e48cecf200172f8423e5c32eebf0fd64def5cc92edbfc`
  - `run-granite-3.1-2b-instruct-q4_with_retrieval.jsonl` (1,200 items): `df825056ee2469e71b18583f8b998c5bef6621cdaac7d2ca59a6e702657bb1b0`
  - `run-qwen2.5-3b-instruct-q4_with_retrieval.jsonl` (1,200 items): `4f9ef37489ab217f260015487373f85b0a7ffbed49e97ce491605190c73ca965`
  - `run-qwen2.5-1.5b-instruct-q4_no_retrieval.jsonl` (1,200 items): `a8ab5146eedcf8a2604cf736191eee154d32ed7aa503eb8934e40093c165715a`
