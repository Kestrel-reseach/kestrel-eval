"""Automated test enforcing that no locked-test item IDs appear in reports/ or docs/."""

from __future__ import annotations

import json
import os
from pathlib import Path


def test_no_locked_ids_in_reports_or_docs():
    """Verify that zero files under reports/ or docs/ mention any locked test item ID."""
    repo_root = Path(__file__).resolve().parent.parent
    private_dir = Path(
        os.environ.get("KESTREL_PRIVATE_DIR", "/home/ash09/project_x/kestrel_private")
    ).resolve()
    locked_dir = private_dir / "locked_test"

    if not locked_dir.exists():
        return

    locked_ids: set[str] = set()
    for jsonl_file in sorted(locked_dir.glob("*.jsonl")):
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                it = json.loads(line)
                iid = it.get("id") or it.get("item_id")
                if iid:
                    locked_ids.add(iid)

    assert len(locked_ids) > 0, "Expected locked IDs in private directory"

    scanned_dirs = [repo_root / "reports", repo_root / "docs"]
    leaked: dict[str, list[str]] = {}

    for d in scanned_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if not p.is_file() or p.name.startswith("."):
                continue
            if p.suffix in (".pyc", ".png", ".jpg", ".bz2", ".gz"):
                continue
            try:
                content = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            found = [iid for iid in locked_ids if iid in content]
            if found:
                leaked[str(p.relative_to(repo_root))] = found

    assert (
        not leaked
    ), f"Security violation: locked item IDs found in documentation/reports: {leaked}"
