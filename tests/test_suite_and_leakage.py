"""Tests for evaluation suite partitioning, hashing, leakage, and out-of-repo isolation (PR 4)."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import yaml

from evaluation.leakage import (
    check_answer_leakage,
    check_exact_prompt_duplicates,
    check_near_duplicates,
    check_no_id_overlap,
)
from evaluation.suite import compute_file_sha256, compute_root_hash, get_private_dir

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_partition_files_exist_and_counts():
    """Verify that validation and train partitions have exactly the D1 group counts."""
    expected_counts = {
        "math": 200,
        "science_mcq": 200,
        "knowledge_mcq": 300,
        "code": 100,
        "knowledge_qa": 300,
        "memory_probe": 100,
    }

    for split in ["validation", "train"]:
        split_dir = REPO_ROOT / "suite" / split
        assert split_dir.exists(), f"Directory {split_dir} does not exist"
        total_items = 0
        for grp, exp_count in expected_counts.items():
            file_path = split_dir / f"{grp}.jsonl"
            assert file_path.exists(), f"Missing {file_path}"
            with open(file_path, encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            assert (
                len(lines) == exp_count
            ), f"{grp} in {split} has {len(lines)} items, expected {exp_count}"
            total_items += len(lines)
        assert total_items == 1200, f"Total items in {split} is {total_items}, expected 1200"


def test_no_locked_test_data_in_repo():
    """Crucial security & integrity test: locked-test data files must NEVER be in repo."""
    # 1. Directory must not exist in repo root or suite/
    assert not (
        REPO_ROOT / "suite" / "locked_test"
    ).exists(), "suite/locked_test must NOT exist in repo!"
    assert not (REPO_ROOT / "locked_test").exists(), "locked_test must NOT exist in repo root!"

    # 2. Git must not track any locked_test data files
    res = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked_files = res.stdout.splitlines()
    for f in tracked_files:
        assert not f.endswith("locked_test.jsonl"), f"Forbidden locked test file tracked: {f}"
        assert "suite/locked_test" not in f, f"Forbidden suite/locked_test tracked: {f}"


def test_manifest_locked_hashes_match():
    """Verify locked-test partition file hashes and root_hash match manifest.yaml."""
    manifest_path = REPO_ROOT / "evaluation" / "manifest.yaml"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    private_dir = get_private_dir()
    locked_dir = private_dir / "locked_test"
    assert locked_dir.exists(), f"Private locked_test dir {locked_dir} does not exist"

    manifest_hashes = manifest.get("locked_test_hashes", {})
    manifest_root = manifest.get("root_hash")

    computed_hashes = {}
    for grp in ["math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe"]:
        fp = locked_dir / f"{grp}.jsonl"
        assert fp.exists(), f"Private locked file {fp} does not exist"
        h = compute_file_sha256(fp)
        computed_hashes[grp] = h
        assert h == manifest_hashes[grp], f"Hash mismatch for {grp}: {h} != {manifest_hashes[grp]}"

    computed_root = compute_root_hash(computed_hashes)
    assert computed_root == manifest_root, f"Root hash mismatch: {computed_root} != {manifest_root}"


def test_partition_leakage_and_duplicates_clean():
    """Verify zero ID overlap, zero exact prompt duplicates across all 3 partitions."""
    private_dir = get_private_dir()
    locked_dir = private_dir / "locked_test"

    partitions: dict[str, list[dict]] = {"validation": [], "train": [], "locked_test": []}

    for split in ["validation", "train"]:
        for grp in ["math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe"]:
            with open(REPO_ROOT / "suite" / split / f"{grp}.jsonl", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        partitions[split].append(json.loads(line))

    for grp in ["math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe"]:
        with open(locked_dir / f"{grp}.jsonl", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    partitions["locked_test"].append(json.loads(line))

    # 1. Zero ID overlap
    check_no_id_overlap(partitions)

    # 2. Zero exact prompt duplicates across partitions
    dups = check_exact_prompt_duplicates(partitions)
    assert len(dups) == 0, f"Found {len(dups)} duplicate prompts across partitions: {dups[:3]}"

    # 3. Check answer leakage
    for split_name, items in partitions.items():
        leaks = check_answer_leakage(items)
        assert len(leaks) == 0, f"Answer leakage detected in {split_name}: {leaks[:3]}"


def test_near_duplicates_detector():
    """Test character 4-gram Jaccard near-duplicate detection."""
    items_a = [
        {"id": "a1", "prompt": "What is the speed of sound in air at 20 degrees Celsius?"},
        {"id": "a2", "prompt": "Compute the derivative of f(x) = sin(x) with respect to x."},
    ]
    # Identical text -> similarity 1.0 -> flagged
    items_b = [
        {"id": "b1", "prompt": "What is the speed of sound in air at 20 degrees Celsius?"},
        {"id": "b2", "prompt": "Completely unrelated question about Roman architecture."},
    ]
    near_dups = check_near_duplicates(items_a, items_b, threshold=0.85)
    assert len(near_dups) == 1
    assert near_dups[0]["id_a"] == "a1"
    assert near_dups[0]["id_b"] == "b1"
    assert near_dups[0]["similarity"] == 1.0


def test_binomial_confidence_interval_widths():
    """Validate 95% confidence interval half-widths per group (Decision D1)."""

    # Formula: 1.96 * sqrt(p*(1-p)/N) with worst-case p=0.5
    def half_width_pp(n: int) -> float:
        return 1.96 * math.sqrt(0.25 / n) * 100

    hw_100 = half_width_pp(100)
    hw_200 = half_width_pp(200)
    hw_300 = half_width_pp(300)
    hw_1200 = half_width_pp(1200)

    assert round(hw_100, 2) == 9.80  # code, memory_probe
    assert round(hw_200, 2) == 6.93  # math, science_mcq
    assert round(hw_300, 2) == 5.66  # knowledge_mcq, knowledge_qa
    assert round(hw_1200, 2) == 2.83  # total locked-test partition
