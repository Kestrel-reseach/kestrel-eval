# Kestrel-eval agent rules — always on
# Read AGENTS.md first, then this file, before any change.

## Non-negotiable rules (from PLAN.md and rules.md)

- Work only from the **validation** partition. Never open or run the
  **locked-test** split before Step 10, and never reference its item IDs.
- Never change a metric or threshold after seeing results. Proposed thresholds
  are marked PROPOSED in `evaluation/manifest.yaml`; only the owner may
  accept or change them.
- Never invent numbers. Any value that has not been measured yet is written as
  UNMEASURED. Any value pending an owner decision is written as UNDEFINED.
- Never write fake tests to make CI pass. Tests must assert real behaviour.
- Never commit secrets, real personal data, hostnames, IPs or device
  identifiers. The memory probe uses synthetic histories unless the owner
  approves real items one by one.
- Stage files by name and check the staged list and diff before committing.
  Never use `git add -A` or `git add .`.
- No co-author or AI-attribution trailers in commits or PR descriptions.
- Do not edit `.github/workflows/ci.yml` or `scripts/check_repo_rules.sh`
  without asking.

## Per-step discipline

- One topic per branch and PR. Branch names: `step-<n>-<short-topic>`.
- A PR description states the step, the deliverables and the gate result.
- After each PR is committed, stop and wait for review.
- Before saying "done", run the preflight check and paste the raw output.

## Preflight check (run before every PR)

```
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Or using a venv:

```
/path/to/venv/bin/ruff check .
/path/to/venv/bin/ruff format --check .
/path/to/venv/bin/pytest -q
```

## Open owner decisions (do not guess — ask)

1. Frontier model F and cost cap.
2. Wall power meter (yes → absolute joules; no → relative-only, labelled on every result).
3. Gate acceptance (G-Q, G-F, G-M, G-R, no-regression — all PROPOSED until owner accepts).
4. Cloud escalation (default: off).
5. Real personal data in memory probe (default: synthetic only).
6. Corpus for the knowledge-QA group (required before Step 1 finishes).

