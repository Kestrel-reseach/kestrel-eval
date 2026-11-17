---
name: energy-measurement
description: >
  Energy measurement protocol for Kestrel Prototype 1.
  Load this skill when implementing or reviewing energy harness code,
  interpreting joules-per-task figures, or writing calibration notes.
---

# Skill: energy-measurement

## Headline metric

**Joules per correct task** — not tokens/s/W, not FLOPS.

```
joules_per_correct_task = sum(energy_joules for correct items) / count(correct items)
```

Include all passes (retries, refinements, escalations) for each item.

## Idle baseline

1. Record a **~10 minute idle baseline** before any evaluation run.
2. Measure CPU + GPU power with no model loaded and no inference.
3. Result: `idle_power_w` (mean watts over the baseline window).
4. For each item: `net_joules = gross_joules - idle_power_w * wall_time_s`.
5. **Always report both** gross and net figures.

## Counter sources on Ryzen 7 5800H / RTX 3060 Laptop

| Component | Source | Path |
|-----------|--------|------|
| CPU | RAPL via powercap | `/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj` |
| CPU (fallback) | hwmon k10temp | `/sys/class/hwmon/hwmon*/power1_average` |
| GPU | NVML via pynvml | `nvmlDeviceGetPowerUsage(handle) / 1000.0` |

RAPL reports cumulative micro-joules (wraps at `max_energy_range_uj`);
hwmon reports instantaneous micro-watts.

## Wall-meter calibration

- Run the harness and a plug-in power meter for the same 10-minute window.
- Record: `wall_meter_joules`, `software_joules`, `ratio = software / wall`.
- If `|ratio - 1| < 0.05`, counters are well-calibrated; report absolute joules.
- If calibration is not possible (no wall meter), set `relative_only: true` in
  `manifest.yaml` and label **every result** "relative energy only".

## Kill gate

If no counter is available (CPU and GPU both fail), energy cannot be measured.
Report wall-time only, add "energy unmeasured" to every result, and record why
in the PLAN.md status log.

## Harness API

```python
from energy.harness import EnergyHarness, HarnessConfig

config = HarnessConfig(
    idle_baseline_seconds=600,
    sample_interval_s=1.0,
    wall_meter_calibrated=None,   # set after calibration
    relative_only=False,
)
harness = EnergyHarness(config)
harness.check_counters()           # raises if no counter usable
baseline = harness.record_idle_baseline()
token = harness.start()
# ... model call ...
sample = harness.stop(token)
net_j = EnergyHarness.net_joules(sample, baseline)
```

