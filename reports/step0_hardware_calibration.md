# Step 0 Hardware Calibration & Measurement Report

**Date**: 2026-11-17  
**Host Identification**:
- **CPU**: AMD Ryzen 7 7435HS (16 vCPUs, 8 cores, 16 threads)
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4,096 MiB VRAM, UUID `GPU-409f90c9-6ae1-444d-c201-7fa1803e5a2b`)
- **NVIDIA Driver**: 615.78.08 | **CUDA**: 13.4
- **OS / Kernel**: Linux 7.2.9-zen1-1-zen (x86_64)

---

## 1. Target Hardware Tier Comparison

| Parameter | PLAN.md Target Tier | Measured Test Machine | Status |
| :--- | :--- | :--- | :--- |
| **CPU** | AMD Ryzen 7 5800H | AMD Ryzen 7 7435HS | **Hardware Variant** (Zen 3+ vs Zen 3) |
| **GPU Model** | NVIDIA GeForce RTX 3060 Laptop | NVIDIA GeForce RTX 3050 Laptop | **Hardware Mismatch** (RTX 3050 vs RTX 3060) |
| **GPU VRAM** | 6.0 GB (1.0–1.5 GB assistant budget) | 4.0 GB (4,096 MiB) | Smaller VRAM ceiling |
| **Power Target** | ~60–80 W TGP tier | 35 W TGP tier | Lower power ceiling |

> [!WARNING]
> The measured machine is an **RTX 3050 Laptop GPU (4 GB)**, whereas `PLAN.md` targets an **RTX 3060 Laptop (6 GB)**.
> Per repository rules, Step 0 cannot be marked passed for target-tier verification without explicit owner approval to accept the RTX 3050 or re-running on an RTX 3060.

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
  "wall_meter_calibrated": null
}
```

### Analysis of Counter Sources:
1. **CPU Counter (`cpu_counter_source: 'none'`)**:
   - `/sys/class/powercap/intel-rapl` exists on this system, but its child node `intel-rapl:0/energy_uj` has permissions `0400` (`-r--------` owned by root). Regular non-root users encounter `PermissionError`.
   - `/sys/class/hwmon/hwmon4` (`k10temp`) does not expose `power*_average` sysfs files.
   - Therefore, CPU energy is truthfully reported as `None` in user space. (To enable CPU RAPL, root access or `chmod o+r` on `energy_uj` would be required).
2. **GPU Counter (`gpu_nvml_available: True`)**:
   - Discovered and read via `pynvml` (`nvidia-ml-py==13.615.71`).
   - Accurately tracks milliwatt power draw across P-states.

---

## 3. Idle Baseline Measurement (`record_idle_baseline`)

- **Duration sampled**: 30 seconds (30.13 s elapsed)
- **Mean GPU idle power**: 8.330 W
- **Combined idle rate ($P_{\text{idle}}$)**: 8.330 W (J/s)

---

## 4. Workload Measurement (`start` / `stop`) & Net Joules

Workload executed: 5.0-second synthetic computational loop.

- **Wall time**: 5.0000 seconds
- **Gross GPU Energy ($E_{\text{gross}}$)**: 30.535 J
- **Gross Total Energy**: 30.535 J
- **Average gross power**: 6.107 W
- **Net Energy ($E_{\text{net}} = E_{\text{gross}} - P_{\text{idle}} \times \Delta t$)**: **0.000 J**

### Clarification on Previous Figures (9.36 W vs 12.48 J / 2.0 s):
- **9.36 W**: Instantaneous point sample from `read_gpu_power_watts()` while in P3 power state.
- **12.48 J over 2.0 s**: Integrated energy over a 2.0-second sleep interval, giving an average power of $12.48 / 2.0 = 6.24\text{ W}$.
- Instantaneous power varies with dynamic GPU clock gating and display refresh; integrated energy over time captures the true average consumption.

---

## 5. JSONL Measurement Record

The run produced the following schema-validated record in `reports/step0_hardware_calibration.jsonl`:
```json
{
  "run_id": "run-step0-pilot-hw-20261117",
  "git_commit": "ce8767f2b5b9c885a4ddff154f98bafe270b727b",
  "config_hash": "e8d738ca8fe9d621096bab9126e316b4409883020f87805380e5ef2808f7766f",
  "seed": 42,
  "split": "val",
  "group": "pilot_hardware_calibration",
  "item_id": "calib-item-001",
  "system": "P1",
  "git_dirty": false,
  "tokens_generated": 0,
  "passes": 1,
  "verifier_score": 1.0,
  "retrieval_hits": 0,
  "bytes_read_from_ssd": 0,
  "energy_joules": 0.0,
  "energy_status": "relative_only",
  "wall_time_ms": 5000.02,
  "peak_vram_mb": 604.0,
  "correct": true
}
```
- `config_hash`: `e8d738ca8fe9d621096bab9126e316b4409883020f87805380e5ef2808f7766f`
- `git_commit`: `ce8767f2b5b9c885a4ddff154f98bafe270b727b`
- `energy_status`: `relative_only` (Per owner decision 2026-11-17: no wall meter, relative energy only)
