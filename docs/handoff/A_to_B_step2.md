# Project Kestrel Prototype 1 — Step 2 to Step 3 Handoff Specification

**From**: Member A (Evaluation, Measurement & Memory Lead)  
**To**: Member B (Core Reasoning & Integration Lead)  
**Date**: 2026-11-20  
**Status**: STEP 2 PARTIAL (Candidate evaluation in progress under Owner Decisions D18–D20; F deferred)  
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`  
**Mandatory Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*  
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*  

---

## 1. Executive Summary & Audit Context

This document is the official handoff package from Member A to Member B for transitioning from Step 2 to Step 3 (Verifier Head Training & Calibration).

### Key Reconciliations (Step 2 Correction Pass):
1. **Train Partition Size**: Exactly **800 checkable labeled train items** (200 math, 200 science MCQ, 300 knowledge MCQ, 100 code).  
   *(Correction Note: An earlier summary inadvertently claimed 2,400 checkable train items by multiplying by 3 partitions; the actual train partition contains 800 checkable items and 1,250 total items).*
2. **Retrieval Corpus Composition**: Total **6,065 documents** indexed in flat BM25:
   - English Wikipedia Abstracts: `data/wikipedia_abstracts_5k.jsonl` (**6,000 documents**, SHA-256 `cbded097e866a71bb74ff5d093bb14081bf2d809dabf1be08a2cdc5c78792f00`).
   - Fictional Abstracts: `data/fictional_abstracts_corpus.jsonl` (**65 documents**, SHA-256 `001c64c3899be55b2a5669c14cfcd88cc66614fc6a68bc2846981e01e23c080b`).
3. **Owner Decisions (D18–D20)**:
   - **D18**: B-LLM selection criterion is the most accurate candidate whose NVML process VRAM at 2048 context is $\le 1,536\text{ MB}$; ties broken by lower net energy per correct on the 800-item scope; final only after all candidates are run and confirmed by owners.
   - **D19**: Option A candidates (five) stand; plus time-boxed exploration of Qwen3.5-0.8B.
   - **D20**: F: free tier (Google AI Studio, $0 cap, paced across days; paid tier pending confirmation).
4. **Frontier Model F**: Zero calls made during this pass. Prepared prompt templates and pacing schedule in `evaluation/f_templates.py`. Execution deferred until explicit owner instruction.

---

## 2. Checkable Train Partition Assets for Member B

Member B will use the labeled train partition for training and calibrating the verifier head:

| Group | Split / File Path | Items | Verification Target | Format / Check |
| :--- | :--- | :---: | :--- | :--- |
| **Math** | `suite/train/math.jsonl` | 200 | Numerical solution | `exact_numeric` |
| **Science MCQ** | `suite/train/science_mcq.jsonl` | 200 | Option letter A–E | `answer_key` |
| **Knowledge MCQ** | `suite/train/knowledge_mcq.jsonl` | 300 | Option letter A–D | `answer_key` |
| **Code** | `suite/train/code.jsonl` | 100 | Python function + unit tests | `unit_tests_pass` |
| **Checkable Total** | *(Above 4 groups)* | **800** | Labeled training pairs | Verified clean |
| **Knowledge QA** | `suite/train/knowledge_qa.jsonl` | 300 | Entity span match | `normalized_exact_match` |
| **Memory Probe** | `suite/train/memory_probe.jsonl` | 150 | Recent fact log | `key_from_source_history` |
| **Full Train Split** | *(All 6 groups)* | **1,250** | Full partition size | Manifest v2.2 |

---

## 3. Recommended Base Model (B-LLM Candidate Status)

Pending final co-owner confirmation across all candidates:
- **Leading Candidate**: `Qwen/Qwen2.5-1.5B-Instruct` in `bitsandbytes` 4-bit NF4.
- **VRAM Profile at 2048 Context**: **1,416.0 MB** NVML process memory ($\le 1,536\text{ MB}$ budget, 120.0 MB headroom).
- **Hidden State Dimension ($d$)**: **1,536**.
- **Decoder Layers**: 28 transformer blocks.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model_name = "Qwen/Qwen2.5-1.5B-Instruct"
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnb_config, device_map="cuda:0")

# Hidden-state hook for Verifier Head (d = 1536)
inputs = tokenizer("Problem statement...", return_tensors="pt").to("cuda:0")
with torch.no_grad():
    outputs = model(**inputs, output_hidden_states=True)
    last_hidden_state = outputs.hidden_states[-1] # shape: [batch, seq_len, 1536]
```

---

## 4. Run Index & Evidence Artifacts

- **Run Index**: `reports/step2/run_index.md`
- **Saved Validation Predictions**:
  - `reports/step2/run_qwen2.5-0.5b-instruct-q4_validation.jsonl` (1,250 records)
  - `reports/step2/run_qwen2.5-1.5b-instruct-q4_validation.jsonl` (1,250 records)
- **Scoring Specification**: `docs/decisions/scoring_spec.md` (v2.2, Deviations Dev-01 & Dev-02)
- **Audit Reports**:
  - `reports/step2/c4_retrieval_ablation_report.md` (reconciled 6,065 docs)
  - `reports/step2/c8_definition_of_done_audit.md`

