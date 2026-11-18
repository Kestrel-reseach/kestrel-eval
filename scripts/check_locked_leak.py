"""Check tracked repo files and git history for locked test item IDs or prompts.

CRITICAL DISCIPLINE:
- Count-only and ID-only.
- Never prints prompt or target content from locked items.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parent.parent
    private_dir = Path(
        os.environ.get("KESTREL_PRIVATE_DIR", "/home/ash09/project_x/kestrel_private")
    ).resolve()
    locked_dir = private_dir / "locked_test"

    if not locked_dir.exists():
        print(f"ERROR: locked directory does not exist: {locked_dir}")
        return

    locked_ids: set[str] = set()
    total_locked_items = 0

    for jsonl_file in sorted(locked_dir.glob("*.jsonl")):
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total_locked_items += 1
                it = json.loads(line)
                iid = it.get("id") or it.get("item_id")
                if iid:
                    locked_ids.add(iid)

    print(f"Total locked-test items read from private dir: {total_locked_items}")
    print(f"Unique locked IDs: {len(locked_ids)}")

    # 1. Check currently tracked git files
    cmd = ["git", "ls-files"]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)
    tracked_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]

    leaked_files: dict[str, list[str]] = {}

    for rel_path in tracked_files:
        full_path = repo_root / rel_path
        if not full_path.is_file():
            continue
        try:
            content = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        found_in_file = [iid for iid in locked_ids if iid in content]
        if found_in_file:
            leaked_files[rel_path] = sorted(found_in_file)

    print("\n--- Tracked File Search Results ---")
    if leaked_files:
        print(f"Found {len(leaked_files)} tracked file(s) containing locked IDs:")
        for path, ids in leaked_files.items():
            print(f"  {path}: {len(ids)} locked item ID(s) found: {ids}")
    else:
        print("Zero tracked files contain locked item IDs.")

    # 2. Check git history for locked ID prefixes
    print("\n--- Git History Commit Check ---")
    prefixes = ("math_lock_", "sci_lock_", "know_lock_", "code_lock_", "kqa_lock_", "mem_lock_")
    grep_cmd = ["git", "log", "-G", "|".join(prefixes), "--oneline"]
    grep_res = subprocess.run(grep_cmd, cwd=repo_root, capture_output=True, text=True)
    commits = grep_res.stdout.strip().splitlines()
    print(f"Found {len(commits)} commit(s) touching locked ID prefixes in git history:")
    for c in commits:
        print(f"  {c}")


if __name__ == "__main__":
    main()
