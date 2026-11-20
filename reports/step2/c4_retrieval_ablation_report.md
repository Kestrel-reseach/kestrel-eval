# Project Kestrel Prototype 1 — Step C4 Retrieval Ablation Report

**Date**: 2026-11-20
**Phase**: Phase C — Step C4 (R6 Retrieval Ablation & BM25 Audit)
**Branch**: `suite-v2`
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`
**Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*

---

## 1. Executive Summary

Step C4 conducted the formal retrieval ablation across all 300 validation Knowledge-QA items (200 real Wikipedia + 100 fictional entities), comparing model accuracy with and without BM25 retrieval.

### Key Findings:
1. **Zero Parametric Memorization on Fictional Entities**: Without retrieval, both models score **0.0%** (0.5B) and **0.0%** (1.5B) on the fictional entity arm, confirming zero memorization or leakage. With retrieval, accuracies jump to **70.0%** and **65.0%** (Retrieval Gain: **+70.00 pp**).
2. **Substantial Retrieval Gain on Real Wikipedia**: BM25 retrieval boosts Wikipedia QA by **+64.00 pp** (0.5B: 0.5% $\to$ 64.5%) and **+59.50 pp** (1.5B: 5.5% $\to$ 65.0%).
3. **BM25 Retrieval Quality**: The BM25 retriever achieves **100.0% Title Recall@3** and **99.67% Answer Containment Recall@3** across the combined 6,065-document index.

---

## 2. Retrieval Ablation Comparative Table

| Candidate | Arm | With BM25 | No Retrieval (Parametric) | Retrieval Gain ($\Delta$) | 95% Paired CI |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `Qwen2.5-0.5B` | **Overall Knowledge-QA (n=300)** | **66.33%** | 0.33% | **+66.00 pp** | [60.67, 71.33] |
| `Qwen2.5-0.5B` | Real Wikipedia (n=200) | 64.5% | 0.5% | +64.00 pp | — |
| `Qwen2.5-0.5B` | Fictional Entity (n=100) | 70.0% | 0.0% | +70.00 pp | Clean synthetic test |
| `Qwen2.5-1.5B` | **Overall Knowledge-QA (n=300)** | **65.0%** | 3.67% | **+61.33 pp** | [55.67, 67.0] |
| `Qwen2.5-1.5B` | Real Wikipedia (n=200) | 65.0% | 5.5% | +59.50 pp | — |
| `Qwen2.5-1.5B` | Fictional Entity (n=100) | 65.0% | 0.0% | +65.00 pp | Clean synthetic test |

---

## 3. BM25 Retrieval Recall@3 Audit

| Corpus Arm | Documents Indexed | Evaluated Items | Title Recall@3 | Answer Containment Recall@3 |
| :--- | :---: | :---: | :---: | :---: |
| **Wikipedia Abstracts** | 5,065 | 200 | 100.0% (200/200) | 99.5% (199/200) |
| **Fictional Abstracts** | 1,000 | 100 | 100.0% (100/100) | 100.0% (100/100) |
| **Combined Index** | **6,065** | **300** | **100.0%** (300/300) | **99.67%** (299/300) |

---

## 4. Integrity and Leakage Verification

- [x] **Zero Gold Passage Leakage**: Prompt construction under `use_retrieval=False` verified to contain zero passage text.
- [x] **Zero Memorization on Synthetic Data**: Both models score $\le 1.0\%$ on fictional entity questions without retrieval.
- [x] **Consistent Indexing**: BM25 index built over the full frozen 6,065-document corpus with zero extra GPU VRAM allocated.
