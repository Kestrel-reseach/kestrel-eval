"""Run the formal 10-minute x 3 repeats idle baseline for Project Kestrel Step 0.

This script runs 3 sequential 10-minute (600 s) idle baseline recordings
at 10 Hz sampling frequency using the EnergyHarness NVML monitor.
Total duration: ~30 minutes (1800 s).

Prerequisites:
- Machine must be connected to AC power.
- Power plan / performance profile must be set to the standard evaluation profile.
- Display/sleep timeouts should be disabled or kept consistent.
- No user activity, background updates, or competing workloads.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from energy.harness import EnergyHarness, HarnessConfig, IdleBaseline


def run_formal_idle_baseline(
    repeat_duration_s: float = 600.0,
    num_repeats: int = 3,
    sample_interval_s: float = 0.1,
    output_path: Path | None = None,
) -> dict:
    print("=" * 75)
    print("KESTREL STEP 0: FORMAL 10-MINUTE x 3 IDLE BASELINE")
    print("=" * 75)
    print(f"Target repeat duration : {repeat_duration_s:.1f} s ({repeat_duration_s / 60:.1f} min)")
    print(f"Number of repeats      : {num_repeats}")
    print(f"Total idle time        : {repeat_duration_s * num_repeats / 60:.1f} minutes")
    print(f"Sampling interval      : {sample_interval_s:.3f} s ({1.0 / sample_interval_s:.1f} Hz)")
    print("=" * 75)

    config = HarnessConfig(
        idle_baseline_seconds=int(repeat_duration_s),
        sample_interval_s=sample_interval_s,
        wall_meter_calibrated=False,
        relative_only=True,
    )
    harness = EnergyHarness(config)
    status = harness.check_counters(strict=True)
    print(f"Harness status: {json.dumps(status, indent=2)}\n")

    repeats: list[IdleBaseline] = []
    repeat_records: list[dict] = []

    for r in range(1, num_repeats + 1):
        print(
            f"--- [Repeat {r}/{num_repeats}] Recording {repeat_duration_s:.0f}s idle at 10 Hz ---"
        )
        b = harness.record_idle_baseline(duration_s=repeat_duration_s)
        repeats.append(b)

        rec = {
            "repeat": r,
            "duration_s": round(b.duration_s, 3),
            "samples": b.samples,
            "sample_rate_hz": round(b.sample_rate_hz, 2) if b.sample_rate_hz else None,
            "mean_gpu_power_w": round(b.gpu_power_w, 4) if b.gpu_power_w is not None else None,
            "gpu_power_std_w": round(b.gpu_power_std_w, 4)
            if b.gpu_power_std_w is not None
            else None,
            "counter_energy_j": round(b.gpu_energy_counter_j, 3)
            if b.gpu_energy_counter_j is not None
            else None,
        }
        repeat_records.append(rec)

        rate_str = f"{b.sample_rate_hz:.1f} Hz" if b.sample_rate_hz else "N/A"
        std_str = f"{b.gpu_power_std_w:.4f} W" if b.gpu_power_std_w is not None else "N/A"
        counter_str = (
            f"{b.gpu_energy_counter_j:.2f} J" if b.gpu_energy_counter_j is not None else "N/A"
        )
        print(
            f"  Repeat {r} finished: duration={b.duration_s:.2f}s | samples={b.samples} ({rate_str}) | "
            f"mean_P={b.gpu_power_w:.4f} W | std={std_str} | counter_energy={counter_str}\n"
        )

    # Pooled calculations
    total_duration = sum(b.duration_s for b in repeats)
    total_samples = sum(b.samples for b in repeats)
    mean_powers = [b.gpu_power_w for b in repeats if b.gpu_power_w is not None]
    pooled_mean_power_w = sum(mean_powers) / len(mean_powers) if mean_powers else 0.0

    stds = [b.gpu_power_std_w for b in repeats if b.gpu_power_std_w is not None]
    pooled_std_w = math.sqrt(sum(s**2 for s in stds) / len(stds)) if stds else 0.0

    counter_energies = [
        b.gpu_energy_counter_j for b in repeats if b.gpu_energy_counter_j is not None
    ]
    total_counter_j = sum(counter_energies) if counter_energies else None
    counter_derived_power_w = (
        (total_counter_j / total_duration) if (total_counter_j and total_duration > 0) else None
    )

    result = {
        "status": "COMPLETED",
        "protocol": "formal_10min_x3",
        "num_repeats": num_repeats,
        "total_duration_s": round(total_duration, 3),
        "total_samples": total_samples,
        "overall_sample_rate_hz": round(total_samples / total_duration, 2)
        if total_duration > 0
        else None,
        "pooled_mean_idle_power_w": round(pooled_mean_power_w, 4),
        "pooled_idle_power_std_w": round(pooled_std_w, 4),
        "total_counter_energy_j": round(total_counter_j, 3)
        if total_counter_j is not None
        else None,
        "counter_derived_power_w": round(counter_derived_power_w, 4)
        if counter_derived_power_w is not None
        else None,
        "repeats": repeat_records,
    }

    print("=" * 75)
    print("FORMAL IDLE BASELINE SUMMARY (Pooled Across 3 Repeats)")
    print("=" * 75)
    print(f"Total idle duration        : {total_duration:.2f} s ({total_duration / 60:.2f} min)")
    print(f"Total samples collected    : {total_samples} ({total_samples / total_duration:.1f} Hz)")
    print(f"Pooled Mean Idle Power     : {pooled_mean_power_w:.4f} W")
    print(f"Pooled Std Dev (sigma_idle): {pooled_std_w:.4f} W")
    if counter_derived_power_w is not None:
        print(
            f"Counter-Derived Mean Power : {counter_derived_power_w:.4f} W (delta={abs(pooled_mean_power_w - counter_derived_power_w):.4f} W)"
        )
    print("=" * 75)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Result written to {output_path}")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Formal 10-minute x 3 Idle Baseline")
    parser.add_argument(
        "--duration",
        type=float,
        default=600.0,
        help="Per-repeat duration in seconds (default: 600s)",
    )
    parser.add_argument("--repeats", type=int, default=3, help="Number of repeats (default: 3)")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Sampling interval in seconds (default: 0.1s = 10 Hz)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/step0/formal_idle_baseline.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()
    run_formal_idle_baseline(
        repeat_duration_s=args.duration,
        num_repeats=args.repeats,
        sample_interval_s=args.interval,
        output_path=args.output,
    )
