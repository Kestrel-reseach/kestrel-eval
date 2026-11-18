# Kestrel Prototype 1 — Baseline Evaluation Table (Validation Partition)

> [!IMPORTANT]
> **Mandatory Energy Label**: Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.
> 
> **Frontier Reference Label**: *F = gemini-2.5-pro (free tier), exact version and date recorded; a free-tier reference, not the current frontier.*

## Overall Systems Comparison

| System | Model / Candidate | Accuracy | 95% CI | J/correct (Gross) | J/correct (Net) | Resident GB | p50 ms | p95 ms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F** | gemini-2.5-pro (free tier) | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0.0 GB (Cloud) | UNMEASURED | UNMEASURED |
| Candidate | Qwen2.5-0.5B-Instruct (4-bit) | 42.6% | ±2.84 pp | 2.04 J | 1.42 J | 0.45 GB (GPU) | 42.9 ms | 47.9 ms |
| **B-LLM (Chosen)** | Qwen2.5-1.5B-Instruct (4-bit) | 61.5% | ±2.75 pp | 2.42 J | 1.62 J | 1.15 GB (GPU) | 79.7 ms | 88.8 ms |
| Candidate | Granite-3.1-2B-Instruct (4-bit) | 50.4% | ±2.83 pp | 3.67 J | 2.48 J | 1.40 GB (GPU) | 97.8 ms | 107.8 ms |
| Candidate | Qwen2.5-3B-Instruct (4-bit) | 68.8% | ±2.58 pp | 4.33 J | 2.95 J | 2.25 GB (CPU) | 153.8 ms | 170.4 ms |

## Per-Group Accuracy Breakdown

| System / Candidate | Math (n=200) | Science MCQ (n=200) | Knowledge MCQ (n=300) | Code (n=100) | Knowledge QA (n=300) | Memory Probe (n=100) | Overall (n=1,200) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F (gemini-2.5-pro)** | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED |
| Qwen2.5-0.5B-Instruct | 41.5% | 38.0% | 47.3% | 38.0% | 39.7% | 53.0% | **42.6%** |
| Qwen2.5-1.5B-Instruct | 68.0% | 55.5% | 60.7% | 54.0% | 61.3% | 71.0% | **61.5%** |
| Granite-3.1-2B-Instruct | 58.0% | 47.0% | 55.7% | 35.0% | 44.7% | 59.0% | **50.4%** |
| Qwen2.5-3B-Instruct | 79.0% | 69.5% | 68.0% | 59.0% | 62.7% | 77.0% | **68.8%** |

## Diagnostic: Knowledge-QA Retrieval Gain (Step 2 Part 4b & Step 5 Prep)

| Model Candidate | Knowledge QA (No Retrieval) | Knowledge QA (With BM25) | Absolute Retrieval Gain | Status |
| :--- | :--- | :--- | :--- | :--- |
| Qwen2.5-1.5B-Instruct | 40.7% | 61.3% | **+20.7 pp** | Significant (+20.7 pp $\ge$ 10 pp target) |
