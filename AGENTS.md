# kestrel-eval: agent instructions (Member A)

You are helping Member A build the evaluation, measurement and memory side of
Kestrel Prototype 1.

Precedence: `rules.md` and `PLAN.md` (in the `kestrel` repository) are the authoritative
sources of truth for repository rules, project scope, and gates. If anything
disagrees, `rules.md` and `PLAN.md` win.

Read these before changing anything:
1. `rules.md` (repository rules, enforced by CI)
2. `.agents/rules/kestrel-core.md` (operational discipline for agents)
3. `PLAN.md` in the `kestrel` repository (Prototype 1 plan)

Skills in `.agents/skills/` load on demand:
- `eval-harness-jsonl` — JSONL schema and validator
- `energy-measurement` — joules-per-task protocol
- `eval-statistics` — bootstrap CIs and gate arithmetic
- `suite-split-hash` — suite groups, splits, hashing, leakage checks
- `baseline-runs` — Step 2 candidate protocol

Workflows: use the commands below.
Work in small pull requests. After each PR, stop and wait for review.

## Preflight (run before every PR)

```
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

## Report format (paste raw output after every step)

```
STEP / PR:
Commit hash(es):
Files added or changed:
Commands run and RAW output (ruff, pytest, harness runs):
Test results: passed / failed / skipped:
Measured vs assumed (list every number and its source):
Deviations from the plan:
Open questions / blockers:
```

## Open owner decisions (do not guess — ask)

1. Frontier model F and cost cap.
2. Wall power meter (yes → absolute joules; no → relative-only, labelled on every result).
3. Gate acceptance (all gates are PROPOSED until the owner accepts them).
4. Cloud escalation (default: off).
5. Real personal data in memory probe (default: synthetic only).
6. Corpus for the knowledge-QA group (required before Step 1 finishes).

