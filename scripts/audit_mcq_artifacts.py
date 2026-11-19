"""A3: MCQ Artifact Audit on Synthetic Science and Knowledge MCQ Generators.

Audit Criteria (Pre-registered):
A trivial heuristic FAILS if the lower bound of its 95% Wilson confidence interval exceeds 25.0%.
If any heuristic fails for a group, that synthetic generator arm is DROPPED from Suite v2.0,
and that group becomes public-only.

Evaluated Heuristics:
1. Always 'A'
2. Longest Option (character length)
3. Shortest Option (character length)
4. Most Word Overlap with Question Stem
5. Median Numeric Option (for numeric options)
"""

from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996
    p = k / n
    denom = 1.0 + (z**2) / n
    centre = (p + (z**2) / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) + (z**2) / (4 * n)) / n)) / denom
    return (round(max(0.0, centre - half) * 100, 2), round(min(1.0, centre + half) * 100, 2))


def extract_stem_and_choices(item: dict[str, Any]) -> tuple[str, list[tuple[str, str]]]:
    """Returns (stem, [('A', text), ('B', text), ('C', text), ('D', text)])."""
    choices = item.get("choices", [])
    if choices and len(choices) == 4:
        labels = ["A", "B", "C", "D"]
        choice_pairs = [(labels[i], str(choices[i]).strip()) for i in range(4)]
    else:
        # Parse from prompt
        prompt = item.get("prompt", "")
        choice_pairs = []
        for line in prompt.splitlines():
            m = re.match(r"^\s*([A-D])\)\s*(.*)", line)
            if m:
                choice_pairs.append((m.group(1), m.group(2).strip()))
        if len(choice_pairs) != 4:
            choice_pairs = [("A", ""), ("B", ""), ("C", ""), ("D", "")]

    stem = item.get("stem") or item.get("question")
    if not stem:
        prompt = item.get("prompt", "")
        m = re.search(r"^(.*?)(?:\n\s*[A-D]\)|\n\nChoices:)", prompt, re.DOTALL)
        stem = m.group(1).strip() if m else prompt
    return stem, choice_pairs


def run_heuristic_audit(items: list[dict[str, Any]], group_name: str) -> dict[str, Any]:
    n = len(items)
    correct_always_a = 0
    correct_longest = 0
    correct_shortest = 0
    correct_overlap = 0

    numeric_total = 0
    correct_median_numeric = 0

    lengths_by_label = {"A": [], "B": [], "C": [], "D": []}
    correct_lengths = []
    incorrect_lengths = []
    key_distribution = Counter()

    # Per-family tracking
    family_stats: dict[str, dict[str, int]] = {}

    for it in items:
        target = it["target"]
        key_distribution[target] += 1
        stem, choices = extract_stem_and_choices(it)
        fam = (
            it.get("domain")
            or it.get("subject")
            or it.get("metadata", {}).get("domain")
            or it.get("metadata", {}).get("subject", "general")
        )
        if fam not in family_stats:
            family_stats[fam] = {
                "total": 0,
                "always_a": 0,
                "longest": 0,
                "shortest": 0,
                "overlap": 0,
            }
        family_stats[fam]["total"] += 1

        # Record lengths
        for lbl, txt in choices:
            l_len = len(txt)
            lengths_by_label[lbl].append(l_len)
            if lbl == target:
                correct_lengths.append(l_len)
            else:
                incorrect_lengths.append(l_len)

        # 1. Always A
        if target == "A":
            correct_always_a += 1
            family_stats[fam]["always_a"] += 1

        # 2. Longest option (break ties with first)
        longest_lbl = max(choices, key=lambda c: len(c[1]))[0]
        if longest_lbl == target:
            correct_longest += 1
            family_stats[fam]["longest"] += 1

        # 3. Shortest option
        shortest_lbl = min(choices, key=lambda c: len(c[1]))[0]
        if shortest_lbl == target:
            correct_shortest += 1
            family_stats[fam]["shortest"] += 1

        # 4. Word overlap with stem
        stem_words = set(re.findall(r"\w+", stem.lower()))

        def overlap_score(c: tuple[str, str], sw: set[str] = stem_words) -> int:
            c_words = set(re.findall(r"\w+", c[1].lower()))
            return len(sw & c_words)

        overlap_lbl = max(choices, key=overlap_score)[0]
        if overlap_lbl == target:
            correct_overlap += 1
            family_stats[fam]["overlap"] += 1

        # 5. Median numeric
        # Check if all choices parse as numbers
        numeric_vals = []
        for lbl, txt in choices:
            clean_num = re.sub(r"[^\d.-]", "", txt)
            try:
                numeric_vals.append((lbl, float(clean_num)))
            except ValueError:
                break
        if len(numeric_vals) == 4:
            numeric_total += 1
            sorted_by_val = sorted(numeric_vals, key=lambda x: x[1])
            # Middle two options in 4 items: take lower middle index 1
            median_lbl = sorted_by_val[1][0]
            if median_lbl == target:
                correct_median_numeric += 1

    heuristics = {
        "always_a": {
            "correct": correct_always_a,
            "accuracy": round(correct_always_a / n * 100, 2),
            "ci_95": wilson_ci(correct_always_a, n),
            "fails_criterion": wilson_ci(correct_always_a, n)[0] > 25.0,
        },
        "longest_option": {
            "correct": correct_longest,
            "accuracy": round(correct_longest / n * 100, 2),
            "ci_95": wilson_ci(correct_longest, n),
            "fails_criterion": wilson_ci(correct_longest, n)[0] > 25.0,
        },
        "shortest_option": {
            "correct": correct_shortest,
            "accuracy": round(correct_shortest / n * 100, 2),
            "ci_95": wilson_ci(correct_shortest, n),
            "fails_criterion": wilson_ci(correct_shortest, n)[0] > 25.0,
        },
        "most_word_overlap": {
            "correct": correct_overlap,
            "accuracy": round(correct_overlap / n * 100, 2),
            "ci_95": wilson_ci(correct_overlap, n),
            "fails_criterion": wilson_ci(correct_overlap, n)[0] > 25.0,
        },
    }

    if numeric_total > 0:
        heuristics["median_numeric"] = {
            "applicable_items": numeric_total,
            "correct": correct_median_numeric,
            "accuracy": round(correct_median_numeric / numeric_total * 100, 2),
            "ci_95": wilson_ci(correct_median_numeric, numeric_total),
            "fails_criterion": wilson_ci(correct_median_numeric, numeric_total)[0] > 25.0,
        }

    # Length analysis
    mean_correct_len = (
        round(sum(correct_lengths) / len(correct_lengths), 1) if correct_lengths else 0
    )
    mean_incorrect_len = (
        round(sum(incorrect_lengths) / len(incorrect_lengths), 1) if incorrect_lengths else 0
    )
    mean_lens_by_lbl = {
        lbl: round(sum(lens) / len(lens), 1) if lens else 0
        for lbl, lens in lengths_by_label.items()
    }

    # Any heuristic fails overall
    any_failed = any(h["fails_criterion"] for h in heuristics.values())

    return {
        "group": group_name,
        "total_items": n,
        "key_distribution": dict(key_distribution),
        "mean_correct_option_length": mean_correct_len,
        "mean_incorrect_option_length": mean_incorrect_len,
        "mean_lengths_by_label": mean_lens_by_lbl,
        "heuristics": heuristics,
        "arm_retained": not any_failed,
        "family_breakdown": family_stats,
    }


def sample_30_for_review(items: list[dict[str, Any]], seed: int = 20260105) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    sampled = rng.sample(items, min(30, len(items)))
    out = []
    for it in sampled:
        stem, choices = extract_stem_and_choices(it)
        fam = (
            it.get("domain")
            or it.get("subject")
            or it.get("metadata", {}).get("domain")
            or it.get("metadata", {}).get("subject", "general")
        )
        out.append(
            {
                "item_id": it.get("id") or it.get("item_id"),
                "family": fam,
                "stem": stem,
                "choices": choices,
                "target": it.get("target"),
            }
        )
    return out


def main() -> None:
    # Load validation and train partitions
    with open(REPO_ROOT / "suite" / "validation" / "science_mcq.jsonl", encoding="utf-8") as f:
        sci_val = [json.loads(line) for line in f if line.strip()]
    with open(REPO_ROOT / "suite" / "train" / "science_mcq.jsonl", encoding="utf-8") as f:
        sci_train = [json.loads(line) for line in f if line.strip()]

    with open(REPO_ROOT / "suite" / "validation" / "knowledge_mcq.jsonl", encoding="utf-8") as f:
        know_val = [json.loads(line) for line in f if line.strip()]
    with open(REPO_ROOT / "suite" / "train" / "knowledge_mcq.jsonl", encoding="utf-8") as f:
        know_train = [json.loads(line) for line in f if line.strip()]

    sci_val_audit = run_heuristic_audit(sci_val, "science_mcq (validation)")
    sci_train_audit = run_heuristic_audit(sci_train, "science_mcq (train)")
    sci_combined_audit = run_heuristic_audit(sci_val + sci_train, "science_mcq (val + train)")

    know_val_audit = run_heuristic_audit(know_val, "knowledge_mcq (validation)")
    know_train_audit = run_heuristic_audit(know_train, "knowledge_mcq (train)")
    know_combined_audit = run_heuristic_audit(know_val + know_train, "knowledge_mcq (val + train)")

    # Sample 30 items for owner inspection
    sci_30 = sample_30_for_review(sci_val, seed=101)
    know_30 = sample_30_for_review(know_val, seed=202)

    audit_report = {
        "pre_registered_failure_criterion": "Heuristic FAILS if 95% Wilson CI lower bound > 25.0%",
        "science_mcq": {
            "validation": sci_val_audit,
            "train": sci_train_audit,
            "combined": sci_combined_audit,
            "decision": "RETAIN" if sci_combined_audit["arm_retained"] else "DROP (PUBLIC-ONLY)",
            "sample_30_for_factual_inspection": sci_30,
        },
        "knowledge_mcq": {
            "validation": know_val_audit,
            "train": know_train_audit,
            "combined": know_combined_audit,
            "decision": "RETAIN" if know_combined_audit["arm_retained"] else "DROP (PUBLIC-ONLY)",
            "sample_30_for_factual_inspection": know_30,
        },
    }

    out_file = REPO_ROOT / "reports" / "step2" / "mcq_artifact_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    print("\n" + "=" * 80)
    print("A3: MCQ ARTIFACT AUDIT RESULTS")
    print("=" * 80)
    for name, audit in [
        ("science_mcq", sci_combined_audit),
        ("knowledge_mcq", know_combined_audit),
    ]:
        print(f"\n--- {name.upper()} (N={audit['total_items']}) ---")
        print(f"Key Distribution: {audit['key_distribution']}")
        print(
            f"Mean Option Length: Correct={audit['mean_correct_option_length']} chars, Incorrect={audit['mean_incorrect_option_length']} chars"
        )
        print(f"Mean Lengths by Label: {audit['mean_lengths_by_label']}")
        for h_name, h_data in audit["heuristics"].items():
            status = "FAILED (>25% lower bound)" if h_data["fails_criterion"] else "PASSED"
            print(
                f"  * {h_name:<20}: {h_data['accuracy']}% [95% CI: {h_data['ci_95']}] -> {status}"
            )
        decision = "RETAINED" if audit["arm_retained"] else "DROPPED -> PUBLIC-ONLY"
        print(f"Verdict for {name} synthetic arm: {decision}")

    print(f"\nWrote full audit and 30-item review samples to {out_file}")


if __name__ == "__main__":
    main()
