"""Step 10: assemble the final report from committed measurement records.

Reads the validation reports produced in Steps 3-7 (from the kestrel repo)
and the baselines/F records (from this repo), and emits a single report with:
  - the three headline numbers (gap to F, joules per correct task, resident GB)
  - every gate verdict and every ablation
  - every failed component, reported honestly
  - the Step 10 decision rule applied

Locked-test numbers are NOT filled by this script. The locked partition must be
run exactly once on the target hardware with the frozen config; pass those
numbers with --locked-test when that run is available. Until then the report
states that the locked test has not been run and is validation-only.

Stdlib only; no model or hardware access here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ENERGY_LABEL = (
    "Relative energy only; GPU NVML scope; same machine and session; "
    "not comparable across machines."
)
F_LABEL = (
    "F = gemini-flash-lite-latest (gemini-3.5-flash-lite, free tier, D21); "
    "a free-tier reference, not the current frontier."
)


def load_json(path: Path) -> dict[str, Any]:
    """Load one committed JSON report."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def collect(
    kestrel_dir: Path,
    eval_dir: Path,
    locked_test: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble all committed measurements into the final report structure."""
    step3 = load_json(kestrel_dir / "reports" / "verifier_step3.json")
    step4 = load_json(kestrel_dir / "reports" / "halting_step4.json")
    step5 = load_json(kestrel_dir / "reports" / "knowledge_store_step5.json")
    step6 = load_json(kestrel_dir / "reports" / "memory_step6.json")
    step7 = load_json(kestrel_dir / "reports" / "integration_step7.json")
    frontier = load_json(eval_dir / "reports" / "step2" / "frontier_f_evaluation_report.json")

    quality_gate = step7["quality_gate"]
    gq = quality_gate["G_Q"]
    gf = quality_gate["G_F"]

    validation_headline = {
        "quality_gap_to_f_pp": gf["gap_to_f_pp"],
        "gap_closed_pct": gf["gap_closed_pct"],
        "joules_per_correct_task_p1": gq["p1_net_joules_per_correct"],
        "joules_per_correct_task_b_llm": gq["b_llm_net_joules_per_correct"],
        "resident_gb_p1": step7["configurations"]["p1_integrated"]["resident_gb"],
        "resident_gb_b_llm": 1.383,  # Step 2 B-LLM resident memory
    }

    validation_gates = {
        "G_Q": gq["status"],
        "G_F": "reported (not promised)",
        "G_M": quality_gate["G_M"]["status"],
        "G_R": quality_gate["G_R"]["status"],
        "no_regression": step7["section_gates"]["gate_decision"],
        "step3_verifier": "PASS" if step3["gate_decision"]["passes"] else "FAIL",
        "step4_halting": step4["gate"]["gate_decision"],
        "step5_store": step5["gate"]["gate_decision"],
        "step6_memory": step6["gate"]["gate_decision"],
    }

    validation_failed = [
        {
            "component": "Step 4 verifier-gated halting",
            "reason": "gate failed; fixed two-pass kept per kill rule",
            "evidence": "reports/halting_step4.json",
        },
        {
            "component": "G-Q product quality gate",
            "reason": (
                f"P1 {gq['p1_accuracy_pct']}% vs B-LLM {gq['b_llm_accuracy_pct']}%; "
                f"delta {gq['delta_vs_b_llm_pp']} pp with CI including zero; "
                "energy above cap"
            ),
            "evidence": "reports/integration_step7.json",
        },
    ]

    ablations = {
        name: {
            "accuracy_pct": config.get("accuracy_pct"),
            "energy_per_correct_joules": config.get("joules_per_correct"),
        }
        for name, config in step7["configurations"].items()
        if name != "p1_integrated"
    }

    # Step 10 reports the locked-test numbers when the one-time run is available,
    # keeping validation numbers as a labelled comparison. Component gates stay
    # validation-only: the locked run has no component ablations.
    locked_gates = locked_test.get("gates", {}) if isinstance(locked_test, dict) else {}
    locked_systems = locked_test.get("systems", {}) if isinstance(locked_test, dict) else {}
    locked_run = (
        isinstance(locked_test, dict)
        and locked_test.get("status") == "RUN"
        and bool(locked_gates)
        and bool(locked_systems)
    )

    if locked_run:
        gf_lock = locked_gates["G_F"]
        gq_lock = locked_gates["G_Q"]
        p1_res = locked_systems["P1"]["resources"]
        b_res = locked_systems["B_LLM"]["resources"]
        headline = {
            "quality_gap_to_f_pp": gf_lock["gap_to_f_pp"],
            "gap_closed_pct": gf_lock["gap_closed_pct"],
            "joules_per_correct_task_p1": p1_res["net_joules_per_correct_full_suite"],
            "joules_per_correct_task_b_llm": b_res["net_joules_per_correct_full_suite"],
            "resident_gb_p1": p1_res["resident_gb"],
            "resident_gb_b_llm": b_res["resident_gb"],
        }
        gate_verdicts = dict(validation_gates)
        gate_verdicts.update(
            {name: locked_gates[name]["status"] for name in ("G_Q", "G_F", "G_M", "G_R")}
        )
        failed_components = [validation_failed[0]]
        if gq_lock["status"] != "PASS":
            failed_components.append(
                {
                    "component": "G-Q product quality gate",
                    "reason": (
                        f"Locked test: P1 {gq_lock['p1_accuracy_pct']}% vs B-LLM "
                        f"{gq_lock['b_llm_accuracy_pct']}%; delta {gq_lock['delta_pp']} pp "
                        f"with CI {[round(x, 2) for x in gq_lock['paired_bootstrap_ci_95_pp']]} "
                        "including zero; "
                        f"P1 {gq_lock['p1_net_joules_per_correct']} J/correct vs B-LLM "
                        f"{gq_lock['b_llm_net_joules_per_correct']} J/correct"
                    ),
                    "evidence": "reports/locked_test_step10.json",
                }
            )
    else:
        headline = validation_headline
        gate_verdicts = validation_gates
        failed_components = validation_failed

    # Step 10 decision rule: prototype 2 only if BOTH G-Q and G-R pass.
    product_path = (
        "prototype_2"
        if gate_verdicts["G_Q"] == "PASS" and gate_verdicts["G_R"] == "PASS"
        else "publish_negative_result"
    )
    decision_scope = "locked_test" if locked_run else "validation"

    return {
        "step": 10,
        "energy_label": ENERGY_LABEL,
        "frontier_reference": F_LABEL,
        "headline_numbers": headline,
        "validation_numbers": validation_headline,
        "headline_scope": decision_scope,
        "gate_verdicts": gate_verdicts,
        "ablations": ablations,
        "honest_wins": step7["honest_wins"],
        "failed_components": failed_components,
        "locked_test": locked_test
        or {
            "status": "NOT_RUN",
            "note": (
                "The locked-test partition must be run exactly once on target "
                "hardware with the frozen config. All numbers above are from "
                "validation only."
            ),
        },
        "decision": product_path,
        "decision_scope": decision_scope,
        "decision_reason": (
            f"G-Q and G-R must both pass for prototype 2 (evaluated on {decision_scope}: "
            f"G-Q={gate_verdicts['G_Q']}, G-R={gate_verdicts['G_R']})."
            if product_path == "publish_negative_result"
            else f"G-Q and G-R both pass (evaluated on {decision_scope})."
        ),
        "caveats": (
            list(locked_test["caveats"])
            if locked_run and isinstance(locked_test.get("caveats"), list)
            else []
        ),
        "f_measurement": {
            "public_accuracy_pct": frontier["metrics"]["arms"]["public"]["accuracy_pct"],
            "synthetic_accuracy_pct": frontier["metrics"]["arms"]["synthetic"]["accuracy_pct"],
            "full_suite_accuracy_pct": frontier["metrics"]["overall"]["accuracy_pct"],
        },
        "source_reports": [
            "kestrel/reports/verifier_step3.json",
            "kestrel/reports/halting_step4.json",
            "kestrel/reports/knowledge_store_step5.json",
            "kestrel/reports/memory_step6.json",
            "kestrel/reports/integration_step7.json",
            "kestrel-eval/reports/step2/frontier_f_evaluation_report.json",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render the assembled report as readable Markdown."""
    headline = report["headline_numbers"]
    scope = report["headline_scope"]
    scope_label = scope.replace("_", " ")
    lines = [
        "# Kestrel Prototype 1 — Final Report (Step 10)",
        "",
        f"> {report['energy_label']}",
        f"> {report['frontier_reference']}",
        "",
        f"## The three numbers ({scope_label})",
        "",
        f"- Quality gap to F: **{headline['quality_gap_to_f_pp']} pp** "
        f"({headline['gap_closed_pct']}% of the gap closed)",
        f"- Energy per correct task: **{headline['joules_per_correct_task_p1']} J** "
        f"(B-LLM {headline['joules_per_correct_task_b_llm']} J)",
        f"- Resident memory: **{headline['resident_gb_p1']} GB** "
        f"(B-LLM {headline['resident_gb_b_llm']} GB)",
        "",
    ]
    if scope == "locked_test":
        val = report["validation_numbers"]
        lines.extend(
            [
                "Validation-only for comparison: gap "
                f"{val['quality_gap_to_f_pp']} pp ({val['gap_closed_pct']}% closed), "
                f"{val['joules_per_correct_task_p1']} J/correct vs "
                f"{val['joules_per_correct_task_b_llm']} J for B-LLM, "
                f"{val['resident_gb_p1']} GB resident.",
                "",
            ]
        )
    lines.extend(
        [
            f"## Gate verdicts (product gates: {scope}; component gates: validation)",
            "",
        ]
    )
    for name, verdict in report["gate_verdicts"].items():
        lines.append(f"- **{name}**: {verdict}")
    lines.extend(["", "## Failed components", ""])
    for failed in report["failed_components"]:
        lines.append(f"- **{failed['component']}**: {failed['reason']} ({failed['evidence']})")
    lines.extend(["", "## Ablations (validation only)", ""])
    for name, metrics in report["ablations"].items():
        lines.append(
            f"- **{name}**: {metrics['accuracy_pct']}% accuracy, "
            f"{metrics['energy_per_correct_joules']} J/correct"
        )
    locked = report["locked_test"]
    locked_note = locked.get("note", "")
    lines.extend(
        [
            "",
            "## Locked-test partition",
            "",
            f"**{locked['status']}** — {locked_note}" if locked_note else f"**{locked['status']}**",
        ]
    )
    if locked.get("status") == "RUN" and isinstance(locked.get("systems"), dict):
        lines.extend(
            [
                "",
                "| System | Full Suite (1,250) | Checkable G-Q/G-F (800) | Store QA (300) | Memory (150) | Net J/Correct | Resident GB |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
            ]
        )
        for sys_name in ("F", "B_LLM", "P1"):
            s = locked["systems"].get(sys_name)
            if not s:
                continue
            fs = s["scopes"]["full_suite_1250"]
            chk = s["scopes"]["matched_checkable_800"]
            st = s["scopes"]["store_knowledge_qa_300"]
            mem = s["scopes"]["memory_probe_150"]
            res = s.get("resources", {})
            j_corr = res.get("net_joules_per_correct_full_suite")
            j_str = f"{j_corr:.2f} J" if j_corr is not None else "unmeasured"
            gb = res.get("resident_gb")
            gb_str = f"{gb:.3f} GB" if gb is not None else "—"
            lines.append(
                f"| **{sys_name}** | {fs['accuracy_pct']}% ({fs['correct']}/{fs['total']}) | "
                f"{chk['accuracy_pct']}% ({chk['correct']}/{chk['total']}) | "
                f"{st['accuracy_pct']}% ({st['correct']}/{st['total']}) | "
                f"{mem['accuracy_pct']}% ({mem['correct']}/{mem['total']}) | "
                f"{j_str} | {gb_str} |"
            )
        if isinstance(locked.get("gates"), dict):
            lines.extend(["", "### Locked-test gate verdicts", ""])
            for gname, gval in locked["gates"].items():
                if isinstance(gval, dict):
                    lines.append(f"- **{gname}**: {gval.get('status', gval)}")
    if report.get("caveats"):
        lines.extend(["", "## Caveats", ""])
        for caveat in report["caveats"]:
            lines.append(f"- {caveat}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"**{report['decision']}** — {report['decision_reason']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kestrel-dir", required=True, type=Path)
    parser.add_argument("--eval-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--locked-test", type=Path, default=None)
    args = parser.parse_args()

    locked = load_json(args.locked_test) if args.locked_test else None
    report = collect(args.kestrel_dir, args.eval_dir, locked)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path = args.out.with_suffix(".md")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {args.out} and {md_path}")
    print(f"Decision: {report['decision']}")


if __name__ == "__main__":
    main()
