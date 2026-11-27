# Repository and project rules

Applies to every repository in the `Kestrel-reseach` GitHub org: `kestrel` and
`kestrel-eval`. Each repo keeps a copy of this file at its root. When a rule
changes, update every copy in the same round of PRs so the two do not drift.

## Org-wide rules

- Both repositories are public. The default branch is `main` and is protected:
  changes arrive through pull requests, the `lint-and-test` check must pass,
  branches must be up to date before merge, force pushes and branch deletion
  are blocked.
- Admins can bypass protection only for a genuine emergency, and must record
  why in the status log. Normal work, including documentation, goes through a
  PR.
- Use squash merges. Branch deletion on merge is enabled; do not recreate a
  branch after it has been merged.
- Never commit secrets, real personal data, hostnames, IPs or device
  identifiers. This includes API keys, tokens, private keys, `.env` files and
  real personal histories. The memory probe uses synthetic histories unless the
  owner approves real items one by one.
- No co-author or AI-attribution trailers in commits or PRs. Commit messages
  are plain and factual.
- Stage files by name. Check the staged list and the staged diff before
  committing; never use a blanket `git add -A` as a shortcut.
- CI is lightweight on purpose: lint, format check and unit tests. Model
  inference, energy measurement (NVML / CPU counters) and the locked suite need
  the owner's local hardware and stay out of CI.

## Project rules

- The owner's private Notion workspace is the single source of truth for the
  goal, steps, gates, rules and status; these details are not kept in this public
  repo. Work one step at a time, in order, and record status with numbers and
  commit in that workspace when a step passes, fails or is killed.
- Do not decide the open owner decisions recorded there; ask. They cover the
  frontier model F and its cost cap, the wall power meter, gate acceptance,
  cloud escalation and real personal data.
- Develop from the validation partition. Run the locked test partition **once**,
  at Step 10, with the frozen config. No tuning against it.
- Never change a metric or threshold after seeing results. Failed components
  are reported, not hidden. A pilot is "promising", not "passed", until it
  holds on locked seeds.
- Every run writes JSONL with at least: `run_id`, `git_commit`, `config_hash`,
  `seed`, `split`, `item_id`, `system`, `tokens_generated`, `passes`,
  `verifier_score`, `retrieval_hits`, `bytes_read_from_ssd`, `energy_joules`,
  `wall_time_ms`, `peak_vram_mb`, `correct`. Save config, versions, seeds and
  checkpoint hashes alongside the run.
- Energy is joules per correct task. Record a roughly 10 minute idle baseline,
  subtract it and also report the total. Calibrate counters against a wall
  meter once; if that is impossible, report relative energy only and say so on
  every result.
- Report every ablation and every failed component. A component whose removal
  does not hurt accuracy or energy is removed. A kill gate is a result to
  publish, not a failure to hide.
- Model versions and sizes dated after early 2026 are unverified; confirm
  before downloading.
- The prototype is not token-free and not frontier parity on general
  benchmarks. The core is a pretrained small language model that emits tokens.
  The SSD store is plain retrieval until trained jointly with the model; do not
  call it a new architecture.

## Git and PR rules

- One topic or step per branch and PR. Name branches `step-<n>-<short-topic>`
  for implementation work and `docs-<short-topic>` for documentation.
- A PR description states the step, the deliverables and the gate result. Point
  to the relevant status entry in the private workspace when a step finishes.
- Commits are small, build on a passing CI run, and contain no trailers.
- Do not commit generated run output, credentials, dataset snapshots containing
  real data, or large model binaries. Report paths and hashes instead.
- Keep this `rules.md` and the Notion execution page consistent. If they
  disagree, the private Notion plan wins and this file gets corrected.

## Enforcement

Checked automatically on push and pull request by
`.github/workflows/ci.yml`, using `scripts/check_repo_rules.sh`:

- `rules.md` exists and contains the required sections.
- No `.env`-style files are tracked.
- Tracked files are scanned for common secret patterns (GitHub, AWS, OpenAI,
  Slack tokens and private key headers).
- Commit messages in the PR range contain no co-author or AI-attribution
  trailers.
- `ruff check .`, `ruff format --check .` and `pytest -q` pass.

Reviewed manually because automation cannot do it reliably: real personal data
and hostnames/IPs, metric and threshold freezing, validation-versus-locked
partition discipline, gate acceptance, wall-meter calibration and the "no
AI-attribution" rule in PR descriptions.
