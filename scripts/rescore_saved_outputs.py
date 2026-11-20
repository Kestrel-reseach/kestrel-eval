"""Re-score saved raw model outputs with updated extractors (Dev-02).

Performs purely offline, non-GPU re-scoring of Phase C saved validation outputs.
Tracks all score changes by group and arm.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.extractors import extract_answer_for_group


def rescore_run(file_path: Path) -> dict:
    with open(file_path) as f:
        records = [json.loads(line) for line in f]

    changed = []
    before_group = {}
    after_group = {}
    before_arm = {}
    after_arm = {}

    for r in records:
        grp = r.get("group")
        arm = r.get("arm")
        old_corr = r.get("correct", False)

        if grp in ("math", "science_mcq", "knowledge_mcq", "knowledge_qa"):
            ext, new_corr = extract_answer_for_group(r, r.get("raw_output", ""))
        else:
            ext, new_corr = r.get("extracted_answer"), old_corr

        before_group[grp] = before_group.get(grp, 0) + (1 if old_corr else 0)
        after_group[grp] = after_group.get(grp, 0) + (1 if new_corr else 0)

        arm_key = f"{grp}:{arm}"
        before_arm[arm_key] = before_arm.get(arm_key, 0) + (1 if old_corr else 0)
        after_arm[arm_key] = after_arm.get(arm_key, 0) + (1 if new_corr else 0)

        if old_corr != new_corr:
            changed.append(
                {
                    "item_id": r["item_id"],
                    "group": grp,
                    "arm": arm,
                    "old_correct": old_corr,
                    "new_correct": new_corr,
                    "target": r.get("target"),
                    "old_ext": r.get("extracted_answer"),
                    "new_ext": ext,
                }
            )

    return {
        "file": str(file_path),
        "total_items": len(records),
        "changed_items": changed,
        "before_group": before_group,
        "after_group": after_group,
        "before_arm": before_arm,
        "after_arm": after_arm,
        "before_total_correct": sum(before_group.values()),
        "after_total_correct": sum(after_group.values()),
    }


def main():
    models = ["0.5b", "1.5b"]
    for m in models:
        path = Path(f"reports/step2/run_qwen2.5-{m}-instruct-q4_validation.jsonl")
        res = rescore_run(path)
        print(f"=== Results for Qwen2.5-{m}-Instruct NF4 ===")
        print(
            f"Total correct: {res['before_total_correct']} -> {res['after_total_correct']} (delta: {res['after_total_correct'] - res['before_total_correct']:+d})"
        )
        print(f"Total changed items: {len(res['changed_items'])}")
        for c in res["changed_items"]:
            print(
                f"  [{c['item_id']}] ({c['group']}/{c['arm']}) {c['old_correct']} -> {c['new_correct']}: target={c['target']!r}, new_ext={c['new_ext']!r}"
            )
        print("Group Breakdown (Before -> After):")
        for g in sorted(res["before_group"].keys()):
            b_cnt = res["before_group"][g]
            a_cnt = res["after_group"][g]
            print(f"  {g:15s}: {b_cnt:3d} -> {a_cnt:3d} ({a_cnt - b_cnt:+d})")
        print("Arm Breakdown (Before -> After):")
        for a in sorted(res["before_arm"].keys()):
            b_cnt = res["before_arm"][a]
            a_cnt = res["after_arm"][a]
            print(f"  {a:30s}: {b_cnt:3d} -> {a_cnt:3d} ({a_cnt - b_cnt:+d})")
        print()


if __name__ == "__main__":
    main()
