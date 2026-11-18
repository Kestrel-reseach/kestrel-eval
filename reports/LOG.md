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
