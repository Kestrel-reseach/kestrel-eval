"""Analyze near-duplicate prompt pairs across partitions per group (3B-5).

CRITICAL DISCIPLINE:
- Locked partition pairs: COUNTS ONLY.
- Validation and train pairs: Detailed top 5 pairs.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from evaluation.leakage import check_near_duplicates  # noqa: E402

GROUPS = ("math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe")


def load_partition_file(path: Path) -> list[dict[str, Any]]:
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def main():
    repo_root = Path(__file__).resolve().parent.parent
    private_dir = Path(
        os.environ.get("KESTREL_PRIVATE_DIR", "/home/ash09/project_x/kestrel_private")
    ).resolve()
    locked_dir = private_dir / "locked_test"

    threshold = 0.85

    print(
        f"=== Near-Duplicate Analysis across 3,600 Items (4-gram Jaccard Threshold: {threshold}) ==="
    )

    for grp in GROUPS:
        val_file = repo_root / "suite" / "validation" / f"{grp}.jsonl"
        train_file = repo_root / "suite" / "train" / f"{grp}.jsonl"
        lock_file = locked_dir / f"{grp}.jsonl"

        val_items = load_partition_file(val_file)
        train_items = load_partition_file(train_file)
        lock_items = load_partition_file(lock_file)

        # 1. Val vs Train
        val_train_dups = check_near_duplicates(val_items, train_items, threshold=threshold)

        # 2. Val vs Locked
        val_lock_dups = check_near_duplicates(val_items, lock_items, threshold=threshold)

        # 3. Train vs Locked
        train_lock_dups = check_near_duplicates(train_items, lock_items, threshold=threshold)

        total_cross_dups = len(val_train_dups) + len(val_lock_dups) + len(train_lock_dups)

        print(f"\n--- Group: {grp} ---")
        print(f"Sizes: Val={len(val_items)}, Train={len(train_items)}, Locked={len(lock_items)}")
        print(f"Cross-partition pairs >= {threshold}:")
        print(f"  Validation vs Train: {len(val_train_dups)} pairs")
        print(f"  Validation vs Locked: {len(val_lock_dups)} pairs (count only)")
        print(f"  Train vs Locked:      {len(train_lock_dups)} pairs (count only)")
        print(f"  Total Cross-Partition Near-Duplicates: {total_cross_dups}")

        if val_train_dups:
            sorted_vt = sorted(val_train_dups, key=lambda x: x["similarity"], reverse=True)
            print("  Top Validation vs Train pairs:")
            for p in sorted_vt[:5]:
                print(f"    - {p['id_a']} vs {p['id_b']} (sim={p['similarity']:.4f})")
                print(f"      Prompt A: {p['prompt_a']}")
                print(f"      Prompt B: {p['prompt_b']}")


if __name__ == "__main__":
    main()
