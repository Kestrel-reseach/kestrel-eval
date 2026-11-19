"""Automated test enforcing that no locked-test item IDs, retired entities, or values appear in repo."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

RETIRED_LOCKED_PERSONAS: list[str] = [
    "Valerius Thorne",
    "Elowen Morvath",
    "Thaddeus Vance",
    "Seraphina Solis",
    "Corin Vane",
    "Aurelia Voss",
    "Kaelen Drake",
    "Isolde Blackwood",
    "Dorian Ravenscroft",
    "Lyra Pendelton",
    "Caspian Sterling",
    "Zephyrina Cross",
    "Magnus Winterbourne",
    "Rowena Darkwater",
    "Theron Ashford",
    "Sylvia Nightshade",
    "Bastian Lockridge",
    "Evadne Starling",
    "Gideon Hawkwood",
    "Marcellus Silverton",
    "Helena Foxglove",
    "Lucian Emberfell",
    "Cordelia Frost",
    "Leander Stormont",
    "Vespera Moon",
]

RETIRED_LOCKED_AWARDS: list[str] = [
    "Grand Astral Medal",
    "Royal Verdant Order",
    "Imperial Cornerstone Award",
    "Alchemical Laurel",
    "Grand Symphony Cross",
    "Sol Invictus Medal",
    "Terra Firma Prize",
    "Silver Quill of Honor",
    "Golden Palette Award",
    "Euler Circle Medal",
    "Iron Gear Trophy",
    "Caduceus Order of Merit",
    "Chronicle Society Laurel",
    "Grand Literary Crest",
    "Concordat Peace Plaque",
    "Linnaean Laurel Medal",
    "Chisel and Stone Prize",
    "Celestial Horizon Award",
    "Civic Defender Cross",
    "Athenaeum Wisdom Medallion",
    "Prismatic Flask Trophy",
    "Grand Vault Pillar Award",
    "Arboretum Gold Crest",
    "Harmonic Lyre Distinction",
    "Quantum Lattice Prize",
]


def test_no_locked_ids_in_reports_or_docs():
    """Verify that zero files under reports/ or docs/ mention any locked test item ID."""
    repo_root = Path(__file__).resolve().parent.parent
    env_dir = os.environ.get("KESTREL_PRIVATE_DIR")
    if env_dir:
        private_dir = Path(env_dir).resolve()
    else:
        private_dir = (repo_root.parent / "kestrel_private").resolve()
    locked_dir = private_dir / "locked_test"

    if not locked_dir.exists() or not (locked_dir / "math.jsonl").exists():
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


def test_no_retired_locked_entities_or_values_in_tracked_files():
    """Verify that no retired locked entity names or awards appear in any tracked repo file."""
    repo_root = Path(__file__).resolve().parent.parent
    res = subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True)
    if res.returncode != 0:
        return

    tracked_files = [repo_root / f for f in res.stdout.splitlines()]
    leaked: dict[str, list[str]] = {}

    for p in tracked_files:
        if not p.is_file() or p.suffix in (".png", ".jpg", ".bz2", ".gz", ".pyc"):
            continue
        # Skip the leak guard test file itself which declares the banned list
        if p.name == "test_leak_guard.py":
            continue
        try:
            content = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        matches = [n for n in RETIRED_LOCKED_PERSONAS + RETIRED_LOCKED_AWARDS if n in content]
        if matches:
            leaked[str(p.relative_to(repo_root))] = matches

    assert (
        not leaked
    ), f"Security violation: retired locked entity names or values found in tracked files: {leaked}"


def test_no_retired_locked_entities_in_git_commits():
    """Verify that no retired locked entity names or awards appear in any git commit description."""
    repo_root = Path(__file__).resolve().parent.parent
    res = subprocess.run(
        ["git", "log", "--format=%B"], cwd=repo_root, capture_output=True, text=True
    )
    if res.returncode != 0:
        return

    commit_text = res.stdout.lower()
    leaked = [
        n for n in RETIRED_LOCKED_PERSONAS + RETIRED_LOCKED_AWARDS if n.lower() in commit_text
    ]

    assert not leaked, f"Security violation: retired locked entity names or values found in commit messages: {leaked}"
