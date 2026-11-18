"""Unit tests for Suite v0 loader, permission guards, and partition integrity (Step 1)."""

from __future__ import annotations

import pytest

from evaluation.suite import GROUP_SIZES, load_suite_partition


def test_load_suite_partition_validation_full():
    """Verify loading the full validation partition returns exactly 1200 items."""
    items = load_suite_partition(split="validation")
    assert len(items) == 1200

    group_counts: dict[str, int] = {}
    for item in items:
        assert item["split"] == "validation"
        assert "prompt" in item and len(item["prompt"]) > 0
        assert "target" in item and item["target"] is not None
        assert "answer_check" in item
        assert "id" in item
        assert "item_id" in item
        grp = item["group"]
        group_counts[grp] = group_counts.get(grp, 0) + 1

    for grp, expected_count in GROUP_SIZES.items():
        assert (
            group_counts[grp] == expected_count
        ), f"Group {grp} count mismatch: {group_counts[grp]} vs {expected_count}"


def test_load_suite_partition_individual_groups():
    """Verify loading each group individually from validation partition."""
    for grp, expected_count in GROUP_SIZES.items():
        grp_items = load_suite_partition(split="validation", group=grp)
        assert len(grp_items) == expected_count
        for item in grp_items:
            assert item["group"] == grp
            assert item["split"] == "validation"


def test_load_suite_partition_train():
    """Verify loading the train partition returns exactly 1200 items."""
    items = load_suite_partition(split="train")
    assert len(items) == 1200
    for item in items:
        assert item["split"] == "train"


def test_load_suite_partition_locked_test_guard(monkeypatch: pytest.MonkeyPatch):
    """Verify locked-test split raises PermissionError without KESTREL_ALLOW_LOCKED_TEST=1."""
    monkeypatch.delenv("KESTREL_ALLOW_LOCKED_TEST", raising=False)
    with pytest.raises(PermissionError, match="Access to locked-test partition is forbidden"):
        load_suite_partition(split="locked_test")

    monkeypatch.setenv("KESTREL_ALLOW_LOCKED_TEST", "0")
    with pytest.raises(PermissionError, match="Access to locked-test partition is forbidden"):
        load_suite_partition(split="locked_test")


def test_load_suite_partition_locked_test_allowed(monkeypatch: pytest.MonkeyPatch):
    """Verify locked-test split loads items when KESTREL_ALLOW_LOCKED_TEST=1."""
    from evaluation.suite import get_private_dir

    if not (get_private_dir() / "locked_test" / "math.jsonl").exists():
        pytest.skip("Locked test partition files not present on CI runner")
    monkeypatch.setenv("KESTREL_ALLOW_LOCKED_TEST", "1")
    items = load_suite_partition(split="locked_test")
    assert len(items) == 1200
    for item in items:
        assert item["split"] == "locked_test"


def test_load_suite_partition_invalid_args():
    """Verify invalid split and group names raise ValueError."""
    with pytest.raises(ValueError, match="Unknown split"):
        load_suite_partition(split="nonexistent_split")

    with pytest.raises(ValueError, match="Unknown group"):
        load_suite_partition(split="validation", group="unknown_grp")
