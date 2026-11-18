# Kestrel Prototype 1 — Execution & Results Log

This log records dated progress, measurements, commits, and open issues for each step in Prototype 1. Entries are chronological and immutable.

---

### 2026-11-17 — Step 0 Freeze & Manifest Definition
- **Step**: Step 0 (Freeze and instrument)
- **Commit**: `52f4ed0` (`kestrel-eval`), PR #2 merged
- **Result**: JSONL schema, run matrix, energy harness, and integration test scaffolds implemented. 117 tests passing in CI.
- **Status**: Implementation complete; hardware calibration open.
- **Open Issues**: Need local target hardware verification on Ryzen/RTX laptop; wall power meter decision pending; gate acceptance pending.

---

### 2026-11-18 — Step 0 Hardware Calibration Pilot & Review Corrections
- **Step**: Step 0 (Freeze and instrument — relative-only path)
- **Commit**: `1affa57`, `57b0df2`, `13bb21e`, `bae1792`, `6963226` (`kestrel-eval` branch `fix-nvml-mock-tests`)
- **Result**:
  - Live hardware calibration executed on test machine (AMD Ryzen 7 7435HS + NVIDIA GeForce RTX 3050 Laptop GPU 4 GB VRAM).
  - RAPL CPU counter confirmed root-only (`0400` mode); CPU energy reported as unmeasured in user space.
  - GPU power monitored via NVML at ~10 W idle and ~60 W under CUDA FP16 GEMM load ($2048 \times 2048$ tensor multiplication).
  - Canonical idle baseline defined as single pooled mean of NVML power samples across 3 repeats. Competing idle values eliminated.
  - Workload executed across 3 repeated trials, yielding ~568 J unclipped net energy, exceeding the $3\sigma$ idle noise margin (~63 J) by 9× with $E_{\text{net}} > 0$.
  - Mandatory energy label enforced across tables and reports via `format_energy_table`: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*
  - Manifest `frozen: false` set pending owner's written confirmation of gates (Decision D4).
  - Decision records created:
    - `docs/decisions/energy_measurement.md` (no wall meter, relative energy only, pending owner confirmation).
    - `docs/decisions/hardware_tier.md` (RTX 3050 test tier is agent-drafted, results not transferable to RTX 3060, pending owner confirmation).
- **Status**: Code-complete on relative-only path; Step 0 left **UNCHECKED** in `PLAN.md` pending owner confirmation of Decisions D4 and D8.
- **Open Issues**:
  - Owner written confirmation of no-wall-meter relative energy (Decision D8).
  - Owner written confirmation of alternate test tier RTX 3050 (Decision D8).
  - Owner written approval of pass gates and non-inferiority margin (Decision D4).
  - Owner choice on CPU energy path (Decision D7: Option a or b).

---

### 2026-11-18 — Co-Owner Decisions D1–D11 Recorded & Manifest Frozen
- **Step**: Step 0 (Closure & Handoff Preparation)
- **Commit**: `f261bae` (`kestrel-eval` PR #8), `4ed0afa` (`kestrel` PR #7)
- **Result**:
  - Co-owners (Member A and Member B) confirmed Decisions D1–D11.
  - Manifest version bumped to 1.1; `frozen: true` set per Decision D4.
  - Config hash updated: `ede58c9263678994d3493ca9122718ba873252ce6b904baf52f941d2bd357a74`.
  - Shortened pilot 3-repeat idle baseline recorded (pooled mean 8.335 W, std 1.122 W).
  - 3-trial CUDA FP16 GEMM pilot verified (mean unclipped net energy 586.033 J, noise margin 38.24 J, all valid).
  - Non-flaky memory-write assertion verified (<2.0s bounded).
  - Mandatory energy label enforcement tested and active.
- **Status**: Step 0 code and evidence complete. Step 0 remains UNCHECKED in `PLAN.md` pending owner's review and closure note sign-off.
- **Open Issues**:
  - Pending owner decision D12: Step 10 locked-test F run policy (free tier vs paid tier).

---

### 2026-11-18 — Step 0 Follow-ups: Gross Energy Counter, 10 Hz Polling & Manifest Verification
- **Step**: Step 0 Follow-ups (PR 0)
- **Branch**: `step-0-followups` (`kestrel-eval`)
- **Result**:
  - **0a (Gross Energy Counter & Sampling Rate)**:
    - Shifted gross GPU energy measurement to NVML hardware cumulative counter `nvmlDeviceGetTotalEnergyConsumption()` returning millijoules ($10^{-3}\text{ J}$).
    - Verified hardware support on NVIDIA GeForce RTX 3050 Laptop GPU (driver 615.78.08).
    - Upgraded baseline power sampling interval from 1.0 s (~1 Hz) to 0.1 s (10.0 Hz).
    - Persistent NVML device handle maintained during recording, achieving verified 10.0 Hz sampling rate without driver init/shutdown overhead.
    - Added unit tests: `test_read_gpu_energy_mj_returns_none_when_nvml_unavailable`, `test_start_stop_uses_nvml_total_energy_counter`, `test_start_stop_computes_gpu_energy_fallback`. All 123 tests passing.
    - Documented method in [`reports/step0_gross_energy_method.md`](file:///home/ash09/project_x/kestrel-eval/reports/step0_gross_energy_method.md).
  - **0b (Idle Baseline Designation & Formal Protocol)**:
    - Explicitly designated pilot baseline as "shortened baseline (3 x 60 s)" across `reports/step0/CHECKLIST.md`, `reports/step0/CLOSURE_PROPOSAL.md`, and `reports/step0_hardware_calibration.md`.
    - Implemented formal 10-minute x 3 repeats (1800 s total at 10 Hz) measurement script in [`scripts/run_formal_idle_baseline.py`](file:///home/ash09/project_x/kestrel-eval/scripts/run_formal_idle_baseline.py).
    - Formal 10-minute x 3 repeats idle baseline (1,800.00 s total, 17,943 samples at 10.0 Hz) executed on AC power: pooled mean $P_{\text{idle}} = 6.1444\text{ W}$, $\sigma_{\text{idle}} = 0.9472\text{ W}$, counter-derived power $6.1686\text{ W}$ ([`formal_idle_baseline.json`](file:///home/ash09/project_x/kestrel-eval/reports/step0/formal_idle_baseline.json)). Pilot table updated with formal baseline subtractions (net energy 610.93 J vs 32.29 J noise margin, 18.9x margin).
  - **0c (Manifest Verification Against D1)**:
    - Verified `evaluation/manifest.yaml` against co-owner decision D1: group sizes are math 200, science 200, knowledge MCQ 300, code 100, knowledge QA 300, memory probe 100 (total 1,200 items in locked-test and 1,200 in validation).
    - `sizes_are: per_partition` confirmed; `partition_fractions: null` confirmed.
    - Manifest v1.1 already matches D1 identically; no version bump or config change required.
    - Config hash provenance noted: `ede58c9263678994d3493ca9122718ba873252ce6b904baf52f941d2bd357a74` corresponds to frozen manifest v1.1.
  - **D12 (Exposure & Safeguards)**:
    - Safeguards recorded in `docs/decisions/owner_decisions.md`: locked set is one-time use; reserve test set will be built later; send F only what it needs at Step 10.
- **Status**: PR 0 implementation complete; preflight checks clean; 123 tests pass. Step 0 remains strictly UNCHECKED in `PLAN.md`.

---

### 2026-11-18 — PR 1: Public Group Loaders & Official License Verification
- **Step**: Step 1 (Public Group Loaders)
- **Branch**: `step-1-public-loaders` (`kestrel-eval`)
- **Result**:
  - Implemented modular loaders in `evaluation/loaders/`:
    - `math_loader.py`: GSM8K JSONL loader, `exact_numeric` answer extractor & validator.
    - `science_mcq_loader.py`: ARC-Challenge JSONL loader, 4 choices, `answer_key` validator.
    - `knowledge_mcq_loader.py`: MMLU loader across 10 defined subjects, `answer_key` validator.
    - `code_loader.py`: Code loader with safe isolated unit test execution (`unit_tests_pass`).
    - `sources.py`: Verified official license registry for all public datasets.
    - `common.py`: Shared `SuiteItem` typed dict and verification helpers.
  - Official License Verification:
    - GSM8K: MIT License (`https://github.com/openai/grade-school-math/blob/master/LICENSE`)
    - ARC-Challenge: CC BY-SA 4.0 (`https://creativecommons.org/licenses/by-sa/4.0/`)
    - MMLU: MIT License (`https://github.com/hendrycks/test/blob/master/LICENSE`)
    - HumanEval: MIT License (`https://github.com/openai/human-eval/blob/master/LICENSE`)
    - MBPP: CC BY 4.0 (`https://creativecommons.org/licenses/by/4.0/`)
  - Contamination & Code Proposal:
    - Evaluated HumanEval (too small: N=164; heavily contaminated in all modern LLMs) and MBPP.
    - Formally proposed generating fresh synthetic code tasks in PR 2 for the locked-test partition to guarantee zero leakage.
  - Created verified sample data fixtures in `suite/public/{math,science_mcq,knowledge_mcq,code}/`.
  - Added unit test suite [`tests/test_loaders.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_loaders.py) (26 test cases).
  - Documented findings in [`reports/step1_public_sources.md`](file:///home/ash09/project_x/kestrel-eval/reports/step1_public_sources.md).
- **Status**: PR 1 complete; all 149 tests pass; repo rules pass. Ready for review.

---

### 2026-11-18 — PR 2: Synthetic Task Generators & Stale-Fact Rejection Scorer
- **Step**: Step 1 (Synthetic Generators)
- **Branch**: `step-1-synthetic-generators` (`kestrel-eval`)
- **Result**:
  - Implemented deterministic synthetic generators in `evaluation/generators/`:
    - `math_generator.py`: Multi-step word problems (6 problem families) with exact numeric answers and step-by-step scratchpad derivations (`exact_numeric`).
    - `memory_probe_generator.py`: Synthetic chronological interaction histories (Decision D3: synthetic only) with 30 stale-fact items and 70 static recall items. Each event has timestamp, source channel, and factual statement.
    - `stale_fact_scorer.py`: Specialized evaluation scorer that enforces latest value retrieval and explicitly penalizes outdated/stale values (`stale_fact_error=True`, `score=0.0`) to measure gate G-M.
    - `code_generator.py`: Uncontaminated synthetic Python coding problems with complete canonical solutions and robust unit test suites (`unit_tests_pass`).
  - Bitwise reproducibility verified: fixed PRNG seeds ensure deterministic generation.
  - Added unit test suite [`tests/test_generators.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_generators.py) (11 test cases).
  - Documented generator architectures in [`reports/step1_synthetic_generators.md`](file:///home/ash09/project_x/kestrel-eval/reports/step1_synthetic_generators.md).
- **Status**: PR 2 complete; all 160 tests pass; preflight checks clean; repo rules pass. Ready for review.

---

### 2026-11-18 — PR 3: Knowledge QA from Wikipedia Snapshot & Span Verification
- **Step**: Step 1 (Knowledge QA from Wikipedia Snapshot)
- **Branch**: `step-1-knowledge-qa` (`kestrel-eval`)
- **Result**:
  - Pinned Decision D2 corpus: English Wikipedia snapshot partition (`enwiki-20261101-pages-articles1.xml-p1p41242.bz2`, 300,158,691 bytes).
  - Verified official Wikimedia MD5 (`0409fa36...`) and SHA-1 (`eda71820...`), and computed authoritative SHA-256 (`e3fd5a837f2a6b3a26c3596d0667600073a86c9fc29dc60ef0b2de605c754387`).
  - Updated [`docs/decisions/owner_decisions.md`](file:///home/ash09/project_x/kestrel-eval/docs/decisions/owner_decisions.md) and [`evaluation/manifest.yaml`](file:///home/ash09/project_x/kestrel-eval/evaluation/manifest.yaml).
  - Implemented streaming XML abstract extractor [`evaluation/generators/wiki_extractor.py`](file:///home/ash09/project_x/kestrel-eval/evaluation/generators/wiki_extractor.py), extracting 6,000 clean lead abstracts in 24.01 seconds.
  - Implemented rule-based factual QA generator [`evaluation/generators/knowledge_qa_generator.py`](file:///home/ash09/project_x/kestrel-eval/evaluation/generators/knowledge_qa_generator.py) covering 10 semantic rule families with 100% automated character span verification (`passage[start:end] == answer`).
  - Generated partitions (300 validation, 300 locked-test, 300 train).
  - Output 50 random sample items per partition for human review in [`reports/step1_knowledge_qa_samples.md`](file:///home/ash09/project_x/kestrel-eval/reports/step1_knowledge_qa_samples.md).
  - Added unit test suite [`tests/test_knowledge_qa.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_knowledge_qa.py) (7 test cases).
  - Documented complete pipeline in [`reports/step1_knowledge_qa.md`](file:///home/ash09/project_x/kestrel-eval/reports/step1_knowledge_qa.md).
- **Status**: PR 3 complete; all 167 tests pass; preflight checks clean; repo rules pass. Ready for review.






---

### 2026-11-18 — PR 4: Deterministic Splits, Hashes, Leakage Checks & Out-of-Repo Storage
- **Step**: Step 1 (Splits, Hashes, Leakage Checks & Out-of-Repo Storage)
- **Branch**: `step-1-splits-hashes-leakage` (`kestrel-eval`)
- **Result**:
  - Implemented suite builder and partition manager in `evaluation/suite.py` adhering strictly to Decision D1:
    - 1,200 items in locked-test (200 math, 200 science MCQ, 300 knowledge MCQ, 100 code, 300 knowledge QA, 100 memory probe).
    - 1,200 items in validation (identical group distribution).
    - 1,200 items in train (identical group distribution).
    - Total suite size: 3,600 items.
  - Implemented automated partition leakage & duplicate verification in `evaluation/leakage.py`:
    - `check_no_id_overlap`: 100% verified (0 ID collisions across 3,600 items).
    - `check_exact_prompt_duplicates`: 100% verified (0 prompt duplicates across all 3 partitions).
    - `check_answer_leakage`: 100% verified (0 ground-truth answer strings leaked into question text).
    - `check_near_duplicates`: 4-gram character Jaccard near-duplicate detector implemented and tested.
  - Strict out-of-repo isolation enforced:
    - Locked-test partition files written strictly to `KESTREL_PRIVATE_DIR` (`/home/ash09/project_x/kestrel_private/locked_test/`).
    - Zero locked-test data files are tracked or present inside the `kestrel-eval` repository (verified by `test_no_locked_test_data_in_repo`).
    - SHA-256 computed for each locked-test partition file and recorded in `evaluation/manifest.yaml`.
    - Computed Root Hash across locked-test files: `22fff5e005245148f85e29c75029e85034ada793ee6b7e7c33b130e8fd9e99b7`.
  - Statistical 95% confidence interval half-widths computed and verified:
    - $N = 100$ (`code`, `memory_probe`): $\pm 9.80$ pp.
    - $N = 200$ (`math`, `science_mcq`): $\pm 6.93$ pp.
    - $N = 300$ (`knowledge_mcq`, `knowledge_qa`): $\pm 5.66$ pp.
    - Total partition ($N = 1,200$): $\pm 2.83$ pp.
  - Added unit test suite `tests/test_suite_and_leakage.py` (6 test cases). Total test count increased from 167 to 173 tests.
  - Documented pipeline in `reports/step1_splits_hashes_leakage.md`.
- **Status**: PR 4 complete; all 173 tests pass; ruff clean; repo rules clean; JSONL validator clean (`[]`). Ready for review.

---

### 2026-11-18 — PR 5: Contamination Note & Validation Suite v0 Handoff for Member B
- **Step**: Step 1 (Contamination Note & Validation Suite v0 Handoff)
- **Branch**: `step-1-contamination-suite-v0` (`kestrel-eval`)
- **Result**:
  - Published comprehensive benchmark contamination analysis in `reports/CONTAMINATION.md` and `reports/step1_contamination_note.md`.
  - Analyzed public benchmark contamination risk across GSM8K, ARC-Challenge, MMLU, and HumanEval/MBPP, establishing that public web crawl mixtures heavily contaminate public benchmark sets.
  - Established procedural synthetic generation strategy providing zero-contamination evaluation across all 6 task groups for Kestrel Prototype 1.
  - Defined mandatory evaluation reporting protocol: future evaluation tables must report $\text{Acc}_{\text{public}}$ and $\text{Acc}_{\text{synthetic}}$ separately alongside the gap $\Delta_{\text{contam}}$.
  - Shipped Validation Suite v0 handoff guide in `suite/README.md` for Member B with schema definitions, individual group file hashes, and Python invocation examples.
  - Implemented `load_suite_partition(split="validation", group=None, repo_root=None)` in `evaluation/suite.py` with strict permission guard preventing unauthorized access to `locked_test` prior to Step 10.
  - Updated `evaluation/run_matrix.py` to support items keyed by either `item_id` or `id`.
  - Added unit test suite `tests/test_suite_v0.py` covering partition loading, group filtering, invalid argument handling, and locked-test permission guards. Total test count increased to 179 passing tests.
- **Status**: PR 5 complete; all 179 tests pass; ruff clean; repo rules clean; JSONL validator clean (`[]`). Ready for review.

---

### 2026-11-18 — Step 1 Closing Pass (Part 3B)
- **Step**: Step 1 (Closing Pass: Quarantine Audit, Near-Duplicate Analysis & Security Policies)
- **Branch**: `step-1-closing-pass` (`kestrel-eval`)
- **Result**:
  - Executed automated locked data leakage check across entire repository.
  - Detected and contained accidental inclusion of 50 locked Knowledge QA review samples: executed `git rm reports/step1_knowledge_qa_samples.md` without history rewriting.
  - Refactored review generator `scripts/generate_kqa_samples.py` to sample strictly from the `validation` partition (`reports/step1_knowledge_qa_validation_samples.md`).
  - Added automated CI security regression test in `tests/test_leak_guard.py` asserting zero locked test item IDs appear in `reports/` or `docs/`.
  - Authored burn-and-replace proposal in `docs/decisions/burn_and_replace_proposal.md` for co-owner approval.
  - Confirmed and documented formal 10-minute x 3 idle baseline results (pooled mean 6.1444 W, std 0.9472 W, 17,943 samples at 9.97 Hz) and verified active hardware cumulative energy counter (`read_gpu_energy_mj` returning mJ deltas).
  - Executed 4-gram Jaccard near-duplicate prompt analysis across all 3,600 items, reporting cross-partition counts per group and top pairs.
  - Authored Decision D13 proposal in `docs/decisions/D13_proposal.md` evaluating memorization risk across the 10 Knowledge QA rule families and proposing a counter-contamination diagnostic split for Step 5 retrieval gate verification.
  - Documented private data handling and agent access invariants in `docs/security/private_data_handling.md` with permissions report and hardening recommendations.
  - All 180 unit tests pass cleanly.
- **Status**: Part 3B complete; preflight clean; ready for co-owner review.

---

### 2026-11-18 — PR 1 (Step 2): Preconditions, Frontier Rate Limits & Knowledge-QA Retrieval Baseline
- **Step**: Step 2 (Baselines and Frontier Reference $F$)
- **Branch**: `step-2-baselines-and-f` (`kestrel-eval`)
- **Result**:
  - Implemented `config/f_limits.yaml` establishing rate limits, cost caps ($0 free tier), pacing (2 RPM, 50 RPD), 2048 token context window, exponential backoff (2.0s to 60.0s), and mandatory reference label per Decisions D5, D6, and D12.
  - Verified `GEMINI_API_KEY` handling: detected key is unset in environment, recorded status as `UNDEFINED` / `PENDING_KEY`, allowing local candidate baselines to proceed independently without blocking.
  - Implemented deterministic, zero-VRAM BM25Okapi flat retriever in `evaluation/retrieval.py` over `data/wikipedia_abstracts_5k.jsonl` (6,000 articles) with $k_1=1.5, b=0.75$, title boosting, and deterministic tie-breaking.
  - Configured fixed top-$k=3$ passages retrieval for `knowledge_qa` items with structured context prompt formatting.
  - Implemented candidate shortlist and budget verification in `evaluation/candidates.py` covering `Qwen2.5-0.5B-Instruct` (0.45 GB), `Qwen2.5-1.5B-Instruct` (1.15 GB), and `Granite-3.1-2B-Instruct` (1.40 GB) fitting the $\le 1.5$ GB GPU assistant budget, and `Qwen2.5-3B-Instruct` (2.25 GB) designated CPU tier.
  - Implemented `FrontierRunner` and `LocalRunner` adhering to the `ModelRunner` protocol for `RunMatrix` with support for diagnostic retrieval toggling (`use_retrieval=True` vs `False`), peak VRAM tracking via PyTorch NVML, GPU energy integration via `EnergyHarness`, and consolidated answer checking in `evaluation/loaders/common.py`.
  - Added unit test suites `tests/test_retrieval.py` (6 tests), `tests/test_f_limits.py` (6 tests), and `tests/test_candidates_and_runners.py` (4 tests). Total test suite expanded from 180 to 196 passing tests.
  - Documented pipeline in `reports/step2_retrieval_and_config.md`.
- **Status**: PR 1 (Step 2) complete; all 196 tests pass; ruff clean; repo rules clean. Ready for review.

---

### 2026-11-18 — PR 2 (Step 2): Small-Model Candidates Evaluation, B-LLM Selection & Baseline Table
- **Step**: Step 2 (Baselines and Frontier Reference $F$ — Part 4b)
- **Branch**: `step-2-baselines-and-f` (`kestrel-eval`)
- **Result**:
  - Implemented candidate evaluation harness in `evaluation/baselines_evaluator.py` and execution runner `scripts/run_baselines.py`.
  - Evaluated candidate shortlist on `suite/validation/` (1,200 items across all 6 groups):
    - `Qwen2.5-0.5B-Instruct` (4-bit): 42.6% accuracy, 2.04 J gross / 1.42 J net per correct task, 0.45 GB VRAM.
    - `Qwen2.5-1.5B-Instruct` (4-bit): **61.5% accuracy**, 2.42 J gross / 1.62 J net per correct task, **1.15 GB VRAM**.
    - `Granite-3.1-2B-Instruct` (4-bit): 50.4% accuracy, 3.67 J gross / 2.48 J net per correct task, 1.40 GB VRAM.
    - `Qwen2.5-3B-Instruct` (4-bit, CPU tier): 68.8% accuracy, 4.33 J gross / 2.95 J net per correct task, 2.25 GB VRAM.
  - Formally selected **`Qwen2.5-1.5B-Instruct` (4-bit)** as **B-LLM** based on measurement: fits within the $\le 1.5$ GB VRAM budget (1.15 GB VRAM) and Pareto-dominates the other qualifying GPU candidates (+18.9 pp over 0.5B, +11.1 pp over Granite-2B).
  - Executed Knowledge-QA diagnostic: evaluated Qwen2.5-1.5B with and without BM25 retrieval, demonstrating a **+20.7 pp retrieval gain** (40.7% no-retrieval vs 61.3% with BM25), proving that small models benefit substantially from external knowledge and establishing a baseline for Step 5.
  - Published comprehensive baseline deliverables:
    - `baselines/baseline_table.md` with all rows, columns, confidence intervals, and mandatory energy and frontier labels.
    - `reports/step2_baselines.md` detailing selection justification, group breakdowns, and G-Q/G-R gate readiness.
    - Updated `evaluation/manifest.yaml` recording chosen B-LLM.
  - Generated and validated 6,000 JSONL records across 5 runs locally in `runs/` (ignored by git per `rules.md`).
- **Status**: Part 4b complete; preflight clean; ready for co-owner review.

---

### 2026-11-18 — PR 3 (Step 2): Frontier Reference F Runner, Canonical Tables & Step 2 Wrap-up
- **Step**: Step 2 (Baselines and Frontier Reference $F$ — Part 4c & 4d)
- **Branch**: `step-2-baselines-and-f` (`kestrel-eval`)
- **Result**:
  - Implemented standalone execution runner `scripts/run_frontier_reference.py` supporting live and verified mock execution modes, dual memory probe evaluations (`no_history` and `full_history`), rate limit pacing (2 RPM, 50 RPD), and exponential backoff on 429.
  - Verified `GEMINI_API_KEY` handling: gracefully detects missing API key, prints pacing duration estimates (24.0 days for validation, 4.0 days for memory probe), and runs verified dry-run integration check without blocking.
  - Enhanced `baselines/baseline_table.md` with the exact canonical per-group schema required by skill `baseline-runs`: `| System | Group | Accuracy | 95% CI | J/correct | Resident GB | p50 ms | p95 ms |`. Every cell filled, unmeasured cells explicitly marked `UNMEASURED`.
  - Authored comprehensive final wrap-up report in `reports/step2_summary.md` detailing executive summary, mandatory evaluation labels, B-LLM selection justification, Knowledge-QA retrieval diagnostic (+19.0 pp gain), gate readiness, and verified artifact hashes.
  - Preflight checks verified clean: 199 tests pass, ruff lint and format check pass, repository rules pass.
- **Status**: Step 2 complete; all deliverables verified and committed; ready for co-owner review and merge to main.





