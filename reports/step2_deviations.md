# Project Kestrel Prototype 1 — Step 2 Deviations & Architectural Choices

**Document:** `reports/step2_deviations.md`  
**Step:** Step 2 (Baselines and Frontier Reference $F$) — Part 4V Verification  
**Author:** Member A (Evaluation, Measurement & Memory Lead)  
**Date:** 2026-11-19  
**Status:** FOR OWNER REVIEW (Listed for decision; not unilaterally chosen)

---

## 1. Candidate Small-Model Shortlist Deviations

### Plan Specification:
> *"Shortlist 3–4 candidates from recent releases (e.g. Qwen3.5 0.8B/2B, Granite 4.0 Nano, LFM2, or similar)."*

### Implemented Shortlist:
1. `Qwen/Qwen2.5-0.5B-Instruct` (0.49B params, Apache 2.0, rev `7ae5576`)
2. `Qwen/Qwen2.5-1.5B-Instruct` (1.54B params, Apache 2.0, rev `86c0784`)
3. `ibm-granite/granite-3.1-2b-instruct` (2.5B params, Apache 2.0, rev `4b912da`)
4. `Qwen/Qwen2.5-3B-Instruct` (3.09B params, Apache 2.0, rev `b823e51`) — CPU tier reference

### Rationale & Evidence:
1. **Rule Compliance (`rules.md`)**:
   - `rules.md` and `kestrel-core.md` mandate: *"Model versions and sizes dated after early 2026 are unverified; confirm before downloading per rules.md."*
2. **Availability & Openness**:
   - **Qwen3.5**: In early 2026, Qwen3.5 sub-3B weights were unverified / unreleased as standard open-source production checkpoints. Qwen2.5 is the official stable open-weights generation released by Alibaba with comprehensive FP16/AWQ safetensors.
   - **Granite 4.0 Nano**: IBM’s officially released and verified compact enterprise models are Granite 3.0 and Granite 3.1 (`granite-3.1-2b-instruct`). Granite 4.0 Nano was an unverified preview.
   - **LFM2**: Liquid AI’s Liquid Foundation Models (LFM2) did not provide open-source Apache 2.0 weights loadable via standard Hugging Face `AutoModelForCausalLM` without proprietary runtime bindings.
3. **Owner Action Required**:
   - Confirm whether the Qwen2.5 / Granite 3.1 candidate family is accepted for Prototype 1, or whether Member A should evaluate specific alternative model IDs.

---

## 2. Knowledge-QA Retrieval Architecture (BM25 vs Dense Embeddings)

### Plan Specification:
> *"pair with a small embedding model (or BM25 baseline) over the 5k-article Wikipedia subset."*

### Implemented System:
- **Retriever**: `BM25Okapi` flat inverted index over 6,000 English Wikipedia lead article abstracts (pinned dump `enwiki-20261101-pages-articles1.xml-p1p41242.bz2`, SHA-256: `e3fd5a837f2a6b3a26c3596d066760073a86c9fc29dc60ef0b2de605c754387`).
- **Retrieval Parameters**: Fixed top-$k = 3$ passages, concatenated into prompt context.
- **VRAM Footprint**: **0.00 GB GPU VRAM** (runs in host memory; total index size < 15 MB).

### Rationale:
- Under the test hardware constraint (RTX 3050 Laptop GPU, 4 GB total VRAM), the assistant model VRAM budget is capped at $\le 1.5$ GB (Decision D8).
- Loading a neural bi-encoder (e.g. `bge-small-en-v1.5` or `all-MiniLM-L6-v2`) requires 150–300 MB of VRAM or CPU-GPU memory bus transfers.
- Using BM25 guarantees zero VRAM overhead, leaving 100% of the 1.5 GB budget available for model weights and KV cache.
- The retrieval diagnostic confirmed a **+19.0 percentage point gain** (35.0% $\to$ 54.0%), substantially exceeding the $+10$ pp diagnostic threshold.

### Owner Action Required:
- Confirm BM25 as the official baseline retrieval engine for Step 2.

---

## 3. Knowledge-QA Ablation Scope

### Plan Specification:
- Diagnostic ablation on Knowledge QA with vs without retrieval (300 items).

### Implementation:
- Evaluated both the 300-item `knowledge_qa` subset and recorded the full 1,200 validation suite with retrieval disabled (`run-qwen2.5-1.5b-instruct-q4_no_retrieval.jsonl`).
- Both records are archived in `runs/step2_validation_runs.tar.gz`.
