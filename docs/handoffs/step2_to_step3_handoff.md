# Project Kestrel Prototype 1 — Step 2 to Step 3 Handoff Specification

**From**: Member A (Evaluation, Measurement & Memory Lead)  
**To**: Member B (Core Reasoning & Integration Lead)  
**Date**: 2026-11-20  
**Status**: COMPLETE, VERIFIED & FROZEN (Decision D18)  
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`  
**Mandatory Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*  
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*  

---

## 1. Executive Summary

Member A has completed all requirements for **Step 2 (Small-Model Baseline Candidates, Retrieval Baseline, and Gate Baseline Computations)** on the `suite-v2` branch of `kestrel-eval`.

This document specifies the exact model artifacts, representations, baseline predictions, datasets, and target gate hurdles for Member B's upcoming work in **Step 3 (Verifier Head Training & Calibration)**.

---

## 2. Selected Base Model (B-LLM) Specifications

Following empirical measurement across all 1,250 validation items under the frozen scoring specification, **`Qwen/Qwen2.5-1.5B-Instruct`** in **`bitsandbytes` 4-bit NF4** has been formally selected as **B-LLM**.

### Architectural Parameters & Memory Profile:
- **Base Architecture**: `Qwen2ForCausalLM`
- **Total Parameters**: 1.54 Billion (0.49 GB active weights in NF4)
- **Hidden Dimension ($d$)**: **$1,536$**
- **Decoder Layers**: 28 transformer blocks
- **Attention Heads**: 12 query heads, 2 key/value heads (Grouped Query Attention)
- **Vocabulary Size**: 151,936 tokens
- **Context Length**: 2,048 tokens
- **Resident VRAM Footprint**: **1,416.0 MB** process memory (NVML) / 1,166.0 MB allocated (PyTorch) at context length 2048 (well within the $\le 1,536.0\text{ MB}$ Gate G-R budget).

### Standard Loading & Hidden-State Extraction Code:
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model_name = "Qwen/Qwen2.5-1.5B-Instruct"

# 1. 4-bit NF4 Quantization Configuration (exposes standard PyTorch hidden states)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

# 2. Load Tokenizer & Model
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="cuda:0",
    trust_remote_code=True,
)

# 3. Extracting Hidden States for Verifier Head (d = 1536)
inputs = tokenizer("Problem statement...", return_tensors="pt").to("cuda:0")
with torch.no_grad():
    outputs = model(**inputs, output_hidden_states=True)

# outputs.hidden_states is a tuple of 29 tensors (input embeddings + 28 layer outputs)
# Last layer representation: shape [batch_size, sequence_length, 1536]
last_hidden_state = outputs.hidden_states[-1]
```

---

## 3. Training & Validation Partitions for Step 3

Member B should use the following frozen partition files from `suite/`:

### A. Training Split (`suite/train/`, 3,750 items total)
The checkable subset (2,400 items) provides labeled supervision for training verifier heads (scoring correctness of generated candidate answers):
- **`suite/train/math.jsonl`**: 600 items (GSM8K train + procedural word problems)
- **`suite/train/science_mcq.jsonl`**: 600 items (ARC-Challenge train)
- **`suite/train/code.jsonl`**: 300 items (MBPP train + synthetic functions)
- **`suite/train/knowledge_qa.jsonl`**: 900 items (Wikipedia train + synthetic store)
- **`suite/train/knowledge_mcq.jsonl`**: 900 items (MMLU train splits)
- **`suite/train/memory_probe.jsonl`**: 450 items (Personal history logs)

### B. Validation Split (`suite/validation/`, 1,250 items total)
Used for checkpoint selection, verifier calibration (Platt scaling / temperature tuning), and gate verification:
- `suite/validation/math.jsonl`: 200 items
- `suite/validation/science_mcq.jsonl`: 200 items
- `suite/validation/knowledge_mcq.jsonl`: 300 items
- `suite/validation/code.jsonl`: 100 items
- `suite/validation/knowledge_qa.jsonl`: 300 items
- `suite/validation/memory_probe.jsonl`: 150 items

---

## 4. B-LLM Baseline Records & Established Gate Hurdles

Member A has evaluated `Qwen2.5-1.5B-Instruct` across all 1,250 validation items. The complete item-level JSONL records are available at:
`reports/step2/run_qwen2.5-1.5b-instruct-q4_validation.jsonl`

### Gate G-Q Hurdle for Member B (Step 3 & Step 7):
- **Evaluation Scope**: 800 checkable validation items (`math`, `science_mcq`, `knowledge_mcq`, `code`).
- **B-LLM Baseline Accuracy**: **56.88%** (455 / 800 correct, 95% Wilson CI: [53.42, 60.27]%).
- **B-LLM Baseline Energy**: **171.55 Net Joules / correct task** (208.17 Gross Joules / correct task on checkable scope).
- **Target Pass Condition (Clause 1 - Accuracy Superiority)**:
  $$\text{Acc}(P1) \ge \mathbf{61.88\%} \quad (+5.00\text{ pp over B-LLM})$$
  with paired bootstrap 95% CI strictly excluding zero ($\Delta_{\text{lo}} > 0$) at net energy $\le \mathbf{171.55\text{ J / correct}}$.
- **Target Pass Condition (Clause 2 - Efficiency Dominance)**:
  $$\text{Acc}(P1) \ge \mathbf{53.88\%} \quad (\text{within 3.00 pp non-inferiority margin confirmed in D4})$$
  at net energy $\le \mathbf{85.78\text{ J / correct}}$ ($\le 50.0\%$ of B-LLM energy).

### Gate G-R Hurdle (Hardware Residency):
- Combined resident GPU VRAM for the base model plus verifier head must remain:
  $$\text{Peak NVML Resident VRAM} \le \mathbf{1,536.0\text{ MB}}$$
  (Available headroom above B-LLM baseline: **120.0 MB**).

---

## 5. Scoring Specifications & Test Harness

Member B must score all model predictions using the frozen evaluation extractors:
- **Scoring Engine**: `evaluation/extractors.py` and `evaluation/evaluator.py`.
- **Authoritative Spec**: [`docs/decisions/scoring_spec.md`](docs/decisions/scoring_spec.md).
- **Golden Test Fixture**: All 115 tests in `tests/test_scoring_golden.py` must pass at 100%.

---

## 6. Verification Checklist Before Step 3 Starts

- [x] B-LLM selected and frozen: `Qwen2.5-1.5B-Instruct` (4-bit NF4).
- [x] All 1,250 baseline validation records generated and committed.
- [x] Empirical gate baselines calculated and recorded in manifest (Decision D18).
- [x] All simulated numbers in `baselines/` and `reports/` retracted and rebuilt.
- [x] 359/359 unit and regression tests passing.
- [x] Repo rules cleanly passing (`check_repo_rules.sh`).

