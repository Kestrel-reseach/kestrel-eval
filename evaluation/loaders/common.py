"""Common data classes and answer verification helpers for suite loaders."""

from __future__ import annotations

import re
from typing import Any, TypedDict


class SuiteItem(TypedDict, total=False):
    """Canonical representation of an evaluation suite task item."""

    item_id: str
    id: str
    group: str
    split: str
    prompt: str
    target: str
    answer_check: str
    choices: list[str] | None
    arm: str
    template_family: str
    metadata: dict[str, Any]


def format_mcq_prompt(
    question: str, choices: list[str], labels: tuple[str, ...] = ("A", "B", "C", "D")
) -> str:
    """Format a multiple choice question with labeled options."""
    lines = [question.strip(), ""]
    for i, choice in enumerate(choices):
        label = labels[i] if i < len(labels) else str(i + 1)
        lines.append(f"{label}) {choice.strip()}")
    lines.append("\nAnswer with the option letter (e.g. A, B, C, or D):")
    return "\n".join(lines)


# ── Answer Checking Helpers ──────────────────────────────────────────────────


def extract_last_number(text: str) -> float | None:
    """Extract the last integer or decimal number from a string, handling negative signs and commas."""
    # First look for standard math benchmark format '#### 1234'
    match_hash = re.findall(r"####\s*(-?[\d,]+(?:\.\d+)?)", text)
    if match_hash:
        clean = match_hash[-1].replace(",", "")
        try:
            return float(clean)
        except ValueError:
            pass

    # Next look for general numbers: -?[\d,]+(?:\.\d+)?
    # Strip currency signs like $
    cleaned = re.sub(r"[\$,]", "", text)
    matches = re.findall(r"[-+]?\d*\.?\d+", cleaned)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None


def check_exact_numeric(
    predicted: str | float | int,
    target: str | float | int,
    tolerance: float = 1e-4,
) -> bool:
    """Return True if predicted extracts to the exact numeric target within tolerance."""
    if isinstance(target, (int, float)):
        target_val = float(target)
    else:
        target_val = extract_last_number(str(target))
        if target_val is None:
            return False

    if isinstance(predicted, (int, float)):
        pred_val = float(predicted)
    else:
        pred_val = extract_last_number(str(predicted))
        if pred_val is None:
            return False

    return abs(pred_val - target_val) <= tolerance or (
        target_val != 0.0 and abs((pred_val - target_val) / target_val) <= tolerance
    )


def extract_mcq_answer_key(text: str) -> str | None:
    """Extract multiple-choice letter (A-D) from text."""
    clean = text.strip()
    # Direct single letter
    if len(clean) == 1 and clean.upper() in "ABCD":
        return clean.upper()

    # Match patterns like: (A), A), [A], "Option A", "Answer: A"
    match = re.search(
        r"(?:answer|option|\(?)\s*[:\s]?\s*([A-D])(?:\)|\.|\s|$)", clean, re.IGNORECASE
    )
    if match:
        return match.group(1).upper()

    # Fallback: first occurrence of isolated A, B, C, or D
    match_first = re.search(r"\b([A-D])\b", clean)
    if match_first:
        return match_first.group(1).upper()

    return None


def check_answer_key(predicted: str, target: str) -> bool:
    """Return True if the predicted text matches the target multiple-choice key."""
    target_key = extract_mcq_answer_key(target) or target.strip().upper()
    pred_key = extract_mcq_answer_key(predicted)
    return pred_key == target_key if pred_key is not None else False


def check_unit_tests_pass(
    generated_code: str,
    test_code: str,
    prompt: str | None = None,
    entry_point: str | None = None,
    timeout_s: float = 3.0,
) -> bool:
    """Safely execute Python code against unit tests in an isolated subprocess.

    Returns True if execution exits 0 with no AssertionError or exceptions.
    """
    from evaluation.code_sandbox import run_code_in_sandbox
    from evaluation.extractors import extract_code_solution

    clean_code = extract_code_solution(generated_code, entry_point=entry_point)
    return run_code_in_sandbox(
        code=clean_code,
        test_code=test_code,
        prompt=prompt,
        entry_point=entry_point,
        timeout_s=timeout_s,
    )


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and stripping punctuation and excess whitespace."""
    clean = text.lower().strip()
    clean = re.sub(r"[^\w\s]", " ", clean)
    return " ".join(clean.split())


def check_key_match(predicted: str, target: str) -> bool:
    """Check if the predicted string contains the target key (case/punctuation normalized)."""
    norm_pred = normalize_text(predicted)
    norm_target = normalize_text(target)
    if not norm_target:
        return False
    return norm_target in norm_pred


def check_item_correctness(item: dict[str, Any], prediction: str) -> bool:
    """Consolidated checker routing to group-specific answer checking rules.

    Supported check types:
        - exact_numeric: math problems (GSM8K, synthetic arithmetic)
        - answer_key: multiple choice (ARC-Challenge, MMLU)
        - unit_tests_pass: Python code execution against assertions
        - key_match: Knowledge-QA entity span match
        - key_from_source_history: Personal memory probe with stale-fact scoring
    """
    answer_check = item.get("answer_check", "")
    target = item.get("target") or item.get("answer", "")

    if answer_check == "exact_numeric":
        return check_exact_numeric(prediction, target)

    if answer_check == "answer_key":
        return check_answer_key(prediction, str(target))

    if answer_check == "unit_tests_pass":
        test_code = (
            item.get("test_code")
            or item.get("metadata", {}).get("test_code", "")
            or item.get("target", "")
        )
        prompt = item.get("prompt", "")
        entry_point = item.get("metadata", {}).get("entry_point")
        return check_unit_tests_pass(
            prediction, test_code=test_code, prompt=prompt, entry_point=entry_point
        )

    if answer_check == "key_match":
        return check_key_match(prediction, str(target))

    if answer_check == "key_from_source_history":
        from evaluation.generators.stale_fact_scorer import score_memory_probe_response

        stale_values = item.get("stale_values") or item.get("metadata", {}).get("stale_values", [])
        score_res = score_memory_probe_response(
            prediction=prediction,
            target=str(target),
            stale_values=stale_values,
            is_stale_fact_item=bool(stale_values),
        )
        return score_res["correct"]

    # Default fallback: normalized target substring
    return check_key_match(prediction, str(target))
