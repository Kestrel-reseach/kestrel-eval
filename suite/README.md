# Project Kestrel — Suite v0 Handoff (Validation Partition)

**Target Audience:** Member B (Core Modeling, Verification & Baselines)  
**Deliverable:** Evaluation Suite v0 — Validation Partition  
**Repository:** `kestrel-eval`  
**Date:** 2026-11-18  

---

## 1. Overview & Golden Rules

Suite v0 provides the **1,200-item validation partition** for Project Kestrel Prototype 1, structured across 6 task groups per **Decision D1** (`sizes_are: per_partition`).

### Golden Rules:
1. **Develop and Tune Against Validation Only**: All model development, prompt engineering, threshold exploration, and baseline evaluations must use `split="validation"`.
2. **Never Touch Locked-Test**: The 1,200 locked-test items are physically quarantined outside the repository in `kestrel_private/locked_test/`. The loader enforces a hardware/software permission guard (`PermissionError`) if access is attempted. Locked-test is executed **once** at Step 10.
3. **Contamination Reporting**: Always report accuracy on public benchmarks (`Acc_public`) and privately written synthetic items (`Acc_synthetic`) separately. See `reports/CONTAMINATION.md`.

---

## 2. Partition Structure & Verified File Hashes

The validation suite is located in `suite/validation/` and consists of 6 JSONL files.

| Group | Filename | Size | Answer Check Mechanism | SHA-256 Digest |
| :--- | :--- | :--- | :--- | :--- |
| **Math Word Problems** | `math.jsonl` | 200 | `exact_numeric` | `93d3af35fbc8803451a1322a210da172db4884551d0f88171cdbf03b280bd939` |
| **Science MCQ** | `science_mcq.jsonl` | 200 | `answer_key` | `51ca870fbbbe7c42e16e318256336e8e76105338d6a92c7e9e8204c39fff6504` |
| **Knowledge MCQ** | `knowledge_mcq.jsonl` | 300 | `answer_key` | `ece7f06dbd657ad721efc6e5d5c3ae14bf17c0767b9d7574c979704dba62a993` |
| **Code Tasks** | `code.jsonl` | 100 | `unit_tests_pass` | `c21e1dc0bd9834ba84098c185fb7db248614dc7b2afbb246f7ae5f05bea03c11` |
| **Knowledge QA** | `knowledge_qa.jsonl` | 300 | `key_match` | `f2d34d1be2b738eed5aad79a8c84e534ce44ea07e44810053f95f89577310e99` |
| **Memory Probe** | `memory_probe.jsonl` | 100 | `key_from_source_history` | `543beac1bc6fc2bf7786dbb61f31abe8c932c81650309a8f13edbf3a4c3619b7` |
| **Total Validation** | **6 files** | **1,200** | — | — |

*Note: The locked-test partition contains an identical 1,200-item group distribution with hashes frozen in `evaluation/manifest.yaml` (root hash: `22fff5e005245148f85e29c75029e85034ada793ee6b7e7c33b130e8fd9e99b7`).*

---

## 3. JSONL Record Schema

Every line in each `.jsonl` file is a valid JSON object adhering to the unified evaluation schema:

### Universal Fields
- `id` / `item_id` (str): Unique item identifier (e.g., `math_val_0001`, `sci_val_0042`).
- `group` (str): One of `math`, `science_mcq`, `knowledge_mcq`, `code`, `knowledge_qa`, `memory_probe`.
- `split` (str): `"validation"`.
- `prompt` (str): Full text prompt formatted and ready to present to the model.
- `target` (str): Canonical correct answer.
- `answer_check` (str): Evaluation protocol to score model output.

### Group-Specific Metadata
- **`math`**: `metadata.scratchpad` contains the ground-truth step-by-step derivation.
- **`science_mcq`**: `choices` contains a list of 4 options (`[{"label": "A", "text": ...}, ...]`), `answerKey` is the correct letter.
- **`knowledge_mcq`**: `subject` indicates which of the 10 MMLU-style disciplines is covered (30 items each: `college_biology`, `college_computer_science`, `college_physics`, `econometrics`, `high_school_chemistry`, `high_school_geography`, `high_school_macroeconomics`, `high_school_world_history`, `machine_learning`, `professional_law`).
- **`code`**: `metadata.entry_point` specifies the target function name; `metadata.test_code` contains the executable unit test harness.
- **`knowledge_qa`**: `passage_id`, `passage_title`, and `passage` provide the source Wikipedia abstract text; `answer_span` marks `[start, end]` character offsets of the target in the passage.
- **`memory_probe`**: `metadata.is_stale_fact` (30 items) indicates facts that updated over time; `metadata.stale_values` lists previous/deprecated values that the model must reject (Gate G-M).

---

## 4. How to Run / Python API

### Loading Items in Python

The cleanest way for Member B to load validation items is via `evaluation.suite.load_suite_partition`:

```python
from evaluation.suite import load_suite_partition

# 1. Load the entire validation partition (1,200 items)
val_suite = load_suite_partition(split="validation")
print(f"Loaded {len(val_suite)} validation items.")

# 2. Load a specific group (e.g. Code, 100 items)
code_tasks = load_suite_partition(split="validation", group="code")
for task in code_tasks[:3]:
    print(task["id"], task["prompt"])

# 3. Accessing locked-test without authorization raises PermissionError:
try:
    load_suite_partition(split="locked_test")
except PermissionError as e:
    print("Guard active:", e)
```

### Running Evaluation Harness with Checkpointing

To evaluate a model against the validation suite using the Kestrel evaluation harness:

```bash
uv run python -m evaluation.run_matrix \
  --manifest evaluation/manifest.yaml \
  --split validation \
  --output runs/val_baseline_candidate.jsonl
```

The run matrix handles resume checkpoints, NVML energy instrumentation (if GPU is present), latency tracking, and schema validation.
