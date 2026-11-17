---
name: eval-harness-jsonl
description: >
  JSONL run record schema for Kestrel Prototype 1 evaluation.
  Load this skill when writing or validating run records, designing
  evaluation pipelines, or implementing the run_matrix.
---

# Skill: eval-harness-jsonl

## What it covers

Every evaluation run writes one JSONL record per item to a `.jsonl` file.
The schema is defined in `evaluation/schema.py` and enforced by
`validate_record()` and `validate_jsonl_file()`.

## Required fields

```
run_id          str    — unique run identifier (e.g. "run-20260101-001")
git_commit      str    — at least 7 hex characters of the current commit
config_hash     str    — SHA-256 of the frozen config dict (sorted keys)
seed            int    — the eval_run seed from manifest.yaml
split           str    — "train" | "validation" | "locked_test"
item_id         str    — group-prefixed item identifier (e.g. "math-001")
system          str    — "F" | "B_LLM" | "P1"
tokens_generated int   — total tokens emitted (all passes combined)
passes          int    — number of generate-score cycles (>= 1)
verifier_score  float | null — calibrated correctness probability in [0,1]
retrieval_hits  int    — number of SSD chunks read (0 when store not used)
bytes_read_from_ssd int — total bytes read from the knowledge store
energy_joules   float  — gross CPU + GPU energy for this item (non-negative)
wall_time_ms    float  — elapsed wall time in milliseconds
peak_vram_mb    float  — peak VRAM usage in megabytes
correct         bool   — whether the final answer matched the answer key
```

## Rules

- `verifier_score` may be `null` before Step 3 delivers the verifier.
- `split` is validated; "locked_test" is blocked unless `allow_locked_test=True`
  (only set at Step 10).
- `energy_joules` is gross energy; subtract `idle_power_w * wall_time_s` to
  get the net figure for reporting.
- `config_hash` = `hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()`.

## Validator usage

```python
from evaluation.schema import validate_record, validate_jsonl_file
errors = validate_record(record)
# errors == [] means valid
errors = validate_jsonl_file(Path("runs/run-001.jsonl"))
```

## Saving config alongside a run

Save a `run_<run_id>_config.json` next to the JSONL file:

```json
{
  "run_id": "run-20260101-001",
  "git_commit": "abc1234deadbeef",
  "config_hash": "<sha256>",
  "seed": 20260101,
  "model": "qwen3.5-0.8b-instruct-q4",
  "split": "validation",
  "manifest_path": "evaluation/manifest.yaml"
}
```

