"""Common data classes and answer verification helpers for suite loaders."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from typing import Any, TypedDict


class SuiteItem(TypedDict):
    """Canonical representation of an evaluation suite task item."""

    item_id: str
    group: str
    prompt: str
    target: str
    answer_check: str
    choices: list[str] | None
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
    if prompt and not generated_code.strip().startswith("def "):
        code_to_run = f"{prompt}\n{generated_code}"
    else:
        code_to_run = generated_code

    # Quick syntax validation
    try:
        ast.parse(code_to_run)
        ast.parse(test_code)
    except SyntaxError:
        return False

    full_script = f"""import sys

{code_to_run}

{test_code}

sys.exit(0)
"""
    try:
        res = subprocess.run(
            [sys.executable, "-c", full_script],
            capture_output=True,
            timeout=timeout_s,
            text=True,
        )
        return res.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False
