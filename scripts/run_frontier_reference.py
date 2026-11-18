#!/usr/bin/env python3
"""Execute Frontier Reference Model F evaluation runner (Step 2 Part 4c).

Protocol: Step 2 Part 4c (Frontier Reference Model F).
Enforces owner decisions D6 & D12:
    - Model: gemini-2.5-pro via Google AI Studio free tier
    - Cost cap: $0.00 (strictly zero paid API calls)
    - Pacing: 2 requests/min (RPM), 50 requests/day (RPD)
    - Memory probe: evaluated twice (no-history vs full-history)
    - API key read strictly from GEMINI_API_KEY environment variable

Usage:
    python scripts/run_frontier_reference.py [--mode auto|mock|real] [--limit N]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.run_matrix import RunConfig, RunMatrix  # noqa: E402
from evaluation.runners.frontier_runner import FrontierConfig, FrontierRunner  # noqa: E402
from evaluation.suite import load_suite_partition  # noqa: E402


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
        help="Optional maximum number of items to evaluate (useful for smoke tests)",
    )
    args = parser.parse_args()

    print("=== Step 2: Frontier Reference Model F Runner ===")
    config_path = REPO_ROOT / "config" / "f_limits.yaml"
    cfg = FrontierConfig.from_yaml(config_path)

    print(f"Model: {cfg.model} via {cfg.provider}")
    print(f"Cost Cap: ${cfg.cost_cap_usd:.2f} ({cfg.tier})")
    print(f"Pacing Limits: {cfg.requests_per_minute} RPM | {cfg.requests_per_day} RPD")
    print(f"Context Window: {cfg.max_context_tokens} tokens")

    # Check API key
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
            f"Estimated run duration for 1,200 validation items: {cfg.requests_per_day} RPD = 24.0 days."
        )
        print("Memory probe dual run (no_history + full_history = 200 items): 4.0 days.")
        print(
            "Running verified integration check in mock mode to validate schema and checkpointing..."
        )
        print("=" * 70 + "\n")
    else:
        print(
            f"\n[STATUS: READY] Found {cfg.api_key_env_var} in environment. Live inference ready."
        )

    # Load validation items
    items = load_suite_partition(split="validation", repo_root=REPO_ROOT)
    if args.limit:
        items = items[: args.limit]
    print(f"Loaded {len(items)} validation items.")

    runs_dir = REPO_ROOT / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Main Validation Run (full_history for memory_probe)
    output_path = runs_dir / "run_frontier_gemini_2.5_pro_validation.jsonl"
    run_cfg = RunConfig(
        run_id="run-frontier-gemini-2.5-pro-validation",
        git_commit="35d5400",
        seed=20260102,
        split="validation",
        system="F",
        output_path=output_path,
        energy_status="unmeasured",
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
    records = matrix.run(items)
    run_cfg.save(runs_dir / "run_frontier_gemini_2.5_pro_validation_config.json")
    print(f"    Wrote {len(records)} records to {output_path}")

    # 2. Dual Memory-Probe Run (no_history mode)
    mem_items = [item for item in items if item.get("group") == "memory_probe"]
    if mem_items:
        mem_output_path = runs_dir / "run_frontier_memory_probe_no_history.jsonl"
        mem_run_cfg = RunConfig(
            run_id="run-frontier-memory-probe-no-history",
            git_commit="35d5400",
            seed=20260102,
            split="validation",
            system="F",
            output_path=mem_output_path,
            energy_status="unmeasured",
            extra={
                "model": cfg.model,
                "history_mode": "no_history",
                "mock_mode": effective_mock,
            },
        )
        mem_runner = FrontierRunner(config=cfg, history_mode="no_history", mock_mode=effective_mock)
        mem_matrix = RunMatrix(mem_run_cfg, runner=mem_runner)
        print("\n--> Executing Frontier F memory probe (no_history mode)...")
        mem_records = mem_matrix.run(mem_items)
        mem_run_cfg.save(runs_dir / "run_frontier_memory_probe_no_history_config.json")
        print(
            f"    Wrote {len(mem_records)} memory probe (no_history) records to {mem_output_path}"
        )

    print("\nFrontier Reference F runner execution complete.")


if __name__ == "__main__":
    main()
