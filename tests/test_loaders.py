"""Unit tests for public evaluation suite loaders (PR 1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.loaders import (
    MMLU_10_SUBJECTS,
    PUBLIC_SOURCES,
    check_answer_key,
    check_exact_numeric,
    check_unit_tests_pass,
    get_source_metadata,
    load_code_items_from_jsonl,
    load_knowledge_mcq_items_from_jsonl,
    load_math_items_from_jsonl,
    load_science_mcq_items_from_jsonl,
    verify_code_item,
    verify_knowledge_mcq_item,
    verify_math_item,
    verify_science_mcq_item,
)

# ── 1. Sources & License Registry Tests ──────────────────────────────────────


def test_public_sources_registered() -> None:
    expected_keys = {"gsm8k", "arc_challenge", "mmlu", "humaneval", "mbpp"}
    assert expected_keys.issubset(set(PUBLIC_SOURCES.keys()))


def test_public_sources_have_verified_licenses() -> None:
    for key, meta in PUBLIC_SOURCES.items():
        assert meta.license != "UNVERIFIED", f"Source {key} must have verified license"
        assert meta.license in {"MIT", "CC BY-SA 4.0", "CC BY 4.0"}
        assert meta.url.startswith("https://")
        assert meta.license_url.startswith("https://")
        assert meta.verified_on_official_page is True
        assert meta.permissible is True
        assert len(meta.contamination_risk) > 0


def test_get_source_metadata_raises_on_unknown() -> None:
    with pytest.raises(KeyError, match="Unknown source 'unknown_set'"):
        get_source_metadata("unknown_set")


# ── 2. Answer Checking Helpers Tests ─────────────────────────────────────────


@pytest.mark.parametrize(
    ("pred", "target", "expected"),
    [
        (42, 42, True),
        ("42", "42", True),
        ("The answer is 42", "42", True),
        ("The answer is #### 42", "#### 42", True),
        ("42.0001", "42.0", True),
        ("-15", "-15", True),
        ("$100", "100", True),
        ("42", "43", False),
        ("No number here", "42", False),
    ],
)
def test_check_exact_numeric(
    pred: str | int | float, target: str | int | float, expected: bool
) -> None:
    assert check_exact_numeric(pred, target) is expected


@pytest.mark.parametrize(
    ("pred", "target", "expected"),
    [
        ("A", "A", True),
        ("(A)", "A", True),
        ("Option A", "A", True),
        ("Answer: B", "B", True),
        ("b", "B", True),
        ("C) description", "C", True),
        ("D", "A", False),
        ("Invalid response", "A", False),
    ],
)
def test_check_answer_key(pred: str, target: str, expected: bool) -> None:
    assert check_answer_key(pred, target) is expected


def test_check_unit_tests_pass() -> None:
    good_code = "def add(a, b):\n    return a + b\n"
    bad_code = "def add(a, b):\n    return a - b\n"
    syntax_error = "def add(a, b):\n    return a +\n"
    test_code = "assert add(2, 3) == 5\nassert add(-1, 1) == 0\n"

    assert check_unit_tests_pass(good_code, test_code) is True
    assert check_unit_tests_pass(bad_code, test_code) is False
    assert check_unit_tests_pass(syntax_error, test_code) is False


# ── 3. Math Loader Tests (GSM8K) ─────────────────────────────────────────────


def test_math_loader_with_sample_file() -> None:
    sample_path = Path("suite/public/math/sample.jsonl")
    assert sample_path.is_file()

    items = load_math_items_from_jsonl(sample_path)
    assert len(items) == 3

    item = items[0]
    assert item["item_id"] == "math-0001"
    assert item["group"] == "math"
    assert item["target"] == "72"
    assert item["answer_check"] == "exact_numeric"
    assert item["metadata"]["source"] == "GSM8K (Grade School Math 8K)"
    assert item["metadata"]["license"] == "MIT"

    # Verification function
    for it in items:
        errors = verify_math_item(it)
        assert errors == [], f"Errors for {it['item_id']}: {errors}"


# ── 4. Science MCQ Loader Tests (ARC) ────────────────────────────────────────


def test_science_mcq_loader_with_sample_file() -> None:
    sample_path = Path("suite/public/science_mcq/sample.jsonl")
    assert sample_path.is_file()

    items = load_science_mcq_items_from_jsonl(sample_path)
    assert len(items) == 3

    item = items[0]
    assert item["item_id"] == "science_mcq-0001"
    assert item["group"] == "science_mcq"
    assert item["target"] == "A"
    assert item["answer_check"] == "answer_key"
    assert len(item["choices"]) == 4
    assert item["metadata"]["license"] == "CC BY-SA 4.0"

    for it in items:
        errors = verify_science_mcq_item(it)
        assert errors == [], f"Errors for {it['item_id']}: {errors}"


# ── 5. Knowledge MCQ Loader Tests (MMLU) ─────────────────────────────────────


def test_knowledge_mcq_loader_with_sample_file() -> None:
    sample_path = Path("suite/public/knowledge_mcq/sample.jsonl")
    assert sample_path.is_file()

    items = load_knowledge_mcq_items_from_jsonl(sample_path)
    assert len(items) == 3

    item = items[0]
    assert item["item_id"] == "knowledge_mcq-0001"
    assert item["group"] == "knowledge_mcq"
    assert item["target"] == "B"
    assert item["answer_check"] == "answer_key"
    assert len(item["choices"]) == 4
    assert item["metadata"]["subject"] == "college_computer_science"
    assert item["metadata"]["license"] == "MIT"

    for it in items:
        errors = verify_knowledge_mcq_item(it)
        assert errors == [], f"Errors for {it['item_id']}: {errors}"


def test_mmlu_10_subjects_list() -> None:
    assert len(MMLU_10_SUBJECTS) == 10
    assert "college_computer_science" in MMLU_10_SUBJECTS
    assert "econometrics" in MMLU_10_SUBJECTS


# ── 6. Code Loader Tests (HumanEval / MBPP) ──────────────────────────────────


def test_code_loader_with_sample_file() -> None:
    sample_path = Path("suite/public/code/sample.jsonl")
    assert sample_path.is_file()

    items = load_code_items_from_jsonl(sample_path)
    assert len(items) == 2

    item = items[0]
    assert item["item_id"] == "code-0001"
    assert item["group"] == "code"
    assert item["answer_check"] == "unit_tests_pass"
    assert item["metadata"]["entry_point"] == "has_close_elements"
    assert item["metadata"]["license"] == "MIT"

    for it in items:
        errors = verify_code_item(it, run_unit_tests=True)
        assert errors == [], f"Errors for {it['item_id']}: {errors}"
