"""Automated tests asserting partition independence and unique questions only across all splits."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _get_partitions() -> dict[str, list[dict]]:
    repo_root = Path(__file__).resolve().parent.parent
    env_dir = os.environ.get("KESTREL_PRIVATE_DIR")
    if env_dir:
        private_dir = Path(env_dir).resolve()
    else:
        private_dir = (repo_root.parent / "kestrel_private").resolve()

    partitions: dict[str, list[dict]] = {}
    for split in ("validation", "train"):
        sdir = repo_root / "suite" / split
        items = []
        for p in sorted(sdir.glob("*.jsonl")):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        items.append(json.loads(line))
        partitions[split] = items

    locked_dir = private_dir / "locked_test"
    if locked_dir.exists() and (locked_dir / "math.jsonl").exists():
        items = []
        for p in sorted(locked_dir.glob("*.jsonl")):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        items.append(json.loads(line))
        partitions["locked_test"] = items

    return partitions


def test_unique_questions_within_each_partition():
    """Verify that every partition contains zero internal question/prompt duplicates."""
    partitions = _get_partitions()
    assert len(partitions) >= 2, "Expected at least validation and train partitions"

    for split_name, items in partitions.items():
        seen_prompts: set[str] = set()
        duplicates: list[str] = []
        for it in items:
            p_norm = " ".join(it.get("prompt", "").lower().split())
            if p_norm in seen_prompts:
                duplicates.append(it.get("item_id") or it.get("id"))
            seen_prompts.add(p_norm)

        assert not duplicates, f"Found {len(duplicates)} duplicate prompts within partition {split_name}: {duplicates[:5]}"


def test_zero_question_overlap_across_partitions():
    """Verify that zero question/prompt overlap exists across validation, train, and locked partitions."""
    partitions = _get_partitions()
    split_names = list(partitions.keys())

    prompts_by_split: dict[str, dict[str, str]] = {}
    for s_name, items in partitions.items():
        prompts_by_split[s_name] = {
            " ".join(it.get("prompt", "").lower().split()): (it.get("item_id") or it.get("id"))
            for it in items
        }

    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            s1, s2 = split_names[i], split_names[j]
            overlap = set(prompts_by_split[s1].keys()) & set(prompts_by_split[s2].keys())
            overlapping_ids = [(prompts_by_split[s1][p], prompts_by_split[s2][p]) for p in overlap]
            assert not overlap, f"Cross-partition prompt overlap detected between {s1} and {s2}: {overlapping_ids[:5]}"
