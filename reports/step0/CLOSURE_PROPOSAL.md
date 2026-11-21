# Step 0 Closure Proposal — For Owner Review & Formal Sign-Off

**Date**: 2026-11-18  
**Repository**: `kestrel-eval`  
**Reference Document**: `PLAN.md` (Step 0) & `docs/plan/prototype_1_plan.md`  
**Status**: `PENDING OWNER FORMAL SIGN-OFF` *(Do NOT tick Step 0 in PLAN.md; only the owner ticks it)*

---

## 1. Executive Summary

This proposal summarizes the implementation and experimental status of **Step 0 (Freeze and Instrument)** for Project Kestrel Prototype 1 under the **relative-only energy measurement path**.

Per the project owner's decision relayed on 2026-11-18 (*"Vendam software laye pananum / Laptop oda own sensors vachi dhan"*), physical wall meter calibration is skipped. The **Step 0 Kill Gate** (`PLAN.md` line 96) has been formally applied across the repository.

---

## 2. What is DONE

1. **Evaluation Manifest (`evaluation/manifest.yaml`)**:
   - Split seeds, partition sizes (math 200, science 200, knowledge MCQ 300, code 100, store QA 300, memory probe 100), budgets, and hardware cards frozen in schema.
   - Status of `frozen` flag: Set to `frozen: true` (version `1.1`) per co-owner decision D4. Non-inferiority margin confirmed at 3 pp.
2. **Evaluation JSONL Schema (`evaluation/schema.py`)**:
   - Enforces all 19 schema fields.
   - Validates that item evaluation records require `run_id`, `git_commit`, `config_hash`, `seed`, `split`, `group`, `item_id`, `system`, `git_dirty`, `tokens_generated`, `passes`, `verifier_score`, `retrieval_hits`, `bytes_read_from_ssd`, `energy_joules`, `energy_status`, `wall_time_ms`, `peak_vram_mb`, `correct`.
3. **Locked-Test Guard**:
   - Protects the locked evaluation partition. Any attempt to write or evaluate `split: "locked_test"` requires `allow_locked_test=True`, environment variable `KESTREL_LOCKED_RUN=1`, `manifest.frozen=True`, and a matching config hash.
4. **Energy Harness (`energy/harness.py`)**:
   - Primary gross GPU energy measurement via hardware cumulative total-energy counter `nvmlDeviceGetTotalEnergyConsumption()` in millijoules (tested on RTX 3050 Laptop GPU).
   - High-frequency 10 Hz idle baseline sampling (`sample_interval_s=0.1`) with persistent NVML handle.
   - Default configuration aligned with manifest (`wall_meter_calibrated=False`, `relative_only=True`).
   - Formal 10-minute x 3 repeats idle baseline (1800 s total, 17,943 samples at 10.0 Hz) completed: pooled mean $P_{\text{idle}} = 6.1444\text{ W}$, $\sigma_{\text{idle}} = 0.9472\text{ W}$, counter-derived power $6.1686\text{ W}$ ([`formal_idle_baseline.json`](reports/step0/formal_idle_baseline.json)).
   - Supports unclipped net energy calculation ($E_{\text{net}} = E_{\text{gross}} - P_{\text{idle}} \times \Delta t$) with $3\sigma$ noise margin verification.
5. **Mandatory Energy Label Enforcement**:
   - Enforced by programmatic assertion in `evaluation/metrics.py` and unit tests in `tests/test_metrics.py`. The report generator strictly refuses to format energy tables without:  
     `"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."`
6. **All 4 Step 0 Integration Tests**:
   - No-future-leakage (`test_no_future_leakage_in_validation_and_train`).
   - Checkpoint resume integrity (`test_checkpoint_resume_integrity`).
   - Bitwise deterministic evaluation (`test_deterministic_evaluation`).
   - Memory-write non-flaky fsync timing and ordering (`test_single_memory_write_is_fast`).

---

## 3. What is Closed by Owner Decision (Step 0 Kill Gate)

1. **Wall Power Meter Skipped**:
   - No plug-in wall power meter is used.
2. **Relative Energy Only**:
   - Per `PLAN.md` line 96: *"Kill: if counters cannot be calibrated, report relative energy only."*
   - All energy metrics throughout Prototype 1 are classified as `energy_status: "relative_only"`.
   - The Step 0 pass condition requiring a stated error margin against a wall meter is replaced by the kill gate rule.

---

## 4. What Stays UNMEASURED

1. **CPU Energy Counter**:
   - On Linux AMD Zen (Ryzen 7 7435HS), `/sys/class/powercap/intel-rapl:0/energy_uj` is mode `0400` (root-only). Non-root processes receive `PermissionError`.
   - `k10temp` exposes thermal sensors only, with no energy/power sysfs files.
   - CPU energy is **unmeasured** in unprivileged user space unless the owner grants read permissions (Decision D7, Option b).
2. **CPU-Tier Baseline Energy**:
   - Runs executed on the CPU tier (e.g. larger quantized models or CPU-only baselines) report accuracy, latency, and memory, but **no energy figures**.

---

## 5. Claims That Are STRICTLY DISALLOWED

To maintain absolute scientific integrity, the following claims are **prohibited** across all papers, reports, PRs, and presentations:
1. **No Absolute Joule Claims**:
   - We cannot claim absolute energy consumption (e.g. "P1 uses X Joules from the wall outlet").
2. **No Cross-Machine Comparisons**:
   - Energy numbers cannot be compared across different physical machines, different driver revisions, or different power plans.
   - Comparisons are valid **only** between P1 and baselines executed on the **same machine, same power plan, and same session**.
3. **No CPU-Path Energy Claims**:
   - Energy cannot be reported for CPU execution paths while RAPL remains root-restricted.
4. **No Energy Attribution to Frontier Model F**:
   - F is an external API; its internal physical energy consumption is unmeasured and cannot be compared against local joule figures.

---

## 6. Actions Required from Co-Owners to Formally Close Step 0

Decisions D1–D11 have been recorded in [`docs/decisions/owner_decisions.md`](docs/decisions/owner_decisions.md).
Step 0 is closed with the following documented deviations:
- **Formal idle baseline completed** (1,800.00 s total at 10.0 Hz, 17,943 samples; shortened baseline deviation resolved)
- **Unmeasured CPU energy** (GPU NVML relative energy only, per D7)
- **Test hardware tier** (RTX 3050 Laptop 4 GB / Ryzen 7 7435HS, per D8)
- **No physical wall meter** (software-only relative energy, per D8)

Once confirmed by co-owners, the **owners tick Step 0** in `PLAN.md`:
```markdown
- [x] Step 0 — freeze and instrument (closed with deviations: unmeasured CPU energy, 3050 tier, no wall meter)
```

