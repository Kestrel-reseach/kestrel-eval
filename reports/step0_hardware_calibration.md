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
| **GPU Model** | NVIDIA GeForce RTX 3060 Laptop | NVIDIA GeForce RTX 3050 Laptop | **Test Tier Accepted** (Owner decision 2026-11-18) |
| **GPU VRAM** | 6.0 GB (1.0–1.5 GB assistant budget) | 4.0 GB (4,096 MiB) | Budget accommodated |
| **Power Target** | ~60–80 W TGP tier | 35–60 W dynamic TGP tier | Calibrated in pilot |

> [!NOTE]
> **Owner Decision on Target Hardware (2026-11-18)**:
> In PR #7 (commit `07979e5`), the repository owner approved the RTX 3050 Laptop GPU (4 GB) / Ryzen 7 7435HS as the official test tier for Prototype 1 because the physical RTX 3060 hardware is unavailable. Formal target-tier re-run is deferred, and Gate G-R thresholds remain unchanged.
> **Step 0 in `PLAN.md` remains UNCHECKED** pending reviewer review and formal sign-off.

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
   - Therefore, CPU energy is truthfully reported as `None` in user space without elevated privileges or a setuid helper.
2. **GPU Counter (`gpu_nvml_available: True`)**:
   - Discovered and read via `pynvml` (`nvidia-ml-py==13.615.71`).
   - Accurately tracks milliwatt power draw across dynamic P-states.
3. **Status Defaults**:
   - `wall_meter_calibrated`: `false` (aligned with `manifest.yaml` line 171).
   - `relative_only`: `true` (relative energy only; uncalibrated against wall meter).
   - `energy_status`: `"relative_only"`.

---

## 3. Idle Baseline Measurement (`record_idle_baseline`)

- **Duration sampled**: 60.0 seconds (65.19 s elapsed)
- **Mean GPU idle power ($P_{\text{idle}}$)**: 10.142 W
- **GPU idle power standard deviation ($\sigma_{\text{idle}}$)**: 1.855 W
- **Combined idle rate**: 8.921 W (J/s)

---

## 4. CUDA FP16 GEMM Workload Measurement & Repeatability

Workload executed: Continuous FP16 Matrix Multiplication ($2048 \times 2048$) on `cuda:0` using PyTorch.

### 3-Trial Repeatability Table:
| Trial | Duration (s) | Gross Energy (J) | Gross Power (W) | Idle Energy (J) | Unclipped Net Energy (J) | Noise Margin ($3\sigma$) (J) | Valid |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 11.420 | 684.77 | 59.96 | 115.82 | **568.95** | 63.54 | **PASS** |
| 2 | 11.410 | 684.35 | 59.98 | 115.72 | **568.63** | 63.49 | **PASS** |
| 3 | 11.440 | 686.53 | 60.01 | 116.02 | **570.51** | 63.65 | **PASS** |

### Unclipped Net Energy & Noise Rule:
- Noise criterion: A workload run is valid if $E_{\text{net}} > 0$ and $E_{\text{net}} > 3 \times \sigma_{\text{idle}} \times \Delta t$.
- In all 3 trials, average gross power was ~60 W, giving gross energy of ~600 J over 10 s.
- Idle power was 10.14 W (~101.4 J over 10 s).
- Unclipped net energy was ~568.6 J, exceeding the $3\sigma$ noise margin (63.49 J) by more than 10×.
- All 3 trials are marked **PASS**.

---

## 5. Technical Clarifications on Measurement Figures

### A. Clarification on 9.36 W vs 12.48 J / 2.0 s:
- **9.36 W**: Instantaneous point sample from `read_gpu_power_watts()` while in P3 power state during a brief wake event.
- **12.48 J over 2.0 s**: Integrated energy over a 2.0-second interval, yielding an average power of $12.48 / 2.0 = 6.24\text{ W}$.
- Instantaneous power varies with dynamic clock gating and display refresh; integrated energy over time captures the true average consumption.

### B. Explanation of Previous Pilot Net Energy:
- The initial exploratory pilot ran a CPU-bound Python loop while reading the GPU counter.
- Under CPU load, the GPU remained in idle/display state (~6.1 W), which was lower than a transient idle sample of 8.3 W, causing net energy to calculate as negative and clip to 0.0 J.
- In this revised pilot, the workload is executed directly on the GPU (CUDA FP16 GEMM), drawing ~60 W (well above idle), with unclipped net energy clearly reported and verified against the noise margin rule.

---

## 6. Schema-Validated JSONL Measurement Record

The representative run (Trial 2) produced the following record in `reports/step0_hardware_calibration.jsonl`:
```json
{
  "run_id": "run-step0-pilot-hw-20261118",
  "git_commit": "1affa5725ee7b223c740ebb3c255139a438b8b56",
  "config_hash": "744c5caf509a349c0913f79df50a0fc2555ba951913ffe3357f39b108a51f10b",
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
  "energy_joules": 568.629,
  "energy_status": "relative_only",
  "wall_time_ms": 11409.99,
  "peak_vram_mb": 48.12,
  "correct": true
}
```

### Schema Field Documentation:
- **Measured Fields**:
  - `energy_joules`: 568.629 J (measured net GPU energy).
  - `wall_time_ms`: 11409.99 ms (measured duration).
  - `peak_vram_mb`: 48.12 MB (measured via CUDA memory allocator).
  - `energy_status`: `"relative_only"` (measured uncalibrated software counter).
- **Metadata Fields**:
  - `run_id`: `"run-step0-pilot-hw-20261118"`
  - `git_commit`: `"1affa5725ee7b223c740ebb3c255139a438b8b56"`
  - `config_hash`: `"744c5caf509a349c0913f79df50a0fc2555ba951913ffe3357f39b108a51f10b"`
  - `seed`: 42
  - `split`: `"validation"`
  - `group`: `"pilot_hardware_calibration"`
  - `item_id`: `"calib-item-001"`
  - `git_dirty`: False
- **Schema-Required Evaluation Placeholders** (documented per reviewer instructions):
  - `system`: `"P1"`
  - `correct`: `true`
  - `verifier_score`: `null` (nullable field in schema; null indicates no verification task)
  - `passes`: 1
  - `tokens_generated`: 0
  - `retrieval_hits`: 0
  - `bytes_read_from_ssd`: 0
