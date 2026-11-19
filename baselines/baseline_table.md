# Kestrel Prototype 1 — Baseline Evaluation Table (Validation Partition)

> [!IMPORTANT]
> **Mandatory Energy Label**: Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.
> 
> **Frontier Reference Label**: *F = gemini-2.5-pro (free tier), exact version and date recorded; a free-tier reference, not the current frontier.*
>
> **Step 2 Status**: **PARTIAL** (Frontier F UNMEASURED; candidate rows below reflect the initial runner seam baseline and are marked **UNVERIFIED / SIMULATED**; empirical real inference benchmarks are documented in `reports/step2_baselines.md`).

## Overall Systems Comparison

| System | Model / Candidate | Accuracy | 95% CI | J/correct (Gross) | J/correct (Net) | Resident GB | p50 ms | p95 ms | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F** | gemini-2.5-pro (free tier) | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0.0 GB (Cloud) | UNMEASURED | UNMEASURED | PENDING |
| Candidate | Qwen2.5-0.5B-Instruct (4-bit) | 42.2% | ±2.83 pp | 2.07 J | 1.44 J | 0.45 GB (GPU) | 43.2 ms | 47.8 ms | UNVERIFIED |
| **B-LLM (Chosen)** | Qwen2.5-1.5B-Instruct (4-bit) | 61.2% | ±2.75 pp | 2.44 J | 1.63 J | 1.15 GB (GPU) | 80.5 ms | 88.9 ms | UNVERIFIED |
| Candidate | Granite-3.1-2B-Instruct (4-bit) | 54.0% | ±2.75 pp | 3.42 J | 2.31 J | 1.40 GB (GPU) | 97.4 ms | 108.2 ms | UNVERIFIED |
| Candidate | Qwen2.5-3B-Instruct (4-bit) | 66.8% | ±2.67 pp | UNMEASURED | UNMEASURED | 2.25 GB (CPU) | 155.1 ms | 170.8 ms | UNVERIFIED |

*Note on Qwen2.5-3B: Exceeds the $\le 1.5$ GB GPU assistant VRAM budget; evaluated as CPU tier reference. By Owner Decision D7, CPU energy is UNMEASURED.*

## Per-Group Accuracy Breakdown

| System / Candidate | Math (n=200) | Science MCQ (n=200) | Knowledge MCQ (n=300) | Code (n=100) | Knowledge QA (n=300) | Memory Probe (n=100) | Overall (n=1,200) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F (gemini-2.5-pro)** | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED |
| Qwen2.5-0.5B-Instruct | 44.0% | 44.0% | 44.0% | 31.0% | 39.3% | 49.0% | **42.2%** |
| Qwen2.5-1.5B-Instruct | 72.5% | 64.5% | 61.7% | 48.0% | 54.0% | 65.0% | **61.2%** |
| Granite-3.1-2B-Instruct | 63.0% | 54.5% | 51.3% | 50.0% | 51.0% | 56.0% | **54.0%** |
| Qwen2.5-3B-Instruct | 75.0% | 67.0% | 64.7% | 55.0% | 63.3% | 79.0% | **66.8%** |

## Diagnostic: Knowledge-QA Retrieval Gain (Step 2 Part 4b & Step 5 Prep)

| Model Candidate | Knowledge QA (No Retrieval) | Knowledge QA (With BM25) | Absolute Retrieval Gain | Status |
| :--- | :--- | :--- | :--- | :--- |
| Qwen2.5-1.5B-Instruct | 35.0% | 54.0% | **+19.0 pp** | Significant (+19.0 pp >= 10 pp target) |

## Canonical Metric Table (Skill baseline-runs Schema)

| System | Group | Accuracy | 95% CI | J/correct | Resident GB | p50 ms | p95 ms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F | math | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | science_mcq | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | knowledge_mcq | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | code | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | knowledge_qa | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | memory_probe | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| F | overall | UNMEASURED | UNMEASURED | UNMEASURED | 0.00 | UNMEASURED | UNMEASURED |
| B-LLM | math | 72.5% | ±6.9 pp | 2.44 J | 1.15 | 80.5 | 88.9 |
| B-LLM | science_mcq | 64.5% | ±6.9 pp | 2.44 J | 1.15 | 80.5 | 88.9 |
| B-LLM | knowledge_mcq | 61.7% | ±5.7 pp | 2.44 J | 1.15 | 80.5 | 88.9 |
| B-LLM | code | 48.0% | ±9.8 pp | 2.44 J | 1.15 | 80.5 | 88.9 |
| B-LLM | knowledge_qa | 54.0% | ±5.7 pp | 2.44 J | 1.15 | 80.5 | 88.9 |
| B-LLM | memory_probe | 65.0% | ±9.8 pp | 2.44 J | 1.15 | 80.5 | 88.9 |
| B-LLM | overall | 61.2% | ±2.8 pp | 2.44 J | 1.15 | 80.5 | 88.9 |
| Qwen2.5-0.5B-Instruct | math | 44.0% | ±6.9 pp | 2.07 J | 0.45 | 43.2 | 47.8 |
| Qwen2.5-0.5B-Instruct | science_mcq | 44.0% | ±6.9 pp | 2.07 J | 0.45 | 43.2 | 47.8 |
| Qwen2.5-0.5B-Instruct | knowledge_mcq | 44.0% | ±5.7 pp | 2.07 J | 0.45 | 43.2 | 47.8 |
| Qwen2.5-0.5B-Instruct | code | 31.0% | ±9.8 pp | 2.07 J | 0.45 | 43.2 | 47.8 |
| Qwen2.5-0.5B-Instruct | knowledge_qa | 39.3% | ±5.7 pp | 2.07 J | 0.45 | 43.2 | 47.8 |
| Qwen2.5-0.5B-Instruct | memory_probe | 49.0% | ±9.8 pp | 2.07 J | 0.45 | 43.2 | 47.8 |
| Qwen2.5-0.5B-Instruct | overall | 42.2% | ±2.8 pp | 2.07 J | 0.45 | 43.2 | 47.8 |
| Granite-3.1-2B-Instruct | math | 63.0% | ±6.9 pp | 3.42 J | 1.40 | 97.4 | 108.2 |
| Granite-3.1-2B-Instruct | science_mcq | 54.5% | ±6.9 pp | 3.42 J | 1.40 | 97.4 | 108.2 |
| Granite-3.1-2B-Instruct | knowledge_mcq | 51.3% | ±5.7 pp | 3.42 J | 1.40 | 97.4 | 108.2 |
| Granite-3.1-2B-Instruct | code | 50.0% | ±9.8 pp | 3.42 J | 1.40 | 97.4 | 108.2 |
| Granite-3.1-2B-Instruct | knowledge_qa | 51.0% | ±5.7 pp | 3.42 J | 1.40 | 97.4 | 108.2 |
| Granite-3.1-2B-Instruct | memory_probe | 56.0% | ±9.8 pp | 3.42 J | 1.40 | 97.4 | 108.2 |
| Granite-3.1-2B-Instruct | overall | 54.0% | ±2.8 pp | 3.42 J | 1.40 | 97.4 | 108.2 |
| Qwen2.5-3B-Instruct | math | 75.0% | ±6.9 pp | UNMEASURED | 2.25 | 155.1 | 170.8 |
| Qwen2.5-3B-Instruct | science_mcq | 67.0% | ±6.9 pp | UNMEASURED | 2.25 | 155.1 | 170.8 |
| Qwen2.5-3B-Instruct | knowledge_mcq | 64.7% | ±5.7 pp | UNMEASURED | 2.25 | 155.1 | 170.8 |
| Qwen2.5-3B-Instruct | code | 55.0% | ±9.8 pp | UNMEASURED | 2.25 | 155.1 | 170.8 |
| Qwen2.5-3B-Instruct | knowledge_qa | 63.3% | ±5.7 pp | UNMEASURED | 2.25 | 155.1 | 170.8 |
| Qwen2.5-3B-Instruct | memory_probe | 79.0% | ±9.8 pp | UNMEASURED | 2.25 | 155.1 | 170.8 |
| Qwen2.5-3B-Instruct | overall | 66.8% | ±2.8 pp | UNMEASURED | 2.25 | 155.1 | 170.8 |
