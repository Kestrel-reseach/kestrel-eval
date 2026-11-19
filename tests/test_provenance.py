"""Tests for R0 provenance guards (rules against simulated data leakage)."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.baselines_evaluator import (
    BaselineMetricSummary,
    generate_baseline_table,
    run_candidate_evaluation,
)
from evaluation.metrics import (
    MANDATORY_ENERGY_LABEL,
    format_energy_table,
    gate_q_accuracy,
    gate_q_energy,
)
from evaluation.schema import validate_record


def _make_record(**overrides) -> dict:
    base = {
        "run_id": "test-run",
        "git_commit": "abc1234",
        "config_hash": "deadbeef12345678",
        "seed": 20260101,
        "split": "validation",
        "group": "math",
        "item_id": "math-001",
        "system": "B_LLM",
        "git_dirty": False,
        "energy_status": "relative_only",
        "tokens_generated": 10,
        "passes": 1,
        "verifier_score": None,
        "retrieval_hits": 0,
        "bytes_read_from_ssd": 0,
        "energy_joules": 1.0,
        "wall_time_ms": 100.0,
        "peak_vram_mb": 500.0,
        "correct": True,
        "inference_mode": "real",
        "simulated": False,
    }
    base.update(overrides)
    return base


def test_schema_requires_inference_mode_and_simulated():
    rec = _make_record()
    del rec["inference_mode"]
    errors = validate_record(rec)
    assert any("inference_mode" in e for e in errors)

    rec = _make_record()
    del rec["simulated"]
    errors = validate_record(rec)
    assert any("simulated" in e for e in errors)


def test_schema_rejects_mismatched_inference_mode():
    rec = _make_record(inference_mode="simulated", simulated=False)
    errors = validate_record(rec)
    assert any("simulated must be True" in e for e in errors)

    rec = _make_record(inference_mode="real", simulated=True)
    errors = validate_record(rec)
    assert any("simulated must be False" in e for e in errors)


def test_generate_baseline_table_refuses_simulated_data():
    simulated_summary = BaselineMetricSummary(
        system="B_LLM",
        candidate_id="qwen2.5-0.5b-instruct-q4",
        group_accuracies={"math": 0.44},
        overall_accuracy=0.44,
        ci_95=(40.0, 48.0),
        gross_joules_per_correct=2.0,
        net_joules_per_correct=1.5,
        resident_vram_gb=0.45,
        p50_latency_ms=40.0,
        p95_latency_ms=50.0,
        simulated=True,
        inference_mode="simulated",
    )
    with pytest.raises(ValueError, match="Provenance guard violated"):
        generate_baseline_table({"qwen2.5-0.5b-instruct-q4": simulated_summary})


def test_format_energy_table_refuses_simulated_rows():
    headers = ["System", "Joules"]
    rows = [["B_LLM (Simulated)", "2.0 J"]]
    with pytest.raises(ValueError, match="Provenance guard violated"):
        format_energy_table(headers, rows, mandatory_label=MANDATORY_ENERGY_LABEL)


def test_gates_refuse_simulated_records():
    sim_rec = _make_record(inference_mode="simulated", simulated=True)
    real_rec = _make_record(inference_mode="real", simulated=False)

    with pytest.raises(ValueError, match="Provenance guard violated"):
        gate_q_accuracy([sim_rec], [real_rec])

    with pytest.raises(ValueError, match="Provenance guard violated"):
        gate_q_energy([real_rec], [sim_rec])


def test_run_candidate_evaluation_refuses_simulated_to_reports(tmp_path: Path):
    dummy_item = {
        "item_id": "math-001",
        "group": "math",
        "prompt": "2+2",
        "target": "4",
    }
    with pytest.raises(RuntimeError, match="Provenance guard violated"):
        run_candidate_evaluation(
            "qwen2.5-0.5b-instruct-q4",
            [dummy_item],
            output_dir=Path("reports/step2_simulated"),
            simulate=True,
        )
