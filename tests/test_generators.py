"""Unit tests for synthetic generators and stale-fact scorer (PR 2)."""

from __future__ import annotations

from evaluation.generators import (
    generate_code_suite,
    generate_math_suite,
    generate_memory_probe_suite,
    score_memory_probe_response,
)
from evaluation.loaders import (
    check_exact_numeric,
    verify_code_item,
    verify_math_item,
)

# ── 1. Synthetic Math Generator Tests ─────────────────────────────────────────


def test_math_generator_determinism() -> None:
    suite1 = generate_math_suite(n_items=10, seed=42)
    suite2 = generate_math_suite(n_items=10, seed=42)
    suite3 = generate_math_suite(n_items=10, seed=99)

    assert len(suite1) == 10
    # Bitwise identical under same seed
    for it1, it2 in zip(suite1, suite2, strict=False):
        assert it1["prompt"] == it2["prompt"]
        assert it1["target"] == it2["target"]
        assert it1["item_id"] == it2["item_id"]

    # Different seeds produce different problems
    assert suite1[0]["prompt"] != suite3[0]["prompt"]


def test_math_generator_validates_items() -> None:
    suite = generate_math_suite(n_items=25, seed=20260101)
    for it in suite:
        errors = verify_math_item(it)
        assert errors == [], f"Validation errors for {it['item_id']}: {errors}"
        # Assert exact numeric check matches target
        assert check_exact_numeric(it["target"], it["target"]) is True


# ── 2. Memory Probe Generator Tests (D3) ──────────────────────────────────────


def test_memory_probe_suite_proportions() -> None:
    suite = generate_memory_probe_suite(n_items=100, stale_fact_count=30, seed=20260101)
    assert len(suite) == 100

    stale_items = [it for it in suite if it["metadata"]["is_stale_fact"]]
    static_items = [it for it in suite if not it["metadata"]["is_stale_fact"]]

    assert len(stale_items) == 30
    assert len(static_items) == 70

    # Verify stale items have chronological events and old values
    for it in stale_items:
        assert len(it["metadata"]["stale_values"]) >= 2
        assert it["target"] not in it["metadata"]["stale_values"]
        events = it["metadata"]["events"]
        assert len(events) == 3
        # Chronological timestamps
        t0, t1, t2 = events[0]["timestamp"], events[1]["timestamp"], events[2]["timestamp"]
        assert t0 < t1 < t2


def test_memory_probe_determinism() -> None:
    suite1 = generate_memory_probe_suite(n_items=5, stale_fact_count=2, seed=123)
    suite2 = generate_memory_probe_suite(n_items=5, stale_fact_count=2, seed=123)
    for it1, it2 in zip(suite1, suite2, strict=False):
        assert it1["target"] == it2["target"]
        assert it1["prompt"] == it2["prompt"]


# ── 3. Stale-Fact Rejection Scorer Tests ───────────────────────────────────────


def test_stale_fact_scorer_correct_latest_value() -> None:
    # Model retrieves latest value
    score = score_memory_probe_response(
        prediction="Your current city of residence is San Francisco.",
        target="San Francisco",
        stale_values=["Austin", "Seattle"],
        is_stale_fact_item=True,
    )
    assert score["correct"] is True
    assert score["score"] == 1.0
    assert score["stale_fact_error"] is False
    assert score["stale_values_found"] == []


def test_stale_fact_scorer_rejects_outdated_value() -> None:
    # Model hallucinates/retrieves the old value
    score = score_memory_probe_response(
        prediction="You live in Austin.",
        target="San Francisco",
        stale_values=["Austin", "Seattle"],
        is_stale_fact_item=True,
    )
    assert score["correct"] is False
    assert score["score"] == 0.0
    assert score["stale_fact_error"] is True
    assert "Austin" in score["stale_values_found"]


def test_stale_fact_scorer_distinguishes_chronological_change() -> None:
    # Model mentions both, but explains you moved from Austin to San Francisco
    score = score_memory_probe_response(
        prediction="You previously lived in Austin, but you recently moved to San Francisco.",
        target="San Francisco",
        stale_values=["Austin", "Seattle"],
        is_stale_fact_item=True,
    )
    assert score["correct"] is True
    assert score["score"] == 1.0
    assert score["stale_fact_error"] is False


def test_stale_fact_scorer_ambiguous_both_values_error() -> None:
    # Model ambiguously states both without recency distinction
    score = score_memory_probe_response(
        prediction="You reside in Austin and San Francisco.",
        target="San Francisco",
        stale_values=["Austin", "Seattle"],
        is_stale_fact_item=True,
    )
    assert score["correct"] is False
    assert score["score"] == 0.0
    assert score["stale_fact_error"] is True


def test_stale_fact_scorer_static_item() -> None:
    score_pass = score_memory_probe_response(
        prediction="Your mother's birthday is May 14.",
        target="May 14",
        stale_values=[],
        is_stale_fact_item=False,
    )
    assert score_pass["correct"] is True
    assert score_pass["score"] == 1.0

    score_fail = score_memory_probe_response(
        prediction="Your mother's birthday is in December.",
        target="May 14",
        stale_values=[],
        is_stale_fact_item=False,
    )
    assert score_fail["correct"] is False
    assert score_fail["score"] == 0.0


# ── 4. Synthetic Code Generator Tests ─────────────────────────────────────────


def test_code_generator_determinism() -> None:
    suite1 = generate_code_suite(n_items=5, seed=42)
    suite2 = generate_code_suite(n_items=5, seed=42)
    suite3 = generate_code_suite(n_items=5, seed=99)

    for it1, it2 in zip(suite1, suite2, strict=False):
        assert it1["prompt"] == it2["prompt"]
        assert it1["target"] == it2["target"]
        assert it1["item_id"] == it2["item_id"]

    # Different seeds produce different problem orderings
    assert [it["prompt"] for it in suite1] != [it["prompt"] for it in suite3]
    assert suite1[0]["item_id"] == "code-synth-0001"


def test_code_generator_all_canonical_solutions_pass() -> None:
    # Generate 15 distinct items and verify that every canonical solution passes its own unit tests
    suite = generate_code_suite(n_items=15, seed=20260101)
    assert len(suite) == 15

    for it in suite:
        errors = verify_code_item(it, run_unit_tests=True)
        assert errors == [], f"Validation errors for {it['item_id']}: {errors}"
