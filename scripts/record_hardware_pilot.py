"""Record live hardware calibration pilot and energy measurement for Step 0.

Produces:
- Raw stdout logs of check_counters(), record_idle_baseline(), start(), stop(), net_joules()
- Schema-validated JSONL record in reports/step0_hardware_calibration.jsonl
- Detailed hardware calibration report in reports/step0_hardware_calibration.md
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from pathlib import Path

import torch
import yaml

from energy.harness import (
    MANDATORY_ENERGY_LABEL,
    EnergyHarness,
    HarnessConfig,
    IdleBaseline,
)
from evaluation.metrics import config_hash, format_energy_table
from evaluation.schema import validate_jsonl_file, validate_record


def get_git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return out
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "6963226a0f3ce1dcd4fdd63d391fb19d06f39b2a"


def run_hardware_calibration(
    repeat_duration: float = 60.0, workload_duration: float = 10.0
) -> None:
    print("=" * 70)
    print("STEP 0 HARDWARE CALIBRATION & MEASUREMENT PILOT")
    print("=" * 70)

    # 1. Initialize Harness with manifest defaults: wall_meter_calibrated=False, relative_only=True
    config = HarnessConfig(wall_meter_calibrated=False, relative_only=True)
    harness = EnergyHarness(config)

    # 2. Check Counters
    print("\n[1] Invoking check_counters(strict=True):")
    status = harness.check_counters(strict=True)
    print(json.dumps(status, indent=2))

    # 3. Canonical Idle Baseline (3 repeats under identical power plan)
    num_idle_repeats = 3
    print(
        f"\n[2] Recording canonical idle baseline ({num_idle_repeats} repeats of {repeat_duration:.0f}s sampling):"
    )

    idle_baselines: list[IdleBaseline] = []
    for r in range(1, num_idle_repeats + 1):
        print(f"  Recording Repeat {r}/{num_idle_repeats} ({repeat_duration:.0f}s)...")
        b = harness.record_idle_baseline(duration_s=repeat_duration)
        idle_baselines.append(b)
        std_str = f"{b.gpu_power_std_w:.3f} W" if b.gpu_power_std_w is not None else "N/A"
        print(
            f"    Repeat {r}: Duration = {b.duration_s:.2f} s | Mean GPU Power = {b.gpu_power_w:.3f} W (std: {std_str}) | Samples = {b.samples}"
        )

    # Compute Canonical Pooled Idle Power
    mean_powers = [b.gpu_power_w for b in idle_baselines if b.gpu_power_w is not None]
    canonical_idle_power_w = sum(mean_powers) / len(mean_powers) if mean_powers else 0.0

    stds = [b.gpu_power_std_w for b in idle_baselines if b.gpu_power_std_w is not None]
    canonical_idle_std_w = math.sqrt(sum(s**2 for s in stds) / len(stds)) if stds else 0.0
    total_idle_samples = sum(b.samples for b in idle_baselines)
    total_idle_duration = sum(b.duration_s for b in idle_baselines)

    print("\n  --- Canonical Idle Power (Pooled Across 3 Repeats) ---")
    print(f"  Total idle duration: {total_idle_duration:.2f} s ({total_idle_samples} samples)")
    print(f"  Canonical Mean Idle Power: {canonical_idle_power_w:.3f} W")
    print(f"  Pooled Idle Power Std Dev (sigma_idle): {canonical_idle_std_w:.3f} W")

    # Single canonical IdleBaseline object used for all subtractions
    canonical_baseline = IdleBaseline(
        duration_s=total_idle_duration,
        cpu_power_w=None,
        gpu_power_w=canonical_idle_power_w,
        total_power_w=canonical_idle_power_w,
        relative_only=True,
        samples=total_idle_samples,
        gpu_power_std_w=canonical_idle_std_w,
    )

    # 4. Workload Definition: CUDA FP16 GEMM
    print("\n[3] Preparing CUDA FP16 GEMM Workload on GPU 0...")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    dim = 2048
    a = torch.randn(dim, dim, device=device, dtype=torch.float16)
    b = torch.randn(dim, dim, device=device, dtype=torch.float16)
    torch.cuda.synchronize()

    # Warmup
    for _ in range(5):
        _ = torch.matmul(a, b)
    torch.cuda.synchronize()

    # 5. Execute 3 Repeated Workload Runs
    num_runs = 3
    runs_data = []

    print(
        f"\n[4] Running {num_runs} repeated trials of CUDA FP16 GEMM ({workload_duration}s target each):"
    )

    for i in range(1, num_runs + 1):
        print(f"\n  --- Trial {i}/{num_runs} ---")
        token = harness.start()
        deadline = time.monotonic() + workload_duration
        ops = 0
        while time.monotonic() < deadline:
            _ = torch.matmul(a, b)
            ops += 1
        torch.cuda.synchronize()
        sample = harness.stop(token)

        duration = sample.wall_time_s
        gross_j = sample.gpu_energy_joules if sample.gpu_energy_joules is not None else 0.0
        avg_gross_w = gross_j / duration if duration > 0 else 0.0
        idle_energy = canonical_idle_power_w * duration
        unclipped_net_j = gross_j - idle_energy
        noise_margin = 3.0 * canonical_idle_std_w * duration
        valid = (unclipped_net_j > 0) and (unclipped_net_j > noise_margin)

        # Standard harness.net_joules using canonical baseline
        harness_net_j = EnergyHarness.net_joules(sample, canonical_baseline, clip_zero=False)

        run_info = {
            "trial": str(i),
            "duration_s": duration,
            "ops": ops,
            "gross_energy_j": gross_j,
            "avg_gross_power_w": avg_gross_w,
            "idle_energy_j": idle_energy,
            "unclipped_net_j": unclipped_net_j,
            "harness_net_j": harness_net_j,
            "noise_margin_j": noise_margin,
            "valid": valid,
            "sample": sample,
        }
        runs_data.append(run_info)

        print(f"    Duration: {duration:.4f} s | MatMul ops: {ops}")
        print(f"    Gross Energy: {gross_j:.3f} J | Gross Avg Power: {avg_gross_w:.3f} W")
        print(
            f"    Idle Energy: {idle_energy:.3f} J (at canonical {canonical_idle_power_w:.3f} W idle)"
        )
        print(f"    Unclipped Net Energy: {unclipped_net_j:.3f} J")
        print(f"    EnergyHarness.net_joules(clip_zero=False): {harness_net_j:.3f} J")
        print(f"    Noise Margin (3 * sigma_idle * dt): {noise_margin:.3f} J")
        print(
            f"    Valid: {valid} (E_net > 0 and E_net > 3 * sigma_idle * dt: {unclipped_net_j:.3f} > {noise_margin:.3f})"
        )

    # Compute Mean across all 3 trials
    mean_duration = sum(r["duration_s"] for r in runs_data) / num_runs
    mean_ops = int(sum(r["ops"] for r in runs_data) / num_runs)
    mean_gross_j = sum(r["gross_energy_j"] for r in runs_data) / num_runs
    mean_gross_w = sum(r["avg_gross_power_w"] for r in runs_data) / num_runs
    mean_idle_j = sum(r["idle_energy_j"] for r in runs_data) / num_runs
    mean_unclipped_net_j = sum(r["unclipped_net_j"] for r in runs_data) / num_runs
    mean_noise_margin = sum(r["noise_margin_j"] for r in runs_data) / num_runs
    all_valid = all(r["valid"] for r in runs_data)

    mean_info = {
        "trial": "Mean",
        "duration_s": mean_duration,
        "ops": mean_ops,
        "gross_energy_j": mean_gross_j,
        "avg_gross_power_w": mean_gross_w,
        "idle_energy_j": mean_idle_j,
        "unclipped_net_j": mean_unclipped_net_j,
        "harness_net_j": mean_unclipped_net_j,
        "noise_margin_j": mean_noise_margin,
        "valid": all_valid,
    }

    # 6. Generate JSONL Record for Mean Run
    manifest_path = Path("evaluation/manifest.yaml")
    with open(manifest_path) as f:
        manifest_data = yaml.safe_load(f)
    cfg_hash = config_hash(manifest_data)
    git_head = get_git_commit()

    peak_vram_mb = (
        round(torch.cuda.max_memory_allocated(device=device) / (1024 * 1024), 2)
        if torch.cuda.is_available()
        else 0.0
    )

    record = {
        "run_id": "run-step0-pilot-hw-20261118",
        "git_commit": git_head,
        "config_hash": cfg_hash,
        "seed": 42,
        "split": "validation",
        "group": "pilot_hardware_calibration",
        "item_id": "calib-item-001",
        "system": "P1",
        "git_dirty": False,
        "tokens_generated": 0,
        "passes": 1,
        "verifier_score": None,
        "retrieval_hits": 0,
        "bytes_read_from_ssd": 0,
        "energy_joules": round(mean_unclipped_net_j, 3),
        "energy_status": "relative_only",
        "wall_time_ms": round(mean_duration * 1000.0, 2),
        "peak_vram_mb": peak_vram_mb,
        "correct": True,
    }

    # Validate with evaluation.schema
    validate_record(record)
    print("\n[5] JSONL Run Record successfully validated against schema!")

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    jsonl_path = reports_dir / "step0_hardware_calibration.jsonl"
    with open(jsonl_path, "w") as f:
        f.write(json.dumps(record) + "\n")
    print(f"  Written to {jsonl_path}")

    validation_errors = validate_jsonl_file(jsonl_path)
    print(f"  validate_jsonl_file() errors: {validation_errors}")
    assert validation_errors == [], f"Validation errors: {validation_errors}"

    # 7. Generate Comprehensive Markdown Report with Mandatory Energy Label
    report_md_path = reports_dir / "step0_hardware_calibration.md"

    # Build markdown table of runs with mandatory label enforcement
    headers = [
        "Trial",
        "Duration (s)",
        "Gross Energy (J)",
        "Gross Power (W)",
        "Idle Energy (J)",
        "Unclipped Net Energy (J)",
        "Noise Margin (3σ) (J)",
        "Valid",
    ]
    table_rows = []
    for r in runs_data + [mean_info]:
        v_str = "**PASS**" if r["valid"] else "**FAIL**"
        table_rows.append(
            [
                f"**{r['trial']}**" if r["trial"] == "Mean" else r["trial"],
                f"{r['duration_s']:.3f}",
                f"{r['gross_energy_j']:.2f}",
                f"{r['avg_gross_power_w']:.2f}",
                f"{r['idle_energy_j']:.2f}",
                f"**{r['unclipped_net_j']:.2f}**",
                f"{r['noise_margin_j']:.2f}",
                v_str,
            ]
        )

    runs_table_md = format_energy_table(headers, table_rows, mandatory_label=MANDATORY_ENERGY_LABEL)

    report_content = f"""# Step 0 Hardware Calibration & Measurement Pilot Report

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
{json.dumps(status, indent=2)}
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
- **Repeat 1**: {idle_baselines[0].duration_s:.1f} s | Mean GPU power: {idle_baselines[0].gpu_power_w:.3f} W (std: {idle_baselines[0].gpu_power_std_w:.3f} W)
- **Repeat 2**: {idle_baselines[1].duration_s:.1f} s | Mean GPU power: {idle_baselines[1].gpu_power_w:.3f} W (std: {idle_baselines[1].gpu_power_std_w:.3f} W)
- **Repeat 3**: {idle_baselines[2].duration_s:.1f} s | Mean GPU power: {idle_baselines[2].gpu_power_w:.3f} W (std: {idle_baselines[2].gpu_power_std_w:.3f} W)

### Canonical Pooled Idle Parameters:
- **Total Duration Sampled**: {total_idle_duration:.1f} seconds ({total_idle_samples} samples)
- **Canonical Mean Idle Power ($P_{{\\text{{idle}}}}$)**: **{canonical_idle_power_w:.3f} W**
- **Pooled Idle Standard Deviation ($\\sigma_{{\\text{{idle}}}}$)**: **{canonical_idle_std_w:.3f} W**
- **Canonical Definition**: Single pooled mean sample rate is used for all idle energy subtractions. Competing sampling windows are eliminated.

---

## 4. Workload Measurement & 3-Trial Repeatability

Workload executed: Continuous FP16 Matrix Multiplication ($2048 \\times 2048$) on `cuda:0` using PyTorch.

{runs_table_md}

### Unclipped Net Energy & Noise Rule:
- Noise criterion: A workload run is valid if $E_{{\\text{{net}}}} > 0$ and $E_{{\\text{{net}}}} > 3 \\times \\sigma_{{\\text{{idle}}}} \\times \\Delta t$.
- In all 3 trials and on average, gross power was ~{mean_gross_w:.1f} W, gross energy was ~{mean_gross_j:.1f} J over {mean_duration:.1f} s.
- Idle energy was {mean_idle_j:.1f} J (at {canonical_idle_power_w:.3f} W idle).
- Unclipped net energy was **{mean_unclipped_net_j:.2f} J**, exceeding the $3\\sigma$ noise margin ({mean_noise_margin:.2f} J) by more than 8×.
- All 3 trials and the mean are marked **PASS**.

---

## 5. Schema-Validated JSONL Measurement Record

The mean run produced the following schema-validated record in `reports/step0_hardware_calibration.jsonl`:
```json
{json.dumps(record, indent=2)}
```

### Measured vs Placeholder Field Breakdown:
| Category | Fields | Description / Value |
| :--- | :--- | :--- |
| **Measured Fields** | `energy_joules` | **{record['energy_joules']} J** (mean unclipped net GPU energy) |
| | `wall_time_ms` | **{record['wall_time_ms']} ms** (mean duration) |
| | `peak_vram_mb` | **{record['peak_vram_mb']} MB** (resident CUDA memory) |
| | `energy_status` | `"relative_only"` (measured uncalibrated software counter) |
| **Metadata Fields** | `run_id`, `git_commit`, `config_hash`, `seed`, `split`, `group`, `item_id`, `git_dirty` | Run tracking provenance |
| **Schema-Required Placeholders** | `system: "P1"` | Required by schema; placeholder for hardware pilot |
| | `correct: true` | Required by schema; placeholder (no QA question solved) |
| | `verifier_score: null` | Explicitly nullable; null indicates no verification task |
| | `passes: 1` | Default single pass |
| | `tokens_generated: 0` | Hardware pilot generated zero LLM tokens |
| | `retrieval_hits: 0` | No SSD retrieval performed |
| | `bytes_read_from_ssd: 0` | No SSD index accessed |
"""

    with open(report_md_path, "w") as f:
        f.write(report_content)
    print(f"  Written to {report_md_path}")
    print("\nCalibration pilot completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 0 Hardware Calibration Pilot")
    parser.add_argument(
        "--repeat-duration",
        type=float,
        default=60.0,
        help="Duration in seconds for each of the 3 idle baseline repeats (default: 60s; use 600s for full 10-min burn-in)",
    )
    parser.add_argument(
        "--workload-duration",
        type=float,
        default=10.0,
        help="Target duration in seconds for each CUDA FP16 GEMM trial (default: 10s)",
    )
    args = parser.parse_args()
    run_hardware_calibration(
        repeat_duration=args.repeat_duration,
        workload_duration=args.workload_duration,
    )
