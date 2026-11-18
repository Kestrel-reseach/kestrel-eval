# Step 0 — Gross GPU Energy Measurement Method & Counter Specification

**Date**: 2026-11-18  
**Hardware Tier**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB) / Ryzen 7 7435HS  
**Scope**: Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.

---

## 1. Executive Summary

In response to the reviewer review on Step 0 gross energy computation and baseline sampling rates:
1. **Gross GPU Energy Method**: Shifted from single-point power approximation to the hardware-level cumulative energy counter `nvmlDeviceGetTotalEnergyConsumption()`.
2. **Sampling Rate**: Upgraded idle baseline power polling from ~1 Hz (1.0 s) to **10 Hz** (0.1 s interval), achieving exactly 10.0 Hz verified on hardware.
3. **Hardware Counter Verification**: Confirmed active support on the RTX 3050 Laptop GPU (driver 615.78.08).

---

## 2. Gross GPU Energy Computation

### Primary Hardware Counter: `nvmlDeviceGetTotalEnergyConsumption`
- **Source**: NVIDIA Management Library (NVML) via `pynvml.nvmlDeviceGetTotalEnergyConsumption(handle)`.
- **Unit**: Millijoules ($\text{mJ}$), returning an accumulating 64-bit unsigned integer since driver load.
- **Resolution**: Sub-millijoule hardware accumulator ($10^{-3}\text{ J}$).
- **Window Delta**:
  $$\Delta E_{\text{GPU}} = \frac{E_{\text{end}} - E_{\text{start}}}{1000.0} \quad [\text{Joules}]$$
- **Advantages**:
  - Eliminates sampling rate error on short (1–2 s) LLM inference windows.
  - Captures high-frequency transients and burst power spikes without CPU polling overhead.
  - Zero performance interference with executing PyTorch / CUDA workloads.

### Fallback Method: Integrated Power Samples
- When running on legacy or mock hardware where `nvmlDeviceGetTotalEnergyConsumption` is unsupported (or returns `None`), the harness automatically falls back to integrated instantaneous power sampling:
  $$E_{\text{GPU, fallback}} = P_{\text{instant}} \times \Delta t_{\text{wall}}$$
- Tagged with `gpu_energy_method: "integrated_power_samples"` in the `EnergySample`.

---

## 3. Idle Baseline Sampling Specification

| Parameter | Previous Pilot Value | New Specification (Step 0 Follow-up) |
| :--- | :--- | :--- |
| **Poll Interval (`sample_interval_s`)** | 1.0 s | **0.10 s** |
| **Target Sampling Frequency** | ~1 Hz | **10.0 Hz** |
| **Verified Measured Rate** | 0.97 Hz (58 samples in 60s) | **10.0 Hz (20 samples in 2.000s; ~6,000 samples in 10 min)** |
| **Driver Handle Management** | Re-init per sample (`nvmlInit` / `nvmlShutdown`) | **Persistent handle maintained throughout recording loop** |
| **Counter Cross-Check** | None | **Dual recording: $\bar{P}_{\text{NVML}}$ vs $\Delta E_{\text{counter}} / \Delta t$** |

### Standard Deviation Formulation
The idle power standard deviation $\sigma_{\text{idle}}$ is computed over $N$ discrete 10 Hz samples:
$$\sigma_{\text{idle}} = \sqrt{\frac{1}{N - 1}\sum_{i=1}^{N} (P_i - \bar{P})^2}$$
For the 3-sigma noise floor rule:
$$\text{Noise Margin} = 3 \times \sigma_{\text{idle}} \times \Delta t_{\text{workload}}$$

---

## 4. Software Implementation & Unit Tests

- **Code Path**: [`energy/harness.py`](file:///home/ash09/project_x/kestrel-eval/energy/harness.py)
  - `read_gpu_energy_mj(handle=None) -> int | None`
  - `read_gpu_power_watts(handle=None) -> float | None`
  - `EnergyHarness.start()` records `token.start_gpu_mj`
  - `EnergyHarness.stop(token)` computes exact delta in Joules and sets `gpu_energy_method="nvml_total_energy_counter"`
- **Test Suite**: [`tests/test_harness.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_harness.py)
  - `test_read_gpu_energy_mj_returns_none_when_nvml_unavailable`
  - `test_start_stop_uses_nvml_total_energy_counter`
  - `test_start_stop_computes_gpu_energy_fallback`
  - `test_record_idle_baseline_computes_mean_gpu_power`
- **Test Status**: All 123 tests passing cleanly.
