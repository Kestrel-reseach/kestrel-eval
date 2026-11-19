"""Golden fixture test: 100 fixed raw outputs with expected normalized_match correctness.

Enforces scoring integrity (Phase A3 / Step 2 Part H5).
Any future change to extractors or scoring logic that alters these decisions will immediately fail CI.
"""

from __future__ import annotations

import pytest

from evaluation.extractors import extract_answer_for_group

GOLDEN_CASES: list[tuple[dict[str, any], str, bool]] = [
    # ── 1-20: MCQ (Science & Knowledge) ──────────────────────────────────────
    ({"group": "science_mcq", "target": "A", "answer_check": "answer_key"}, "A", True),
    ({"group": "science_mcq", "target": "B", "answer_check": "answer_key"}, "B)", True),
    ({"group": "science_mcq", "target": "C", "answer_check": "answer_key"}, "(C)", True),
    ({"group": "science_mcq", "target": "D", "answer_check": "answer_key"}, "D.", True),
    (
        {"group": "science_mcq", "target": "A", "answer_check": "answer_key"},
        "The correct answer is A) Metamorphic rock",
        True,
    ),
    (
        {"group": "science_mcq", "target": "B", "answer_check": "answer_key"},
        "The correct answer is B.",
        True,
    ),
    ({"group": "science_mcq", "target": "C", "answer_check": "answer_key"}, "Answer: C", True),
    (
        {"group": "science_mcq", "target": "D", "answer_check": "answer_key"},
        "Final Answer: D",
        True,
    ),
    (
        {"group": "science_mcq", "target": "A", "answer_check": "answer_key"},
        r"\boxed{A}",
        True,
    ),
    (
        {"group": "science_mcq", "target": "B", "answer_check": "answer_key"},
        "Therefore, the correct choice is B.",
        True,
    ),
    ({"group": "knowledge_mcq", "target": "C", "answer_check": "answer_key"}, "c", True),
    (
        {"group": "knowledge_mcq", "target": "D", "answer_check": "answer_key"},
        "The answer is D",
        True,
    ),
    (
        {"group": "knowledge_mcq", "target": "A", "answer_check": "answer_key"},
        "Option A is the best answer.",
        True,
    ),
    (
        {"group": "knowledge_mcq", "target": "B", "answer_check": "answer_key"},
        "I conclude that (B) is right.",
        True,
    ),
    ({"group": "science_mcq", "target": "A", "answer_check": "answer_key"}, "B", False),
    (
        {"group": "science_mcq", "target": "C", "answer_check": "answer_key"},
        "The correct answer is A",
        False,
    ),
    (
        {"group": "science_mcq", "target": "D", "answer_check": "answer_key"},
        "characterized by high temperature",
        False,
    ),
    (
        {"group": "knowledge_mcq", "target": "B", "answer_check": "answer_key"},
        "It could be A or B, but definitely C.",
        False,
    ),
    ({"group": "knowledge_mcq", "target": "C", "answer_check": "answer_key"}, "", False),
    (
        {"group": "knowledge_mcq", "target": "A", "answer_check": "answer_key"},
        "None of the above choices are correct.",
        False,
    ),
    # ── 21-40: Math (Exact Numeric) ──────────────────────────────────────────
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, "42", True),
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, "42.0", True),
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, "#### 42", True),
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, "$42", True),
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, r"\boxed{42}", True),
    (
        {"group": "math", "target": "125", "answer_check": "exact_numeric"},
        "The total is 125.",
        True,
    ),
    ({"group": "math", "target": "-15", "answer_check": "exact_numeric"}, "-15", True),
    ({"group": "math", "target": "0.75", "answer_check": "exact_numeric"}, "0.75", True),
    ({"group": "math", "target": "1000", "answer_check": "exact_numeric"}, "1,000", True),
    (
        {"group": "math", "target": "24", "answer_check": "exact_numeric"},
        "#### 24\nSome explanation",
        True,
    ),
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, "43", False),
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, "-42", False),
    ({"group": "math", "target": "42", "answer_check": "exact_numeric"}, "#### 41", False),
    (
        {"group": "math", "target": "42", "answer_check": "exact_numeric"},
        "No numeric answer found",
        False,
    ),
    ({"group": "math", "target": "100", "answer_check": "exact_numeric"}, "99.9", False),
    ({"group": "math", "target": "0", "answer_check": "exact_numeric"}, "0", True),
    ({"group": "math", "target": "0", "answer_check": "exact_numeric"}, "1", False),
    ({"group": "math", "target": "500", "answer_check": "exact_numeric"}, "500 dollars", True),
    (
        {"group": "math", "target": "250", "answer_check": "exact_numeric"},
        "Total cost: $250.00",
        True,
    ),
    ({"group": "math", "target": "250", "answer_check": "exact_numeric"}, "240.00", False),
    # ── 41-75: Knowledge QA (Dates, Numbers, Entities, Aliases) ──────────────
    (
        {
            "group": "knowledge_qa",
            "target": "3 February 1898",
            "answer_check": "normalized_exact_match",
        },
        "3 February 1898",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "3 February 1898",
            "answer_check": "normalized_exact_match",
        },
        "February 3, 1898",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "3 February 1898",
            "answer_check": "normalized_exact_match",
        },
        "on 3 February 1898",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "3 February 1898",
            "answer_check": "normalized_exact_match",
        },
        "was born on 3 February 1898",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "3 February 1898",
            "answer_check": "normalized_exact_match",
        },
        "1898",
        False,
    ),  # Strict date: year alone NOT credited for full date
    (
        {"group": "knowledge_qa", "target": "1898", "answer_check": "normalized_exact_match"},
        "1898",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "1898", "answer_check": "normalized_exact_match"},
        "in 1898",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "1898", "answer_check": "normalized_exact_match"},
        "circa 1898",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "1898", "answer_check": "normalized_exact_match"},
        "1899",
        False,
    ),
    (
        {"group": "knowledge_qa", "target": "17 million", "answer_check": "normalized_exact_match"},
        "17,000,000",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "17,000,000", "answer_check": "normalized_exact_match"},
        "17 million",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "17 million", "answer_check": "normalized_exact_match"},
        "17 million inhabitants",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "528,490", "answer_check": "normalized_exact_match"},
        "528490 residents",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "528,490", "answer_check": "normalized_exact_match"},
        "528,490",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "528,490", "answer_check": "normalized_exact_match"},
        "528,491",
        False,
    ),
    (
        {"group": "knowledge_qa", "target": "astronomer", "answer_check": "normalized_exact_match"},
        "astronomer",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "astronomer", "answer_check": "normalized_exact_match"},
        "An astronomer.",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "astronomer", "answer_check": "normalized_exact_match"},
        "astronomer, physicist, and mathematician",
        False,
    ),  # Profession list rejected
    (
        {"group": "knowledge_qa", "target": "actress", "answer_check": "normalized_exact_match"},
        "singer and actress",
        False,
    ),
    (
        {"group": "knowledge_qa", "target": "actress", "answer_check": "normalized_exact_match"},
        "actress",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "Aurora Borealis Prize",
            "answer_check": "normalized_exact_match",
        },
        "Aurora Borealis Prize",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "Aurora Borealis Prize",
            "answer_check": "normalized_exact_match",
        },
        "the Aurora Borealis Prize",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "Aurora Borealis Prize",
            "answer_check": "normalized_exact_match",
        },
        "Australis Fellowship",
        False,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "Paris",
            "answer_check": "normalized_exact_match",
            "aliases": ["City of Light"],
        },
        "City of Light",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "Paris",
            "answer_check": "normalized_exact_match",
            "aliases": ["City of Light"],
        },
        "London",
        False,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "United States",
            "answer_check": "normalized_exact_match",
            "aliases": ["USA", "US"],
        },
        "USA",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "United States",
            "answer_check": "normalized_exact_match",
            "aliases": ["USA", "US"],
        },
        "the United States",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "United States",
            "answer_check": "normalized_exact_match",
        },
        "Canada",
        False,
    ),
    (
        {"group": "knowledge_qa", "target": "geologist", "answer_check": "normalized_exact_match"},
        "geologist",
        True,
    ),
    (
        {"group": "knowledge_qa", "target": "geologist", "answer_check": "normalized_exact_match"},
        "botanist",
        False,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "14 July 1842",
            "answer_check": "normalized_exact_match",
        },
        "July 14, 1842",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "14 July 1842",
            "answer_check": "normalized_exact_match",
        },
        "14 July 1842",
        True,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "14 July 1842",
            "answer_check": "normalized_exact_match",
        },
        "15 July 1842",
        False,
    ),
    (
        {
            "group": "knowledge_qa",
            "target": "14 July 1842",
            "answer_check": "normalized_exact_match",
        },
        "1842",
        False,
    ),
    (
        {"group": "knowledge_qa", "target": "1742", "answer_check": "normalized_exact_match"},
        "1742",
        True,
    ),
    # ── 76-88: Memory Probe ──────────────────────────────────────────────────
    (
        {
            "group": "memory_probe",
            "target": "Austin",
            "answer_check": "key_from_source_history",
            "stale_values": ["Denver", "Seattle"],
        },
        "Austin",
        True,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Austin",
            "answer_check": "key_from_source_history",
            "stale_values": ["Denver", "Seattle"],
        },
        "I currently live in Austin.",
        True,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Austin",
            "answer_check": "key_from_source_history",
            "stale_values": ["Denver", "Seattle"],
        },
        "Denver",
        False,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Austin",
            "answer_check": "key_from_source_history",
            "stale_values": ["Denver", "Seattle"],
        },
        "Seattle",
        False,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Austin",
            "answer_check": "key_from_source_history",
            "stale_values": ["Denver", "Seattle"],
        },
        "I moved from Denver to Austin.",
        False,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Rachel Vance",
            "answer_check": "key_from_source_history",
            "stale_values": ["David Chen"],
        },
        "Rachel Vance",
        True,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Rachel Vance",
            "answer_check": "key_from_source_history",
            "stale_values": ["David Chen"],
        },
        "David Chen",
        False,
    ),
    (
        {
            "group": "memory_probe",
            "target": "2024 Toyota RAV4 Hybrid",
            "answer_check": "key_from_source_history",
            "stale_values": ["2018 Honda Civic"],
        },
        "2024 Toyota RAV4 Hybrid",
        True,
    ),
    (
        {
            "group": "memory_probe",
            "target": "2024 Toyota RAV4 Hybrid",
            "answer_check": "key_from_source_history",
            "stale_values": ["2018 Honda Civic"],
        },
        "2018 Honda Civic",
        False,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Blue",
            "answer_check": "key_from_source_history",
            "stale_values": [],
        },
        "Blue",
        True,
    ),
    (
        {
            "group": "memory_probe",
            "target": "Blue",
            "answer_check": "key_from_source_history",
            "stale_values": [],
        },
        "Red",
        False,
    ),
    (
        {
            "group": "memory_probe",
            "target": "94107",
            "answer_check": "key_from_source_history",
            "stale_values": [],
        },
        "94107",
        True,
    ),
    (
        {
            "group": "memory_probe",
            "target": "94107",
            "answer_check": "key_from_source_history",
            "stale_values": [],
        },
        "94108",
        False,
    ),
    # ── 89-100: Code Extraction & Sandbox Execution ──────────────────────────
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate([1, 2, 3]) == 6\ncheck(add_all)",
            "metadata": {"entry_point": "add_all"},
            "prompt": "def add_all(nums: list[int]) -> int:",
        },
        "def add_all(nums: list[int]) -> int:\n    return sum(nums)",
        True,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate([1, 2, 3]) == 6\ncheck(add_all)",
            "metadata": {"entry_point": "add_all"},
            "prompt": "def add_all(nums: list[int]) -> int:",
        },
        "```python\ndef add_all(nums: list[int]) -> int:\n    return sum(nums)\n```",
        True,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate([1, 2, 3]) == 6\ncheck(add_all)",
            "metadata": {"entry_point": "add_all"},
            "prompt": "def add_all(nums: list[int]) -> int:",
        },
        "def add_all(nums: list[int]) -> int:\n    return 0",
        False,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate(4) == 16\ncheck(square)",
            "metadata": {"entry_point": "square"},
            "prompt": "def square(n: int) -> int:",
        },
        "def square(n: int) -> int:\n    return n * n",
        True,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate(4) == 16\ncheck(square)",
            "metadata": {"entry_point": "square"},
            "prompt": "def square(n: int) -> int:",
        },
        "def square(n: int) -> int:\n    return n + n",
        False,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": 'def check(candidate):\n    assert candidate("hello") == "olleh"\ncheck(rev)',
            "metadata": {"entry_point": "rev"},
            "prompt": "def rev(s: str) -> str:",
        },
        "def rev(s: str) -> str:\n    return s[::-1]",
        True,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate([1, -2, 3]) == [1, 3]\ncheck(pos)",
            "metadata": {"entry_point": "pos"},
            "prompt": "def pos(nums: list[int]) -> list[int]:",
        },
        "def pos(nums: list[int]) -> list[int]:\n    return [x for x in nums if x > 0]",
        True,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate([1, -2, 3]) == [1, 3]\ncheck(pos)",
            "metadata": {"entry_point": "pos"},
            "prompt": "def pos(nums: list[int]) -> list[int]:",
        },
        "def pos(nums: list[int]) -> list[int]:\n    return nums",
        False,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate(5) is True\ncheck(is_pos)",
            "metadata": {"entry_point": "is_pos"},
            "prompt": "def is_pos(n: int) -> bool:",
        },
        "def is_pos(n: int) -> bool:\n    return n > 0",
        True,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": "def check(candidate):\n    assert candidate(5) is True\ncheck(is_pos)",
            "metadata": {"entry_point": "is_pos"},
            "prompt": "def is_pos(n: int) -> bool:",
        },
        "def is_pos(n: int) -> bool:\n    return False",
        False,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": 'def check(candidate):\n    assert candidate("a") == 1\ncheck(length)',
            "metadata": {"entry_point": "length"},
            "prompt": "def length(s: str) -> int:",
        },
        "def length(s: str) -> int:\n    return len(s)",
        True,
    ),
    (
        {
            "group": "code",
            "target": "",
            "answer_check": "unit_tests_pass",
            "test_code": 'def check(candidate):\n    assert candidate("a") == 1\ncheck(length)',
            "metadata": {"entry_point": "length"},
            "prompt": "def length(s: str) -> int:",
        },
        "invalid syntax error def",
        False,
    ),
]


def test_golden_cases_count():
    assert len(GOLDEN_CASES) == 100, f"Expected exactly 100 golden cases, got {len(GOLDEN_CASES)}"


@pytest.mark.parametrize(
    "idx,item,raw_output,expected",
    [
        (i, item, raw_output, expected)
        for i, (item, raw_output, expected) in enumerate(GOLDEN_CASES, 1)
    ],
)
def test_scoring_golden_fixture(idx: int, item: dict, raw_output: str, expected: bool):
    _, is_correct = extract_answer_for_group(item, raw_output)
    assert (
        is_correct == expected
    ), f"Golden case #{idx} failed: target={item.get('target')!r}, raw_output={raw_output!r}, expected={expected}, got={is_correct}"
