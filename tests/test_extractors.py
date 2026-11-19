"""Unit tests and regression verification for answer extractors.

Specifically tests:
- Issue 1 regression: sci_val_0002 'characterized' with target 'D' must score False.
- MCQ extraction for diverse standard formats.
- Math numeric parsing for LaTeX boxed and benchmark tags.
- Code block extraction.
"""

from __future__ import annotations

from evaluation.extractors import (
    extract_answer_for_group,
    extract_answer_span,
    extract_code_solution,
    extract_math_answer,
    extract_mcq_answer,
    parse_date_strict,
    score_frozen_exact_match,
)


class TestMCQExtractor:
    def test_sci_val_0002_characterized_regression(self) -> None:
        """Issue 1 regression: trailing 'd' in 'characterized' must NOT extract option D."""
        text = "To determine which solar system planet is characterized"
        extracted = extract_mcq_answer(text)
        assert extracted is None, f"Expected None, got {extracted!r}"

        # Also test full extract_answer_for_group
        item = {
            "item_id": "sci_val_0002",
            "group": "science_mcq",
            "target": "D",
            "answer_check": "answer_key",
        }
        ans, is_correct = extract_answer_for_group(item, text)
        assert ans is None
        assert is_correct is False, "sci_val_0002 must score INCORRECT when answer was truncated"

    def test_words_ending_in_options_rejected(self) -> None:
        """Ensure English words ending in A/B/C/D are not matched as option keys."""
        assert extract_mcq_answer("The subatomic particle in question is the electron") is None
        assert extract_mcq_answer("An interesting idea about the cosmic void") is None
        assert extract_mcq_answer("The asteroid belt lies between Mars and Jupiter") is None
        assert extract_mcq_answer("We need to lead the expedition") is None

    def test_f1_real_output_regression_cases(self) -> None:
        """F1 regression: Real model outputs of the form 'The correct answer is X)' must extract X."""
        f1_cases = [
            (
                "The correct answer is C) Metamorphic rock.\n\nReasoning:\nMetamorphism refers to...",
                "C",
            ),
            (
                "The correct answer is A) Post-transition metal.\n\nReasoning:\nAluminum belongs to...",
                "A",
            ),
            ("The correct answer is A) Endogeneity.\n\nEndogeneity refers to a situation...", "A"),
            (
                "The correct answer is C) British global maritime hegemony and cession of New France.",
                "C",
            ),
            (
                "The correct answer is C) The Dormant Commerce Clause (for discriminating against interstate commerce).",
                "C",
            ),
            (
                "The correct answer is D) sophisticated vigesimal (base-20) mathematics including a symbol for zero.",
                "D",
            ),
            (
                "The correct answer is D) Felony Murder Rule.\n\nReasoning: The Felgy Murder Rule...",
                "D",
            ),
            ("The answer is B", "B"),
            ("correct answer is A)", "A"),
            ("the answer is D", "D"),
        ]
        for text, expected in f1_cases:
            got = extract_mcq_answer(text)
            assert got == expected, f"Failed for {text!r}: expected {expected}, got {got}"

    def test_f8a_option_list_precedence_and_regression(self) -> None:
        """F8a: Option lists without declarative statements must return None; declarative wins; single option line succeeds."""
        # Several option lines without declarative statement -> None
        know_val_0074_raw = (
            "To determine the correct answer, let's analyze each option:\n\n"
            "A) Receptor tyrosine kinase (RTK): RTKs are involved in signal transduction pathways but do not typically dimerize to undergo trans-autophosphorylation.\n\n"
            "B) Adenylate cyclase: This enzyme catalyzes"
        )
        assert extract_mcq_answer(know_val_0074_raw) is None

        sci_val_0005_raw = (
            "To determine which eukaryotic cellular structure generates cellular ATP via oxidative phosphorylation and contains its own circular DNA genome, let's analyze each option:\n\n"
            "A) Chloroplast - While chloroplasts contain their own DNA, they do not generate ATP through oxidative phosphorylation.\n"
            "B) Golgi apparatus - The Golgi apparatus"
        )
        assert extract_mcq_answer(sci_val_0005_raw) is None

        # Generic option list -> None
        assert extract_mcq_answer("A) First option\nB) Second option\nC) Third option") is None

        # Single option line -> succeeds
        assert extract_mcq_answer("C) Metamorphic rock") == "C"
        assert extract_mcq_answer("A. Post-transition metal") == "A"
        assert extract_mcq_answer("(D) Sophisticated vigesimal mathematics") == "D"

        # Option list with explicit declarative statement -> declarative statement wins
        list_with_declaration = (
            "A) Receptor tyrosine kinase\n"
            "B) Adenylate cyclase\n"
            "C) G-protein coupled receptor\n"
            "The correct answer is B) Adenylate cyclase."
        )
        assert extract_mcq_answer(list_with_declaration) == "B"

    def test_valid_mcq_formats(self) -> None:
        """Verify standard answer representations are correctly extracted."""
        assert extract_mcq_answer("Answer: C") == "C"
        assert extract_mcq_answer("Final Answer: B") == "B"
        assert extract_mcq_answer("Option (A)") == "A"
        assert extract_mcq_answer("Choice: [D]") == "D"
        assert extract_mcq_answer("C) Event horizon") == "C"
        assert extract_mcq_answer("(B) Jupiter") == "B"
        assert extract_mcq_answer(r"\boxed{A}") == "A"
        assert extract_mcq_answer(r"\boxed{\text{D}}") == "D"
        assert extract_mcq_answer("**C**") == "C"
        assert extract_mcq_answer("A") == "A"


class TestMathExtractor:
    def test_boxed_extraction(self) -> None:
        assert extract_math_answer(r"The total is \boxed{93}.") == 93.0
        assert extract_math_answer(r"\boxed{12.5}") == 12.5
        assert extract_math_answer(r"Therefore: \boxed{-42}") == -42.0

    def test_benchmark_hash_format(self) -> None:
        assert extract_math_answer("Step 1: 5\n#### 93") == 93.0
        assert extract_math_answer("Calculation: #### 1,250") == 1250.0

    def test_final_answer_declaration(self) -> None:
        assert extract_math_answer("Working... Final Answer: 47") == 47.0
        assert extract_math_answer("Answer: $35.50") == 35.50

    def test_fallback_last_number(self) -> None:
        assert extract_math_answer("The result of 10 plus 20 is 30") == 30.0


class TestCodeExtractor:
    def test_fenced_python_block(self) -> None:
        raw = """Here is the solution:
```python
def solve(x):
    return x * 2
```
Hope this helps!"""
        extracted = extract_code_solution(raw)
        assert extracted == "def solve(x):\n    return x * 2"

    def test_multiple_blocks_entry_point(self) -> None:
        raw = """```python
# Helper
def helper(): pass
```
```python
def main_func():
    return True
```"""
        extracted = extract_code_solution(raw, entry_point="main_func")
        assert "def main_func()" in extracted


class TestKnowledgeQAExtractor:
    def test_strict_date_parsing_and_year_only_rule(self) -> None:
        """Strict date comparison: year-only must NOT be credited for full date."""
        # Full date vs year-only -> must fail
        assert score_frozen_exact_match("Alp Arslan died in 1072.", "24 November 1072") is False
        assert score_frozen_exact_match("1072", "24 November 1072") is False

        # Full date vs full date -> passes
        assert score_frozen_exact_match("Alvar Aalto died on 11 May 1976.", "11 May 1976") is True
        assert score_frozen_exact_match("May 11, 1976", "11 May 1976") is True

        # Year-only vs year-only -> passes
        assert score_frozen_exact_match("1945", "1945") is True
        assert score_frozen_exact_match("Founded in 1945.", "1945") is True

    def test_conversational_wrapper_stripping(self) -> None:
        """Conversational preambles and postambles must be stripped."""
        assert extract_answer_span("According to the context, the answer is Paris") == "Paris"
        assert extract_answer_span("The reported population of Cleveland was 372,624.") == "372,624"
        assert (
            score_frozen_exact_match("According to the context, the answer is Paris", "Paris")
            is True
        )

    def test_number_normalization(self) -> None:
        """Comma-separated numbers and numeric spans are normalized."""
        assert score_frozen_exact_match("535,932", "535,932") is True
        assert score_frozen_exact_match("535932", "535,932") is True
        assert score_frozen_exact_match("17 million inhabitants", "17") is True

    def test_aliases_matching(self) -> None:
        """Target aliases (e.g. alternate profession or name) are credited."""
        assert (
            score_frozen_exact_match("builder", "architect", aliases=["builder", "designer"])
            is True
        )
        assert (
            score_frozen_exact_match("mechanic", "architect", aliases=["builder", "designer"])
            is False
        )

    def test_extract_answer_for_group_integration(self) -> None:
        """extract_answer_for_group for knowledge_qa uses frozen exact match."""
        item = {
            "item_id": "kqa_val_0002",
            "group": "knowledge_qa",
            "target": "11 May 1976",
            "answer_check": "normalized_exact_match",
        }
        span, is_correct = extract_answer_for_group(item, "Alvar Aalto died on 11 May 1976.")
        assert span == "11 May 1976"
        assert is_correct is True

        # Failure case with year-only
        item_fail = {
            "item_id": "kqa_val_0003",
            "group": "knowledge_qa",
            "target": "24 November 1072",
            "answer_check": "normalized_exact_match",
        }
        span, is_correct = extract_answer_for_group(item_fail, "Alp Arslan died in 1072.")
        assert span == "1072"
        assert is_correct is False

    def test_parse_date_strict(self) -> None:
        """Strict date parsing distinguishes full dates from year-only."""
        from datetime import date

        dt, gran = parse_date_strict("11 May 1976")
        assert gran == "full_date"
        assert dt == date(1976, 5, 11)

        dt2, gran2 = parse_date_strict("1976-05-11")
        assert gran2 == "full_date"
        assert dt2 == date(1976, 5, 11)

        val, gran3 = parse_date_strict("1976")
        assert gran3 == "year_only"
        assert val == 1976

        res, gran4 = parse_date_strict("Invalid Date")
        assert gran4 == "none"
        assert res is None
