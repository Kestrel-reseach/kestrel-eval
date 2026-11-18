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
  - Canonical 3-repeat idle baseline recorded (pooled mean 8.335 W, std 1.122 W).
  - 3-trial CUDA FP16 GEMM pilot verified (mean unclipped net energy 586.033 J, noise margin 38.24 J, all valid).
  - Non-flaky memory-write assertion verified (<2.0s bounded).
  - Mandatory energy label enforcement tested and active.
- **Status**: Step 0 code and evidence complete. Step 0 remains UNCHECKED in `PLAN.md` pending owner's review and closure note sign-off.
- **Open Issues**:
  - Pending owner decision D12: Step 10 locked-test F run policy (free tier vs paid tier).


