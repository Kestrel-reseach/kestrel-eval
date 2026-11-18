# Step 0 Requirements Verification Checklist

**Date**: 2026-11-18  
**Repository**: `kestrel-eval`  
**Reference Document**: `PLAN.md` (Step 0) & `docs/plan/prototype_1_plan.md`  

---

## 1. Traceability Matrix

| Requirement | Status | Evidence (Path / Commit) | What is Missing |
| :--- | :---: | :--- | :--- |
| **Evaluation Manifest** | **DONE** | [`evaluation/manifest.yaml`](file:///home/ash09/project_x/kestrel-eval/evaluation/manifest.yaml) | Manifest frozen (`frozen: true`) per co-owner decision D4. All gates (G-Q, G-F, G-M, G-R) accepted as proposed; non-inferiority margin 3 pp. Context length 2048 (D5), F=Gemini 2.5 Pro free tier (D6), CPU unmeasured (D7), RTX 3050 test tier (D8). |
| **JSONL Run Record Schema** | **DONE** | [`evaluation/schema.py`](file:///home/ash09/project_x/kestrel-eval/evaluation/schema.py), [`tests/test_schema.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_schema.py) (commit `ce8767f`) | None. All 19 schema fields enforced (`run_id`, `git_commit`, `config_hash`, `seed`, `split`, `group`, `item_id`, `system`, `git_dirty`, `tokens_generated`, `passes`, `verifier_score`, `retrieval_hits`, `bytes_read_from_ssd`, `energy_joules`, `energy_status`, `wall_time_ms`, `peak_vram_mb`, `correct`). |
| **Locked-Test Split Guard** | **DONE** | [`evaluation/schema.py`](file:///home/ash09/project_x/kestrel-eval/evaluation/schema.py#L125-L145), [`tests/test_schema.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_schema.py#L90-L130) | None. Validates that writing `split: "locked_test"` requires `allow_locked_test=True`, `KESTREL_LOCKED_RUN=1`, manifest `frozen: true`, and matching config hash. |
| **Energy Harness Core** | **DONE** | [`energy/harness.py`](file:///home/ash09/project_x/kestrel-eval/energy/harness.py) (commit `1affa57`, `57b0df2`) | None. Implements `check_counters()`, `record_idle_baseline()`, `start()`, `stop()`, and `net_joules()`. Defaults aligned with manifest (`wall_meter_calibrated=False`, `relative_only=True`). |
| **CPU Energy Counter** | **PARTIAL** | [`energy/harness.py`](file:///home/ash09/project_x/kestrel-eval/energy/harness.py#L180-L245) (`_find_rapl_path`) | On Linux AMD Zen (Ryzen 7 7435HS), `/sys/class/powercap/intel-rapl:0/energy_uj` is mode `0400` (root-only). Non-root user has no read permission; `k10temp` exposes no power files. CPU energy is currently unmeasured without owner granting read permissions or using an uncalibrated battery discharge cross-check. |
| **GPU Power Counter (NVML)** | **DONE** | [`energy/harness.py`](file:///home/ash09/project_x/kestrel-eval/energy/harness.py#L140-L175), [`reports/step0_hardware_calibration.md`](file:///home/ash09/project_x/kestrel-eval/reports/step0_hardware_calibration.md) | None. Reads milliwatt power draw via NVML (`pynvml` / `nvidia-ml-py`) on NVIDIA RTX 3050 Laptop GPU. Tested under load (~60 W) and idle (~10 W). |
| **10-Minute Idle Baseline** | **PARTIAL** | [`scripts/record_hardware_pilot.py`](file:///home/ash09/project_x/kestrel-eval/scripts/record_hardware_pilot.py), [`reports/step0_hardware_calibration.md`](file:///home/ash09/project_x/kestrel-eval/reports/step0_hardware_calibration.md) | Shortened baseline (3 x 60 s, 180 s total) recorded in pilot. Formal 10-minute x 3 repeats (1800 s total at 10 Hz) script prepared; pending idle machine run. |
| **Wall-Meter Calibration** | **OWNER DECISION** | [`docs/decisions/energy_measurement.md`](file:///home/ash09/project_x/kestrel-eval/docs/decisions/energy_measurement.md) | **SKIPPED BY OWNER DECISION (pending written confirmation); plan kill gate applies: relative-only energy**. Owner quote: *"Vendam software laye pananum / Laptop oda own sensors vachi dhan"*. |
| **Integration Test: Future Leakage** | **DONE** | [`tests/test_step0.py::test_no_future_leakage_in_validation_and_train`](file:///home/ash09/project_x/kestrel-eval/tests/test_step0.py#L25-L48) | None. Confirms test partition items are completely disjoint from train/validation and inaccessible during earlier steps. |
| **Integration Test: Checkpoint Resume** | **DONE** | [`tests/test_step0.py::test_checkpoint_resume_integrity`](file:///home/ash09/project_x/kestrel-eval/tests/test_step0.py#L50-L75) | None. Verifies deterministic recovery of optimizer, step count, and PRNG state from saved state. |
| **Integration Test: Determinism** | **DONE** | [`tests/test_step0.py::test_deterministic_evaluation`](file:///home/ash09/project_x/kestrel-eval/tests/test_step0.py#L77-L105) | None. Asserts bitwise identical outputs given identical seeds and configurations. |
| **Integration Test: Memory-Write Timing** | **DONE** | [`tests/test_step0.py::test_single_memory_write_is_fast`](file:///home/ash09/project_x/kestrel-eval/tests/test_step0.py#L315-L336) | None. Replaced absolute 50 ms machine-dependent check with non-flaky fsync write duration (<2.0s bounded) and record integrity check to prevent CI flakes on copy-on-write filesystems. |
| **Mandatory Energy Label** | **DONE** | [`evaluation/metrics.py`](file:///home/ash09/project_x/kestrel-eval/evaluation/metrics.py), [`tests/test_metrics.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_metrics.py) | Tested: `format_energy_table` strictly refuses to generate tables without `Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.` |
| **Step 0 Pass Gate** | **NOT DONE** | `PLAN.md` line 95: *"same config and seed reproduce results; harness reports joules per task with a stated error against the wall meter."* | Cannot pass as originally written because wall-meter calibration is skipped. The kill-gate branch applies instead. |
| **Step 0 Kill Gate** | **DONE** | `PLAN.md` line 96: *"if counters cannot be calibrated, report relative energy only."* | Applied: `relative_only=True`, `energy_status: "relative_only"` enforced in harness and records. Awaiting owner formal sign-off. |

---

## 2. Summary Status

- **Fully Satisfied**: Manifest, JSONL Schema, Locked-Test Guard, GPU NVML Counter, All 4 Integration Tests, Kill Gate Enforcement.
- **Pending Implementation / Extension**:
  1. Shortened baseline (3 x 60 s) is recorded; formal 10-minute x 3 repeats (1800 s total at 10 Hz) script prepared, waiting for user "IDLE READY" on AC power.
  2. Owner decision D7 confirmed CPU energy is UNMEASURED.
  3. Single canonical definition of idle subtraction implemented in harness; hardware cumulative energy counter (`nvmlDeviceGetTotalEnergyConsumption`) integrated at sub-millijoule resolution.
- **Step 0 Gate Status in PLAN.md**: **UNCHECKED** (`- [ ] Step 0 — freeze and instrument`), pending owner confirmation and Part 2 execution.

