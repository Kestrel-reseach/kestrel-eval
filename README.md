# kestrel-eval

Locked evaluation suite, baselines and energy-measurement harness for
[Kestrel](https://github.com/Kestrel-reseach/kestrel). This repository answers
one question: on a fixed slice, how do quality, energy per correct task and
resident memory compare?

The shared plan, pass/kill gates, rules and step status are in the
**[Kestrel PLAN.md](https://github.com/Kestrel-reseach/kestrel/blob/main/PLAN.md)**.
This README is the working copy for the suite itself.

## What lives here

```
.
├── evaluation/
│   ├── manifest.yaml           seeds, splits, budgets, thresholds, hashes
│   ├── run_matrix.py           runs systems × splits × configs
│   └── metrics.py              quality, energy and memory metrics
├── energy/
│   └── harness.py              power sampling, idle baseline, calibration
├── suite/
│   ├── public/                 public benchmark items
│   ├── synthetic/              privately written synthetic items
│   └── personal_memory/        synthetic stale-fact histories
├── baselines/                  quantized small-model candidates
├── reports/                    generated result tables
└── tests/                      no future leakage, resume, determinism, writes
```

The files are currently empty placeholders. They are filled in Steps 0–2 and
used again at Step 10.

## Locked evaluation suite

| Group | Size | Answer check |
| --- | --- | --- |
| Math word problems | 200 | exact numeric match |
| Science multiple choice (ARC-Challenge style) | 200 | answer key |
| Knowledge multiple choice (MMLU style, 10 subjects) | 300 | answer key |
| Code tasks with unit tests | 100 | tests pass |
| Knowledge QA over a fixed corpus snapshot | 300 | key match |
| Personal-memory probe (30 stale-fact items) | 100 | key from source history |

Fixed train / validation / locked-test splits are hashed in the manifest
**before any tuning**. No item may appear in two partitions. Add privately
written or synthetic items, because public items may be in every model's
training data; report both. The personal-memory probe uses **synthetic histories
only** unless the owner approves real items one by one.

## Reference systems

- **F** — frontier model, run once on public and synthetic items only. For the
  memory probe it is run with no history and with the full history in the prompt.
- **B-LLM** — best quantized small model from the shortlist (3–5 candidates at
  4-bit, e.g. 0.8B and 2B Qwen3.5 small models, Granite 4.0 Nano 1.5B, LFM2),
  with plain retrieval. Chosen by measurement, not by name.
- **P1** — the prototype from the `kestrel` repository.

## Gates

Proposed gates, accepted by the owner before Step 0 freezes them:

- **G-Q** — on checkable and store groups, P1 beats B-LLM by ≥5 percentage
  points (paired bootstrap 95% interval excludes zero) at no more energy per
  correct task; or matches B-LLM at ≤50% of its energy per correct task.
- **G-F** — report the gap to F and the fraction of the B-LLM-to-F gap P1 closes;
  ≥25% on the checkable groups is a strong result.
- **G-M** — on the memory probe, P1 is at least as good as F with no history and
  within 5 points of F with full history; stale-fact errors at most half those
  of plain external memory.
- **G-R** — ≤1.5 GB resident VRAM on the GPU tier, ≤4 GB resident RAM proposed
  on the CPU tier (SSD index excluded, reported separately); report joules per
  correct task, p50 and p95 latency.
- **No regression** — adding a component must not drop earlier-step results by
  more than 3 points.

## Run records

Every run writes JSONL with at least:

```
run_id, git_commit, config_hash, seed, split, item_id, system,
tokens_generated, passes, verifier_score, retrieval_hits,
bytes_read_from_ssd, energy_joules, wall_time_ms, peak_vram_mb, correct
```

Config, versions, seeds and checkpoint hashes are saved with the run.

## Energy measurement

Energy is **joules per correct task**, not tokens per second per watt. Record an
idle baseline (about 10 minutes), subtract it and also report the total.
Calibrate software counters (CPU energy counters, NVML) against a wall meter
once. If that is not possible, report **relative energy only** and say so on
every result. A pilot is "promising", not "passed", until it holds on locked
data.

## Working rules

- Develop from the validation partition. Run the locked test partition **once**,
  at Step 10, with the frozen config.
- Never change a metric or threshold after seeing results. Failed components
  are reported, not hidden.
- Never commit secrets, real personal data, hostnames, IPs or device
  identifiers. Stage files by name and check the staged list and diff before
  committing. No co-author or AI-attribution trailers in commits or PRs.
- Model versions and sizes dated after early 2026 are unverified; confirm
  before downloading.

## Development

CI (`.github/workflows/ci.yml`) runs on pushes and pull requests to `main` and
performs lightweight checks only: `ruff check .`, `ruff format --check .` and
`pytest -q`. The harness itself needs local hardware (Ryzen 7 5800H, RTX 3060
Laptop 6 GB, NVML and CPU energy counters) and is **not** run in CI.

Python 3.12 is the CI target. To reproduce the checks locally:

```sh
python -m pip install ruff pytest
ruff check .
ruff format --check .
pytest -q
```

`pytest` currently exits 5 (nothing collected) because the Step 0 tests are not
written yet; CI tolerates that specific exit code and fails on real test
failures.
