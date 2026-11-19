"""Compute suite composition table across groups and partitions.
Analyzes validation and train partitions directly from suite/ JSONL files.
Never opens kestrel_private/locked_test.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

GROUPS = [
    "math",
    "science_mcq",
    "knowledge_mcq",
    "code",
    "knowledge_qa",
    "memory_probe",
]


def analyze_partition(split: str) -> dict[str, dict]:
    split_dir = REPO_ROOT / "suite" / split
    res = {}
    for grp in GROUPS:
        p = split_dir / f"{grp}.jsonl"
        if not p.exists():
            continue
        items = []
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))

        # Detect source type and family
        families = Counter()
        source_type = "synthetic"  # default

        if grp == "math":
            source_type = "synthetic"
            for it in items:
                fam = (
                    it.get("template")
                    or it.get("family")
                    or it.get("metadata", {}).get("template", "procedural_math")
                )
                families[fam] += 1
        elif grp == "code":
            source_type = "synthetic"
            for it in items:
                fam = it.get("family") or it.get("metadata", {}).get("family", "procedural_code")
                families[fam] += 1
        elif grp == "science_mcq":
            # Procedural generator stand-in tagged as arc_challenge
            source_type = "stand-in"
            for it in items:
                fam = it.get("domain") or it.get("metadata", {}).get("domain", "science_topic")
                families[fam] += 1
        elif grp == "knowledge_mcq":
            # Procedural generator stand-in tagged as mmlu
            source_type = "stand-in"
            for it in items:
                fam = it.get("subject") or it.get("metadata", {}).get("subject", "mmlu_subject")
                families[fam] += 1
        elif grp == "knowledge_qa":
            # Extracted from Wikipedia dump
            source_type = "verified real (Wikipedia)"
            for it in items:
                fam = it.get("rule_family") or "wikipedia_qa"
                families[fam] += 1
        elif grp == "memory_probe":
            source_type = "synthetic"
            for it in items:
                fam = (
                    "stale_fact"
                    if it.get("is_stale_fact") or it.get("metadata", {}).get("is_stale_fact")
                    else "normal"
                )
                families[fam] += 1

        top_fam, top_count = families.most_common(1)[0] if families else ("none", 0)
        share = (top_count / len(items)) * 100 if items else 0.0

        res[grp] = {
            "count": len(items),
            "source_type": source_type,
            "family_count": len(families),
            "families": dict(families),
            "largest_family": top_fam,
            "largest_share": round(share, 1),
        }
    return res


def main() -> None:
    val_analysis = analyze_partition("validation")
    train_analysis = analyze_partition("train")

    combined = {
        "validation": val_analysis,
        "train": train_analysis,
    }

    out_file = REPO_ROOT / "reports" / "step2" / "suite_composition_analysis.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    print("=== SUITE COMPOSITION ANALYSIS ===")
    print(
        f"{'Group':<15} | {'Split':<10} | {'Count':<6} | {'Source Type':<25} | {'Families':<8} | {'Largest Family (Share)'}"
    )
    print("-" * 95)
    for split, analysis in [("validation", val_analysis), ("train", train_analysis)]:
        for grp, data in analysis.items():
            print(
                f"{grp:<15} | {split:<10} | {data['count']:<6} | {data['source_type']:<25} | {data['family_count']:<8} | {data['largest_family']} ({data['largest_share']}%)"
            )


if __name__ == "__main__":
    main()
