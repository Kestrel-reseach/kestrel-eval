"""Step 10 tests: locked-test summary assembly, paired CIs, gates, and final report."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_final_report import collect, render_markdown
from scripts.run_step10_locked_test import assemble_locked_summary, wilson_ci_95


def _synthetic_records(rate_by_group: dict[str, float]) -> list[dict]:
    specs = [
        ("math", 200, "public"),
        ("science_mcq", 200, "public"),
        ("knowledge_mcq", 300, "public"),
        ("code", 100, "synthetic"),
        ("knowledge_qa", 300, "real_wikipedia"),
        ("memory_probe", 150, "synthetic"),
    ]
    recs = []
    for group, n, arm in specs:
        k = int(round(rate_by_group[group] * n))
        for i in range(n):
            rec = {
                "item_id": f"{group}_{i:04d}",
                "group": group,
                "arm": arm,
                "correct": i < k,
                "stale_fact_error": False,
                "wall_time_ms": 100.0,
                "net_energy_joules": 20.0,
                "gross_energy_joules": 21.0,
                "nvml_process_vram_mb": 1416.0,
                "model_version": "gemini-3.5-flash-lite",
                "execution_date": "2026-11-25",
                "metadata": {
                    "attribute": f"attr_{i % 10}",
                    "is_stale_fact": (group == "memory_probe" and i < 100),
                },
            }
            recs.append(rec)
    return recs


def test_wilson_ci_bounds() -> None:
    lo, hi = wilson_ci_95(400, 800)
    assert 45.0 < lo < 50.0 < hi < 55.0


def test_assemble_locked_summary_and_final_report(tmp_path: Path) -> None:
    f_recs = _synthetic_records(
        {
            "math": 0.75,
            "science_mcq": 0.90,
            "knowledge_mcq": 0.80,
            "code": 0.70,
            "knowledge_qa": 0.66,
            "memory_probe": 0.90,
        }
    )
    b_recs = _synthetic_records(
        {
            "math": 0.65,
            "science_mcq": 0.60,
            "knowledge_mcq": 0.50,
            "code": 0.45,
            "knowledge_qa": 0.68,
            "memory_probe": 0.82,
        }
    )
    p1_recs = _synthetic_records(
        {
            "math": 0.66,
            "science_mcq": 0.61,
            "knowledge_mcq": 0.51,
            "code": 0.46,
            "knowledge_qa": 0.72,
            "memory_probe": 0.96,
        }
    )
    f_nh = [
        {"item_id": f"memory_probe_{i:04d}", "group": "memory_probe", "correct": i < 5}
        for i in range(150)
    ]

    summary = assemble_locked_summary(
        f_recs,
        f_nh,
        b_recs,
        p1_recs,
        {"disk_bytes": 15_000_000, "resident_bytes": 6_000_000},
        kestrel_dir=tmp_path,
    )

    assert summary["status"] == "RUN"
    assert summary["gates"]["G_Q"]["status"] == "FAIL"
    assert summary["gates"]["G_M"]["status"] == "PASS"
    assert summary["gates"]["G_R"]["status"] == "PASS"
    assert summary["decision"] == "publish_negative_result"
    assert "matched_checkable_800" in summary["paired_comparisons"]

    # Feed into build_final_report.collect + render_markdown
    kestrel = tmp_path / "kestrel"
    eval_dir = tmp_path / "eval"
    for rel, obj in (
        ("reports/verifier_step3.json", {"gate_decision": {"passes": True}}),
        ("reports/halting_step4.json", {"gate": {"gate_decision": "FAIL"}}),
        ("reports/knowledge_store_step5.json", {"gate": {"gate_decision": "PASS"}}),
        ("reports/memory_step6.json", {"gate": {"gate_decision": "PASS"}}),
        (
            "reports/integration_step7.json",
            {
                "configurations": {"p1_integrated": {"resident_gb": 1.385}},
                "quality_gate": {
                    "G_Q": {
                        "status": "FAIL",
                        "p1_accuracy_pct": 57.63,
                        "b_llm_accuracy_pct": 56.88,
                        "delta_vs_b_llm_pp": 0.75,
                        "p1_net_joules_per_correct": 297.02,
                        "b_llm_net_joules_per_correct": 171.55,
                    },
                    "G_F": {"gap_to_f_pp": 23.49, "gap_closed_pct": 3.09},
                    "G_M": {"status": "PASS"},
                    "G_R": {"status": "PASS"},
                },
                "section_gates": {"gate_decision": "PASS (no-regression sanity only)"},
                "honest_wins": {},
            },
        ),
    ):
        p = kestrel / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj), encoding="utf-8")

    fp = eval_dir / "reports" / "step2" / "frontier_f_evaluation_report.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(
        json.dumps(
            {
                "metrics": {
                    "arms": {
                        "public": {"accuracy_pct": 79.85},
                        "synthetic": {"accuracy_pct": 88.33},
                    },
                    "overall": {"accuracy_pct": 78.4},
                }
            }
        ),
        encoding="utf-8",
    )

    final = collect(kestrel, eval_dir, locked_test=summary)
    assert final["locked_test"]["status"] == "RUN"
    assert final["decision"] == "publish_negative_result"
    md = render_markdown(final)
    assert "| **F** |" in md
    assert "| **B_LLM** |" in md
    assert "| **P1** |" in md
