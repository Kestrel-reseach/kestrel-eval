# Step 0 Read-Only Power Sensor Discovery Report

**Date**: 2026-11-18  
**Host Machine**: ASUS Laptop (AMD Ryzen 7 7435HS + NVIDIA GeForce RTX 3050 Laptop GPU)  
**Linux Kernel**: 7.2.9-zen1-1-zen (x86_64)  
**Methodology**: Read-only scan of `/sys/class/powercap`, `/sys/class/hwmon`, `/sys/class/power_supply`, and NVML APIs without root privileges (`BypassSandbox: false`). System state modified: **NONE (Change nothing)**.

---

## 1. Power Sensor Inventory Table

| Subsystem / Driver | Path / Interface | Readable Without Root? | Sample Value | Native Unit | Effective Rate / Resolution |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **RAPL (Package-0)** | `/sys/class/powercap/intel-rapl:0/energy_uj` | **NO** (mode `0400`, root:root) | `[Permission denied]` | $\mu\text{J}$ (microjoules) | ~1 ms MSR hardware accumulator |
| **RAPL (Package-0 Max Range)** | `/sys/class/powercap/intel-rapl:0/max_energy_range_uj` | **YES** (mode `0444`) | `65532610987` | $\mu\text{J}$ (~65.53 kJ) | Static rollover constant |
| **RAPL (Package-0 Name)** | `/sys/class/powercap/intel-rapl:0/name` | **YES** (mode `0444`) | `package-0` | text | Static string |
| **RAPL (Package-0 Enabled)** | `/sys/class/powercap/intel-rapl:0/enabled` | **YES** (mode `0644`) | `0` | boolean | Control attribute |
| **RAPL (Core-0)** | `/sys/class/powercap/intel-rapl:0:0/energy_uj` | **NO** (mode `0400`, root:root) | `[Permission denied]` | $\mu\text{J}$ (microjoules) | ~1 ms MSR hardware accumulator |
| **RAPL (Core-0 Name)** | `/sys/class/powercap/intel-rapl:0:0/name` | **YES** (mode `0444`) | `core` | text | Static string |
| **hwmon4 (k10temp)** | `/sys/class/hwmon/hwmon4/` | **YES** (thermal only) | No `power*` or `energy*` files exposed | N/A | Thermal only (`temp1_input` ~54°C) |
| **hwmon2 (BAT1)** | `/sys/class/hwmon/hwmon2/curr1_input` | **YES** (mode `0444`) | `844000` | $\mu\text{A}$ (microamperes) | ~1 Hz (EC/ACPI polling) |
| **hwmon8 (USBC)** | `/sys/class/hwmon/hwmon8/curr1_input` | **YES** (mode `0444`) | `3000000` | $\mu\text{A}$ (3.0 A) | Static / negotiation state |
| **amdgpu hwmon** | `/sys/class/hwmon/` (amdgpu) | **N/A** (Does not exist) | Hardware has no iGPU | N/A | SoC is Ryzen 7 7435HS (no Radeon iGPU die) |
| **power_supply (ACAD)** | `/sys/class/power_supply/ACAD/online` | **YES** (mode `0444`) | `1` | boolean | ACPI event (Mains connected) |
| **power_supply (BAT1 Status)**| `/sys/class/power_supply/BAT1/status` | **YES** (mode `0444`) | `Charging` | string | ACPI state update (~1 Hz) |
| **power_supply (BAT1 Voltage)**| `/sys/class/power_supply/BAT1/voltage_now` | **YES** (mode `0444`) | `12575000` | $\mu\text{V}$ (12.575 V) | ~1 Hz (EC battery gauge) |
| **power_supply (BAT1 Current)**| `/sys/class/power_supply/BAT1/current_now` | **YES** (mode `0444`) | `844000` | $\mu\text{A}$ (0.844 A) | ~1 Hz (Battery charging current on AC) |
| **power_supply (BAT1 Power)** | `/sys/class/power_supply/BAT1/power_now` | **NO** (File does not exist) | Not provided by ACPI | N/A | Must be calculated as $V \times I$ |
| **NVIDIA NVML** | NVML API via `nvidia-ml-py` (`nvmlDeviceGetPowerUsage`) | **YES** (unprivileged access) | `8099` mW (idle) to `60019` mW (load) | milliwatts (`mW`) | ~10–100 Hz polling (~100 ms sensor filter) |

---

## 2. In-Depth Subsystem Analysis

### 1. Powercap / Intel-RAPL Subsystem
- **Kernel interface**: Linux `intel_rapl_common` driver exposes powercap sysfs nodes for AMD Zen CPUs (MSR interface `MSR_RAPL_PWR_UNIT`, `MSR_PKG_ENERGY_STATUS`).
- **Security constraint**: Modern Linux distributions restrict `energy_uj` access to mode `0400` (`-r--------` owned by `root:root`) to protect against side-channel power attacks (e.g., PLATYPUS, CVE-2020-8694).
- **Normal user access**: Non-root processes receive `PermissionError: [Errno 13] Permission denied`. User-space measurement cannot read CPU RAPL energy counters without privilege modification or elevated helpers.

### 2. HWMON Subsystem
- The AMD CPU thermal sensor driver (`k10temp`) at `hwmon4` exposes only temperature metrics (`temp1_input`, `temp3_input`). It does **not** expose power (`power1_average`) or energy registers on this processor family.
- There is **no amdgpu hwmon** instance because the Ryzen 7 7435HS processor variant lacks integrated Radeon graphics silicon.

### 3. Power Supply Subsystem (`/sys/class/power_supply`)
- `ACAD` reports `online: 1` when connected to AC mains power.
- `BAT1` reports battery metrics via ACPI EC:
  - `voltage_now`: $12.575\text{ V}$.
  - `current_now`: $0.844\text{ A}$.
  - When the laptop is connected to AC power, this current represents **battery charging current**, not host computational consumption.
  - If operated on DC battery power, $V \times I$ reflects overall system discharge power (CPU + GPU + screen + SSD + fans), but at a coarse ~1 Hz update rate and under altered power-management throttling profiles.

### 4. NVIDIA Management Library (NVML)
- Accessible without root privileges to any standard user.
- Discovers `NVIDIA GeForce RTX 3050 Laptop GPU`.
- Accurately reports real-time instantaneous power consumption in milliwatts.
- Sampled successfully:
  - Idle baseline: ~8.1 W to 10.1 W.
  - CUDA FP16 GEMM load: ~60.0 W.
- Update frequency is high (~10–100 Hz), suitable for integrating energy over task windows.

---

## 3. Options for CPU Energy Measurement for Owner Choice

*(Presented for owner decision only; no choice is selected by the agent)*

| Option | Implementation Mechanism | Advantages | Disadvantages / Trade-offs |
| :--- | :--- | :--- | :--- |
| **Option (a)** | **Leave CPU energy UNMEASURED** and restrict energy claims strictly to GPU-tier runs. | Zero system modifications; 100% compliant with standard user-space boundaries; completely safe. | CPU-only baseline inference (CPU tier) cannot report joules per task; energy claims are scoped exclusively to GPU runs. |
| **Option (b)** | **Owner grants read permission on RAPL** (`chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj` or setuid helper). | Unlocks high-precision (~1 ms) hardware CPU energy counter across package and cores. | Requires local root administrative action by the owner; permissions may revert on reboot unless udev rule is installed; exposes system to side-channel power measurement. |
| **Option (c)** | **Battery-discharge cross-check** (run benchmarks on battery power reading `/sys/class/power_supply/BAT1/current_now` $\times$ `voltage_now`). | Readable without root; captures whole-system energy (CPU + GPU + platform). | Coarse update rate (~1 Hz); requires unplugging AC; alters CPU/GPU boost governors (battery power profile); must be labelled as an uncalibrated cross-check only. |
