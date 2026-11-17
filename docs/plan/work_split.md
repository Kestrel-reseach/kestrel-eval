# Kestrel Prototype 1 — 3-Member Work Split & Deliverables

> [!NOTE]
> Reference copy only. The single source of truth is `PLAN.md` in the `kestrel`
> repository and the owner's Notion workspace. If this document and `PLAN.md`
> ever disagree, `PLAN.md` wins.

## 1. Non-negotiable rules
- Work from the validation partition only. Run the locked-test partition once, at Step 10, with the frozen config.
- Never change a metric or threshold after seeing results.
- Every run writes JSONL records with at least: run_id, git_commit, config_hash, seed, split, item_id, system, tokens_generated, passes, verifier_score, retrieval_hits, bytes_read_from_ssd, energy_joules, wall_time_ms, peak_vram_mb, correct.
- Energy is joules per correct task. Record a ~10 minute idle baseline, subtract it, and report both total and net.
- The prototype is not token-free and not frontier parity on general benchmarks.
- Model versions and sizes dated after early 2026 are unverified; confirm before downloading.
- Never commit secrets, real personal data, hostnames, IPs or device identifiers. No co-author or AI-attribution trailers.

## 2. Ownership map
- **Member A** (Evaluation, measurement & memory lead): Owns Steps 0, 1, 2, 6, 10 (+ optional 9). Primary repo: `kestrel-eval`, then `kestrel`.
- **Member B** (Core reasoning & integration lead): Owns Steps 3, 4, 5, 7 (+ optional 8). Primary repo: `kestrel`.
- **Member C** (Light support): Bounded support tasks only. No step ownership, no gate decisions.

## 3. Member A Deliverables
- **Step 0**: manifest.yaml, schema.py, harness.py, tests (no future leakage, checkpoint resume, determinism, memory write timing).
- **Step 1**: 6 groups suite, splits, hashing, contamination note.
- **Step 2**: 3–5 quantized 4-bit baseline candidates, baseline table, chosen B-LLM, run F.
- **Step 6**: memory_gated.py with verified writes, timestamps, decay, conflicts.
- **Step 10**: Final evaluation on locked-test, paired bootstrap intervals, final report.

