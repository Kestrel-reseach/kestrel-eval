"""Robust answer extraction and scoring for Kestrel Prototype 1 evaluation.

Protocol: Step 2 Part 4R (Real Inference Verification).
Addresses Issue 1: Eliminates spurious regex matches on words ending in option letters
(e.g., 'characterized' matching 'D').
"""

from __future__ import annotations

import re
from typing import Any

from evaluation.code_sandbox import run_code_in_sandbox


def extract_mcq_answer(text: str) -> str | None:
    """Extract multiple-choice letter (A, B, C, or D) from model output.

    Must NOT match characters inside ordinary English words (e.g. 'characterized', 'lead').
    Prefers explicit final answer declarations over stray option mentions.
    """
    if not text:
        return None

    clean = text.strip()

    # 1. Exact single letter or single letter in brackets/parentheses
    if clean.upper() in ("A", "B", "C", "D"):
        return clean.upper()
    exact_match = re.fullmatch(r"[\(\[\{]?([A-Da-d])[\)\]\}]?", clean)
    if exact_match:
        return exact_match.group(1).upper()

    # 2. LaTeX boxed: \boxed{A} or \boxed{\text{A}}
    boxed_match = re.search(r"\\boxed\{\s*(?:\\text\{)?\s*([A-Da-d])\s*\}?", clean)
    if boxed_match:
        return boxed_match.group(1).upper()

    # 3. Explicit final answer lines at the end of text (searched in reverse lines)
    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
    for line in reversed(lines):
        # Matches: "Answer: A", "Final Answer: (B)", "Option: [C]", "Choice: D", "**Answer**: D"
        m = re.search(
            r"(?i)(?:final\s+)?(?:answer|choice|option)\s*[:=\*]*\s*[\(\[]?\s*([A-D])\s*[\)\]\.]?(?:\s|$)",
            line,
        )
        if m:
            return m.group(1).upper()

    # 4. Leading option format on any line: "A) ...", "(B) ...", "C. ...", "**D**"
    for line in reversed(lines):
        m_lead = re.match(r"^[\(\[]?\s*([A-D])\s*[\)\.\:\-]\s+", line)
        if m_lead:
            return m_lead.group(1).upper()

    # 5. Bold option marker: "**A**" or "__B__"
    bold_matches = re.findall(r"(?:\*\*|__)\s*([A-D])\s*(?:\*\*|__)", clean)
    if bold_matches:
        return bold_matches[-1].upper()

    # 6. Look for standalone option statement near the end
    # Note: Requires word boundaries and excludes any surrounding alphabetic characters.
    end_matches = re.findall(r"\b([A-D])\b", clean)
    # If the text has only 1-2 words and one isolated letter:
    if len(lines) <= 2 and len(clean.split()) <= 6 and end_matches:
        return end_matches[0].upper()

    return None


def extract_math_answer(text: str) -> float | None:
    """Extract numeric answer from math solution text."""
    if not text:
        return None

    clean = text.strip()

    # 1. LaTeX boxed format: \boxed{123} or \boxed{123.45}
    boxed = re.findall(r"\\boxed\{\s*(-?[\d,]+(?:\.\d+)?)\s*\}", clean)
    if boxed:
        clean_num = boxed[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 2. Standard math benchmark format '#### 1234'
    match_hash = re.findall(r"####\s*(-?[\d,]+(?:\.\d+)?)", clean)
    if match_hash:
        clean_num = match_hash[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 3. Explicit 'Final Answer: 123'
    explicit = re.findall(r"(?i)(?:final\s+)?answer\s*[:=\*]*\s*\$?\s*(-?[\d,]+(?:\.\d+)?)", clean)
    if explicit:
        clean_num = explicit[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 4. Fallback: extract last valid number
    cleaned_text = re.sub(r"[\$,]", "", clean)
    matches = re.findall(r"[-+]?\d*\.?\d+", cleaned_text)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None


def extract_code_solution(text: str, entry_point: str | None = None) -> str:
    """Extract Python code solution from generated response."""
    if not text:
        return ""

    # 1. Fenced code block ```python ... ```
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    if blocks:
        if entry_point:
            for b in reversed(blocks):
                if f"def {entry_point}" in b:
                    return b.strip()
        return blocks[-1].strip()

    # 2. If code begins with def ...
    clean = text.strip()
    if clean.startswith("def "):
        return clean

    # 3. Look for a def block in text
    def_idx = clean.find("def ")
    if def_idx != -1:
        return clean[def_idx:].strip()

    return clean


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


def extract_answer_for_group(item: dict[str, Any], raw_output: str) -> tuple[Any, bool]:
    """Extract structured answer from raw_output and evaluate correctness against item target.

    Returns:
        (extracted_answer, is_correct)
    """
    group = item.get("group", "")
    answer_check = item.get("answer_check", "")
    target = item.get("target") or item.get("answer", "")

    if group in ("science_mcq", "knowledge_mcq") or answer_check == "answer_key":
        extracted = extract_mcq_answer(raw_output)
        target_str = str(target).strip().upper()
        target_key = extract_mcq_answer(target_str) or target_str
        is_correct = (extracted is not None) and (extracted == target_key)
        return extracted, is_correct

    if group == "math" or answer_check == "exact_numeric":
        extracted = extract_math_answer(raw_output)
        if isinstance(target, (int, float)):
            target_val = float(target)
        else:
            target_val = extract_math_answer(str(target))

        if extracted is None or target_val is None:
            return extracted, False

        tolerance = 1e-4
        is_correct = abs(extracted - target_val) <= tolerance or (
            target_val != 0.0 and abs((extracted - target_val) / target_val) <= tolerance
        )
        return extracted, is_correct

    if group == "code" or answer_check == "unit_tests_pass":
        entry_point = item.get("metadata", {}).get("entry_point")
        extracted_code = extract_code_solution(raw_output, entry_point=entry_point)
        test_code = (
            item.get("test_code")
            or item.get("metadata", {}).get("test_code", "")
            or item.get("target", "")
        )
        prompt = item.get("prompt", "")
        is_correct = run_code_in_sandbox(
            code=extracted_code,
            test_code=test_code,
            prompt=prompt,
            entry_point=entry_point,
            timeout_s=3.0,
        )
        return extracted_code, is_correct

    if group == "memory_probe" or answer_check == "key_from_source_history":
        from evaluation.generators.stale_fact_scorer import score_memory_probe_response

        stale_values = item.get("stale_values") or item.get("metadata", {}).get("stale_values", [])
        res = score_memory_probe_response(
            prediction=raw_output,
            target=str(target),
            stale_values=stale_values,
            is_stale_fact_item=bool(stale_values),
        )
        return raw_output.strip(), res["correct"]

    # Default knowledge_qa / key_match
    is_correct = check_key_match(raw_output, str(target))
    return raw_output.strip(), is_correct
