# Step 0 Hardware Calibration & Measurement Pilot Report

**Date**: 2026-11-18
**Host Identification**:
- **CPU**: AMD Ryzen 7 7435HS (16 vCPUs, 8 cores, 16 threads)
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4,096 MiB VRAM, UUID `REDACTED`)
- **NVIDIA Driver**: 615.78.08 | **CUDA**: 13.4
- **OS / Kernel**: Linux 7.2.9-zen1-1-zen (x86_64)

---

## 1. Target Hardware Tier Status

| Parameter | PLAN.md Target Tier | Measured Test Machine | Status |
| :--- | :--- | :--- | :--- |
| **CPU** | AMD Ryzen 7 5800H | AMD Ryzen 7 7435HS | **Hardware Variant** (Zen 3+ vs Zen 3) |
| **GPU Model** | NVIDIA GeForce RTX 3060 Laptop | NVIDIA GeForce RTX 3050 Laptop | **PENDING OWNER CONFIRMATION** (`docs/decisions/hardware_tier.md`) |
| **GPU VRAM** | 6.0 GB (1.0–1.5 GB assistant budget) | 4.0 GB (4,096 MiB) | Budget accommodated |
| **Power Target** | ~60–80 W TGP tier | 35–60 W dynamic TGP tier | Calibrated in pilot |

> [!WARNING]
> **Results obtained on the RTX 3050 Laptop GPU (4 GB) are NOT transferable to the RTX 3060 tier.**
> As documented in [`docs/decisions/hardware_tier.md`](file:///home/ash09/project_x/kestrel-eval/docs/decisions/hardware_tier.md), the RTX 3050 tier acceptance was agent-drafted and merged by Member B without a written record authored by the owner. It remains `PENDING OWNER CONFIRMATION` in writing (Decision D8).
> **Step 0 in `PLAN.md` remains strictly UNCHECKED** until owner confirmation is provided.

---

## 2. Hardware Counter Discovery (`check_counters`)

Raw output of `check_counters(strict=True)`:
```json
{
  "cpu_available": false,
  "cpu_counter_source": "none",
  "energy_status": "relative_only",
  "gpu_nvml_available": true,
  "relative_only": true,
  "wall_meter_calibrated": false
}
```

### Analysis of Counter Sources:
1. **CPU Counter (`cpu_counter_source: 'none'`)**:
   - `/sys/class/powercap/intel-rapl` exists on this system, but its child node `intel-rapl:0/energy_uj` has permissions `0400` (`-r--------` owned by root). Regular non-root users encounter `PermissionError`.
   - `/sys/class/hwmon/hwmon4` (`k10temp`) exposes temperature, not `power*_average` sysfs files.
   - Therefore, CPU energy is truthfully reported as `None` in user space without elevated privileges or a setuid helper (Decision D7).
2. **GPU Counter (`gpu_nvml_available: True`)**:
   - Discovered and read via `pynvml` (`nvidia-ml-py==13.615.71`).
   - Accurately tracks milliwatt power draw across dynamic P-states.
3. **Status Defaults**:
   - `wall_meter_calibrated`: `false` (aligned with `manifest.yaml` line 171 and Decision Record `docs/decisions/energy_measurement.md`).
   - `relative_only`: `true` (relative energy only; uncalibrated against wall meter per Step 0 Kill Gate).
   - `energy_status`: `"relative_only"`.

---

## 3. Canonical Idle Baseline Measurement (`record_idle_baseline`)

Idle baseline was sampled across 3 repeated intervals under the same AC power plan:
- **Repeat 1**: 60.0 s | Mean GPU power: 8.689 W (std: 1.649 W)
- **Repeat 2**: 60.0 s | Mean GPU power: 8.281 W (std: 1.024 W)
- **Repeat 3**: 60.0 s | Mean GPU power: 8.036 W (std: 0.082 W)

### Canonical Pooled Idle Parameters:
- **Total Duration Sampled**: 180.1 seconds (174 samples)
- **Canonical Mean Idle Power ($P_{\text{idle}}$)**: **8.335 W**
- **Pooled Idle Standard Deviation ($\sigma_{\text{idle}}$)**: **1.122 W**
- **Canonical Definition**: Single pooled mean sample rate is used for all idle energy subtractions. Competing sampling windows are eliminated.

---

## 4. Workload Measurement & 3-Trial Repeatability

Workload executed: Continuous FP16 Matrix Multiplication ($2048 \times 2048$) on `cuda:0` using PyTorch.

> [!IMPORTANT]
> Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.

| Trial | Duration (s) | Gross Energy (J) | Gross Power (W) | Idle Energy (J) | Unclipped Net Energy (J) | Noise Margin (3σ) (J) | Valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11.409 | 683.77 | 59.93 | 95.10 | **588.67** | 38.40 | **PASS** |
| 2 | 11.422 | 684.03 | 59.89 | 95.20 | **588.83** | 38.44 | **PASS** |
| 3 | 11.257 | 674.43 | 59.91 | 93.83 | **580.60** | 37.89 | **PASS** |
| **Mean** | 11.362 | 680.74 | 59.91 | 94.71 | **586.03** | 38.24 | **PASS** |

### Unclipped Net Energy & Noise Rule:
- Noise criterion: A workload run is valid if $E_{\text{net}} > 0$ and $E_{\text{net}} > 3 \times \sigma_{\text{idle}} \times \Delta t$.
- In all 3 trials and on average, gross power was ~59.9 W, gross energy was ~680.7 J over 11.4 s.
- Idle energy was 94.7 J (at 8.335 W idle).
- Unclipped net energy was **586.03 J**, exceeding the $3\sigma$ noise margin (38.24 J) by more than 8×.
- All 3 trials and the mean are marked **PASS**.

---

## 5. Schema-Validated JSONL Measurement Record

The mean run produced the following schema-validated record in `reports/step0_hardware_calibration.jsonl`:
```json
{
  "run_id": "run-step0-pilot-hw-20261118",
  "git_commit": "1b4d53cb16a4f89d380726d152504b8feec85741",
  "config_hash": "ede58c9263678994d3493ca9122718ba873252ce6b904baf52f941d2bd357a74",
  "seed": 42,
  "split": "validation",
  "group": "pilot_hardware_calibration",
  "item_id": "calib-item-001",
  "system": "P1",
  "git_dirty": false,
  "tokens_generated": 0,
  "passes": 1,
  "verifier_score": null,
  "retrieval_hits": 0,
  "bytes_read_from_ssd": 0,
  "energy_joules": 586.033,
  "energy_status": "relative_only",
  "wall_time_ms": 11362.37,
  "peak_vram_mb": 40.12,
  "correct": true
}
```

### Measured vs Placeholder Field Breakdown:
| Category | Fields | Description / Value |
| :--- | :--- | :--- |
| **Measured Fields** | `energy_joules` | **586.033 J** (mean unclipped net GPU energy) |
| | `wall_time_ms` | **11362.37 ms** (mean duration) |
| | `peak_vram_mb` | **40.12 MB** (resident CUDA memory) |
| | `energy_status` | `"relative_only"` (measured uncalibrated software counter) |
| **Metadata Fields** | `run_id`, `git_commit`, `config_hash`, `seed`, `split`, `group`, `item_id`, `git_dirty` | Run tracking provenance |
| **Schema-Required Placeholders** | `system: "P1"` | Required by schema; placeholder for hardware pilot |
| | `correct: true` | Required by schema; placeholder (no QA question solved) |
| | `verifier_score: null` | Explicitly nullable; null indicates no verification task |
| | `passes: 1` | Default single pass |
| | `tokens_generated: 0` | Hardware pilot generated zero LLM tokens |
| | `retrieval_hits: 0` | No SSD retrieval performed |
| | `bytes_read_from_ssd: 0` | No SSD index accessed |
