"""Step 10 tests: final report assembly from committed measurement records.

Tests build synthetic records in a temp dir so they run on any CI runner
without needing the sibling kestrel repo checkout.
"""

import json
from pathlib import Path

from scripts.build_final_report import collect, render_markdown


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")


def _fixture_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Create minimal kestrel/ and kestrel-eval/ report trees."""
    kestrel = tmp_path / "kestrel"
    eval_dir = tmp_path / "kestrel-eval"

    _write(
        kestrel / "reports" / "verifier_step3.json",
        {"gate_decision": {"passes": True}, "metrics": {"ece": 0.086}},
    )
    _write(
        kestrel / "reports" / "halting_step4.json",
        {"gate": {"gate_decision": "FAIL"}},
    )
    _write(
        kestrel / "reports" / "knowledge_store_step5.json",
        {"gate": {"gate_decision": "PASS"}},
    )
    _write(
        kestrel / "reports" / "memory_step6.json",
        {"gate": {"gate_decision": "PASS"}},
    )
    _write(
        kestrel / "reports" / "integration_step7.json",
        {
            "configurations": {
                "p1_integrated": {"resident_gb": 1.385, "accuracy_pct": 65.6},
                "ablation_no_verifier": {
                    "accuracy_pct": 63.2,
                    "joules_per_correct": 213.83,
                },
            },
            "quality_gate": {
                "G_Q": {
                    "status": "FAIL",
                    "p1_accuracy_pct": 57.63,
                    "b_llm_accuracy_pct": 56.88,
                    "delta_vs_b_llm_pp": 0.75,
                    "p1_net_joules_per_correct": 297.02,
                    "b_llm_net_joules_per_correct": 171.55,
                },
                "G_F": {
                    "gap_to_f_pp": 23.49,
                    "gap_closed_pct": 3.09,
                },
                "G_M": {"status": "PASS"},
                "G_R": {"status": "PASS"},
            },
            "section_gates": {"gate_decision": "PASS (no-regression sanity only)"},
            "honest_wins": {},
        },
    )
    _write(
        eval_dir / "reports" / "step2" / "frontier_f_evaluation_report.json",
        {
            "metrics": {
                "arms": {
                    "public": {"accuracy_pct": 79.85},
                    "synthetic": {"accuracy_pct": 88.33},
                },
                "overall": {"accuracy_pct": 78.4},
            }
        },
    )
    return kestrel, eval_dir


def test_collect_reads_committed_reports(tmp_path) -> None:
    kestrel, eval_dir = _fixture_dirs(tmp_path)
    report = collect(kestrel, eval_dir)
    assert report["step"] == 10
    assert report["gate_verdicts"]["G_Q"] == "FAIL"
    assert report["gate_verdicts"]["G_R"] == "PASS"
    assert report["decision"] == "publish_negative_result"
    assert report["locked_test"]["status"] == "NOT_RUN"
    assert "Relative energy only" in report["energy_label"]
    assert len(report["ablations"]) == 1
    assert len(report["failed_components"]) >= 1


def test_three_numbers_present(tmp_path) -> None:
    kestrel, eval_dir = _fixture_dirs(tmp_path)
    headline = collect(kestrel, eval_dir)["headline_numbers"]
    for key in (
        "quality_gap_to_f_pp",
        "gap_closed_pct",
        "joules_per_correct_task_p1",
        "resident_gb_p1",
    ):
        assert headline[key] is not None


def test_decision_requires_both_gates(tmp_path) -> None:
    kestrel, eval_dir = _fixture_dirs(tmp_path)
    report = collect(kestrel, eval_dir)
    assert report["decision"] == "publish_negative_result"  # G-Q fails here
    text = render_markdown(report)
    assert "publish_negative_result" in text


def test_render_markdown_includes_failed_and_locked(tmp_path) -> None:
    kestrel, eval_dir = _fixture_dirs(tmp_path)
    text = render_markdown(collect(kestrel, eval_dir))
    assert "## Failed components" in text
    assert "Step 4 verifier-gated halting" in text
    assert "NOT_RUN" in text
    assert "## Decision" in text


def test_locked_test_numbers_are_used_when_supplied(tmp_path) -> None:
    kestrel, eval_dir = _fixture_dirs(tmp_path)
    locked = {"status": "RUN", "accuracy_pct": 50.0}
    report = collect(kestrel, eval_dir, locked)
    assert report["locked_test"] == locked
