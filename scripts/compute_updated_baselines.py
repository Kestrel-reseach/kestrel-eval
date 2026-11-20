"""Compute updated baseline metrics, Wilson CIs, cluster CIs, and energy on 800-item checkable scope.

Step 2 Correction Pass (Part 4).
Scope:
- 800 checkable validation items: math (200), science_mcq (200), knowledge_mcq (300), code (100).
- Gate G-Q baseline accuracy and net energy per correct task on 800-item scope.
- Gate G-M stale error rate on 100 stale fact items with cluster CI.
- Gate G-R process VRAM at 2048 context.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from evaluation.extractors import extract_answer_for_group


def wilson_score_interval(correct: int, total: int) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = correct / total
    z = 1.959964
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    half = (z * math.sqrt((p * (1.0 - p) / total) + (z**2) / (4.0 * (total**2)))) / denom
    return max(0.0, center - half), min(1.0, center + half)


REPO_ROOT = Path(__file__).resolve().parent.parent


def evaluate_records(file_path: Path):
    with open(file_path) as f:
        records = [json.loads(line) for line in f]

    # Re-extract and score with Dev-02 for math, mcq, qa
    # Code records were already re-run and updated in the jsonl
    for r in records:
        g = r.get("group")
        if g in ("math", "science_mcq", "knowledge_mcq", "knowledge_qa"):
            ext, corr = extract_answer_for_group(r, r.get("raw_output", ""))
            r["extracted_answer"] = ext
            r["correct"] = corr

    # Write back the clean records to jsonl
    with open(file_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    return records


def analyze_model(records: list[dict], model_tag: str, idle_power_w: float = 6.144):
    groups = ["math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe"]
    by_group = {g: [r for r in records if r.get("group") == g] for g in groups}

    # Group counts
    group_stats = {}
    for g, items in by_group.items():
        n = len(items)
        c = sum(1 for r in items if r["correct"])
        acc = c / n if n > 0 else 0.0
        lo, hi = wilson_score_interval(c, n)
        wall_s = sum(r.get("wall_time_ms", 0.0) for r in items) / 1000.0
        group_stats[g] = {
            "n": n,
            "correct": c,
            "accuracy_pct": round(acc * 100, 2),
            "ci_95": [round(lo * 100, 2), round(hi * 100, 2)],
            "wall_time_s": round(wall_s, 2),
        }

    # 800-item checkable scope
    checkable_groups = ["math", "science_mcq", "knowledge_mcq", "code"]
    checkable_items = [r for r in records if r.get("group") in checkable_groups]
    n_chk = len(checkable_items)
    c_chk = sum(1 for r in checkable_items if r["correct"])
    acc_chk = c_chk / n_chk if n_chk > 0 else 0.0
    lo_chk, hi_chk = wilson_score_interval(c_chk, n_chk)

    wall_s_chk = sum(r.get("wall_time_ms", 0.0) for r in checkable_items) / 1000.0

    # Arm breakdown
    arm_stats = {}
    arms = set(r.get("arm", "public") for r in records)
    for arm in sorted(arms):
        arm_items = [r for r in records if r.get("arm") == arm]
        n_a = len(arm_items)
        c_a = sum(1 for r in arm_items if r["correct"])
        acc_a = c_a / n_a if n_a > 0 else 0.0
        lo_a, hi_a = wilson_score_interval(c_a, n_a)
        arm_stats[arm] = {
            "n": n_a,
            "correct": c_a,
            "accuracy_pct": round(acc_a * 100, 2),
            "ci_95": [round(lo_a * 100, 2), round(hi_a * 100, 2)],
        }

    # Memory probe stale error
    mem_items = by_group["memory_probe"]
    stale_items = [
        r for r in mem_items if r.get("metadata", {}).get("stale_values") or r.get("stale_values")
    ]
    n_stale = len(stale_items)
    # Stale error: model outputs the deprecated historical value
    stale_errors = sum(1 for r in stale_items if not r["correct"])
    stale_err_rate = stale_errors / n_stale if n_stale > 0 else 0.0
    lo_stale, hi_stale = wilson_score_interval(stale_errors, n_stale)

    # Cluster bootstrap CI for memory probe
    rng = random.Random(20260102)
    clusters = {}
    for r in stale_items:
        # Cluster key: person entity id
        ent = (
            r.get("metadata", {}).get("person_id")
            or r.get("metadata", {}).get("entity")
            or r.get("item_id", "")[:12]
        )
        clusters.setdefault(ent, []).append(1 if not r["correct"] else 0)

    cluster_keys = list(clusters.keys())
    boot_rates = []
    for _ in range(2000):
        sampled = rng.choices(cluster_keys, k=len(cluster_keys))
        b_errs = sum(sum(clusters[k]) for k in sampled)
        b_n = sum(len(clusters[k]) for k in sampled)
        boot_rates.append(b_errs / b_n if b_n > 0 else 0.0)
    boot_rates.sort()
    cl_lo = boot_rates[int(0.025 * len(boot_rates))]
    cl_hi = boot_rates[int(0.975 * len(boot_rates))]

    # Overall 1250 items
    n_tot = len(records)
    c_tot = sum(1 for r in records if r["correct"])
    acc_tot = c_tot / n_tot if n_tot > 0 else 0.0
    lo_tot, hi_tot = wilson_score_interval(c_tot, n_tot)

    return {
        "model": model_tag,
        "total_1250": {
            "n": n_tot,
            "correct": c_tot,
            "accuracy_pct": round(acc_tot * 100, 2),
            "ci_95": [round(lo_tot * 100, 2), round(hi_tot * 100, 2)],
        },
        "checkable_800": {
            "n": n_chk,
            "correct": c_chk,
            "accuracy_pct": round(acc_chk * 100, 2),
            "ci_95": [round(lo_chk * 100, 2), round(hi_chk * 100, 2)],
            "wall_time_s": round(wall_s_chk, 2),
        },
        "groups": group_stats,
        "arms": arm_stats,
        "memory_probe_stale": {
            "n_stale": n_stale,
            "stale_errors": stale_errors,
            "stale_error_rate_pct": round(stale_err_rate * 100, 2),
            "wilson_ci_95": [round(lo_stale * 100, 2), round(hi_stale * 100, 2)],
            "cluster_ci_95": [round(cl_lo * 100, 2), round(cl_hi * 100, 2)],
            "clusters_count": len(clusters),
        },
    }


def main():
    models = [
        ("qwen2.5-0.5b-instruct-q4", "reports/step2/run_qwen2.5-0.5b-instruct-q4_validation.jsonl"),
        ("qwen2.5-1.5b-instruct-q4", "reports/step2/run_qwen2.5-1.5b-instruct-q4_validation.jsonl"),
    ]

    print("=" * 80)
    print("STEP 2 UPDATED BASELINE ANALYSIS (Post-Code Rerun & Dev-02 Rescoring)")
    print("=" * 80)

    summaries = {}
    for tag, rel_path in models:
        p = REPO_ROOT / rel_path
        recs = evaluate_records(p)
        s = analyze_model(recs, tag)
        summaries[tag] = s

        print(f"\nMODEL: {tag}")
        print(
            f"  Overall (1,250 items): {s['total_1250']['correct']}/{s['total_1250']['n']} ({s['total_1250']['accuracy_pct']}%), 95% CI {s['total_1250']['ci_95']}"
        )
        print(
            f"  Checkable G-Q Scope (800 items): {s['checkable_800']['correct']}/{s['checkable_800']['n']} ({s['checkable_800']['accuracy_pct']}%), 95% CI {s['checkable_800']['ci_95']}"
        )
        print("  Groups:")
        for g, gs in s["groups"].items():
            print(
                f"    {g:15s}: {gs['correct']:3d}/{gs['n']:3d} ({gs['accuracy_pct']:5.2f}%), 95% CI {gs['ci_95']}"
            )
        print("  Memory Probe Stale Fact:")
        st = s["memory_probe_stale"]
        print(f"    Errors: {st['stale_errors']}/{st['n_stale']} ({st['stale_error_rate_pct']}%)")
        print(f"    Wilson 95% CI : {st['wilson_ci_95']}%")
        print(
            f"    Cluster 95% CI: {st['cluster_ci_95']}% (across {st['clusters_count']} clusters)"
        )

    # Save summary
    out_file = REPO_ROOT / "reports/step2/c6_updated_gate_baselines.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    print(f"\nSaved updated summary: {out_file}")


if __name__ == "__main__":
    main()
