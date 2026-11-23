#!/usr/bin/env python3
"""Execute Frontier Reference Model F evaluation runner (Step 2 Part 4c).

Protocol: Step 2 Part 4c (Frontier Reference Model F).
Enforces owner decisions:
    - D6: Model Gemini via Google AI Studio free tier, $0 cost cap.
    - D11: Record model version, execution date and response IDs per item.
    - D12: Step 10 locked-test run allowed on free tier with safeguards.
    - D20: Paced across days to respect free tier quota limits.
    - Reports public and synthetic arms separately, and memory probe dual scores.

Usage:
    python scripts/run_frontier_reference.py [--mode auto|mock|real] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.run_matrix import RunConfig, RunMatrix  # noqa: E402
from evaluation.runners.frontier_runner import FrontierConfig, FrontierRunner  # noqa: E402
from evaluation.suite import load_suite_partition  # noqa: E402


def compute_arm_and_group_metrics(
    records: list[dict[str, Any]],
    mem_no_history_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute accuracy by arm (public vs synthetic), group, and memory probe."""
    public_records = [r for r in records if r.get("arm") == "public"]
    synthetic_records = [r for r in records if r.get("arm") == "synthetic"]

    def calc_acc(recs: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(recs)
        c = sum(1 for r in recs if r.get("correct"))
        pct = round(c / n * 100, 2) if n > 0 else 0.0
        return {"correct": c, "total": n, "accuracy_pct": pct}

    # Group breakdown
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        g = r.get("group", "unknown")
        groups.setdefault(g, []).append(r)

    group_metrics = {g: calc_acc(recs) for g, recs in groups.items()}

    # Memory probe dual scores
    mem_full_metrics = group_metrics.get(
        "memory_probe", {"correct": 0, "total": 0, "accuracy_pct": 0.0}
    )
    mem_no_metrics = (
        calc_acc(mem_no_history_records)
        if mem_no_history_records
        else {"correct": 0, "total": 0, "accuracy_pct": 0.0}
    )

    return {
        "overall": calc_acc(records),
        "arms": {
            "public": calc_acc(public_records),
            "synthetic": calc_acc(synthetic_records),
        },
        "groups": group_metrics,
        "memory_probe_dual": {
            "full_history": mem_full_metrics,
            "no_history": mem_no_metrics,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Frontier Reference Model F runner")
    parser.add_argument(
        "--mode",
        choices=["auto", "mock", "real"],
        default="auto",
        help="Execution mode (auto detects GEMINI_API_KEY; mock runs simulated; real calls API)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of items to evaluate",
    )
    args = parser.parse_args()

    print("=== Step 2: Frontier Reference Model F Runner ===")
    config_path = REPO_ROOT / "config" / "f_limits.yaml"
    cfg = FrontierConfig.from_yaml(config_path)

    print(f"Model: {cfg.model} via {cfg.provider}")
    print(f"Cost Cap: ${cfg.cost_cap_usd:.2f} ({cfg.tier})")
    print(f"Pacing Limits: {cfg.requests_per_minute} RPM | {cfg.requests_per_day} RPD")
    print(f"Context Window: {cfg.max_context_tokens} tokens")

    env_key = os.environ.get(cfg.api_key_env_var)
    is_key_set = bool(env_key and env_key.strip())

    if args.mode == "real" and not is_key_set:
        print(
            f"\n[ERROR] --mode real requested but {cfg.api_key_env_var} is not set in environment."
        )
        sys.exit(1)

    effective_mock = (args.mode == "mock") or (args.mode == "auto" and not is_key_set)

    if not is_key_set:
        print("\n" + "=" * 70)
        print("FRONTIER MODEL F STATUS: PENDING_KEY")
        print(f"Environment variable '{cfg.api_key_env_var}' is not set.")
        print(
            f"Estimated run duration for 1,250 validation items: {cfg.requests_per_day} RPD = 25.0 days."
        )
        print("Memory probe dual run (no_history + full_history = 300 items): 6.0 days.")
        print(
            "Running verified integration check in mock mode to validate schema and checkpointing..."
        )
        print("=" * 70 + "\n")
    else:
        print(
            f"\n[STATUS: READY] Found {cfg.api_key_env_var} in environment. Live inference ready."
        )

    items = load_suite_partition(split="validation", repo_root=REPO_ROOT)
    if args.limit:
        items = items[: args.limit]
    print(f"Loaded {len(items)} validation items.")

    runs_dir = REPO_ROOT / "runs"
    reports_dir = REPO_ROOT / "reports" / "step2"
    runs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Main Validation Run (full_history for memory_probe)
    model_slug = cfg.model.replace("/", "_").replace(".", "_")
    output_path = runs_dir / f"run_frontier_{model_slug}_validation.jsonl"
    run_cfg = RunConfig(
        run_id=f"run-frontier-{model_slug}-validation",
        git_commit="2b4cca4",
        seed=20260102,
        split="validation",
        system="F",
        output_path=output_path,
        energy_status="unmeasured",
        simulated=effective_mock,
        inference_mode="simulated" if effective_mock else "real",
        extra={
            "model": cfg.model,
            "provider": cfg.provider,
            "history_mode": "full_history",
            "mock_mode": effective_mock,
            "reference_label": cfg.reference_label,
        },
    )

    runner = FrontierRunner(config=cfg, history_mode="full_history", mock_mode=effective_mock)
    matrix = RunMatrix(run_cfg, runner=runner)

    print("\n--> Executing Frontier F validation run...")
    try:
        records = matrix.run(items)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        ValueError,
        RuntimeError,
        TimeoutError,
    ) as exc:
        print(f"\n[API NOTICE / EXCEPTION]: {exc}")
        records = []

    run_cfg.save(runs_dir / f"run_frontier_{model_slug}_validation_config.json")
    print(f"    Wrote {len(records)} records to {output_path}")

    # 2. Dual Memory-Probe Run (no_history mode)
    mem_items = [item for item in items if item.get("group") == "memory_probe"]
    mem_records: list[dict[str, Any]] = []
    if mem_items:
        mem_output_path = runs_dir / f"run_frontier_{model_slug}_memory_probe_no_history.jsonl"
        mem_run_cfg = RunConfig(
            run_id=f"run-frontier-{model_slug}-memory-probe-no-history",
            git_commit="2b4cca4",
            seed=20260102,
            split="validation",
            system="F",
            output_path=mem_output_path,
            energy_status="unmeasured",
            simulated=effective_mock,
            inference_mode="simulated" if effective_mock else "real",
            extra={
                "model": cfg.model,
                "history_mode": "no_history",
                "mock_mode": effective_mock,
            },
        )
        mem_runner = FrontierRunner(config=cfg, history_mode="no_history", mock_mode=effective_mock)
        mem_matrix = RunMatrix(mem_run_cfg, runner=mem_runner)
        print("\n--> Executing Frontier F memory probe (no_history mode)...")
        try:
            mem_records = mem_matrix.run(mem_items)
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            ValueError,
            RuntimeError,
            TimeoutError,
        ) as exc:
            print(f"\n[API NOTICE / EXCEPTION on memory probe]: {exc}")
            mem_records = []
        mem_run_cfg.save(
            runs_dir / f"run_frontier_{model_slug}_memory_probe_no_history_config.json"
        )
        print(
            f"    Wrote {len(mem_records)} memory probe (no_history) records to {mem_output_path}"
        )

    # 3. Generate Step 2 Frontier Reference Report
    all_eval_records = records if records else []
    metrics = compute_arm_and_group_metrics(all_eval_records, mem_records)

    # Response ID log mapping
    response_id_log = [
        {
            "item_id": r["item_id"],
            "response_id": r.get("response_id"),
            "model_version": r.get("model_version"),
            "execution_date": r.get("execution_date"),
            "correct": r.get("correct"),
        }
        for r in all_eval_records
    ]

    report = {
        "step": 2,
        "system": "F",
        "model": cfg.model,
        "provider": cfg.provider,
        "tier": cfg.tier,
        "cost_cap_usd": cfg.cost_cap_usd,
        "reference_label": cfg.reference_label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_validation_items": len(items),
        "total_records_written": len(all_eval_records),
        "execution_mode": "mock" if effective_mock else "real",
        "api_key_status": runner.api_key_status,
        "metrics": metrics,
        "response_ids_logged": len(response_id_log),
        "response_id_log_sample": response_id_log[:10],
    }

    report_path = reports_dir / "frontier_f_evaluation_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nWrote Frontier F evaluation report to {report_path}")
    print("\nFrontier Reference F runner execution complete.")


if __name__ == "__main__":
    main()
