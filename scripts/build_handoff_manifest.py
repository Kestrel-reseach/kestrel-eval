"""Build SHA-256 handoff manifest of all committed artifacts (Step 2 Part 5a)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    tracked_patterns = [
        "evaluation/manifest.yaml",
        "docs/decisions/scoring_spec.md",
        "docs/decisions/owner_decisions.md",
        "docs/decisions/proposals/D18_bllm_selection_proposal.md",
        "docs/handoff/A_to_B_step2.md",
        "data/wikipedia_abstracts_5k.jsonl",
        "data/fictional_abstracts_corpus.jsonl",
        "suite/validation/*.jsonl",
        "suite/train/*.jsonl",
        "reports/step2/*.md",
    ]

    files_to_hash = []
    for pattern in tracked_patterns:
        if "*" in pattern:
            files_to_hash.extend(sorted(REPO_ROOT.glob(pattern)))
        else:
            p = REPO_ROOT / pattern
            if p.exists():
                files_to_hash.append(p)

    manifest_entries = {}
    for p in files_to_hash:
        rel = str(p.relative_to(REPO_ROOT))
        # Never hash locked files contents directly into public manifests if sensitive
        if "locked" in rel:
            continue
        manifest_entries[rel] = {
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }

    out_path = REPO_ROOT / "docs/handoff/handoff_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "manifest_version": "2.2",
                "generated_at": "2026-11-20",
                "total_tracked_files": len(manifest_entries),
                "artifacts": manifest_entries,
            },
            f,
            indent=2,
        )

    print(f"Handoff manifest generated: {out_path} ({len(manifest_entries)} files)")


if __name__ == "__main__":
    main()

