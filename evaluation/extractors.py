"""Robust answer extraction and scoring for Kestrel Prototype 1 evaluation.

Protocol: Step 2 Part 4R (Real Inference Verification).
Addresses Issue 1: Eliminates spurious regex matches on words ending in option letters
(e.g., 'characterized' matching 'D').
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from evaluation.code_sandbox import run_code_in_sandbox


def extract_mcq_answer(text: str) -> str | None:
    """Extract multiple-choice letter (A, B, C, D, or E) from model output.

    Must NOT match characters inside ordinary English words (e.g. 'characterized', 'lead').
    Prefers explicit final answer declarations over stray option mentions.
    Supports formats like:
      - 'The correct answer is C) ...' or 'The correct answer is A.'
      - 'correct answer is X)' or 'the answer is X'
      - 'Answer: X' or 'Final Answer: X'
      - '\\boxed{X}'
      - Leading line options 'X) ...' or 'X. ...'
    """
    if not text:
        return None

    clean = text.strip()

    # 1. Exact single letter or single letter in brackets/parentheses
    if clean.upper() in ("A", "B", "C", "D", "E"):
        return clean.upper()
    exact_match = re.fullmatch(r"[\(\[\{]?([A-Ea-e])[\)\]\}]?", clean)
    if exact_match:
        return exact_match.group(1).upper()

    # 2. LaTeX boxed: \boxed{A} or \boxed{\text{A}}
    boxed_match = re.search(r"\\boxed\{\s*(?:\\text\{)?\s*([A-Ea-e])\s*\}?", clean)
    if boxed_match:
        return boxed_match.group(1).upper()

    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]

    # Guard against broken sentences where line 1 is 'A' and line 2 is lowercase continuation
    if (
        len(lines) > 1
        and lines[0] in ("A", "B", "C", "D", "E")
        and lines[1]
        and lines[1][0].islower()
    ):
        return None

    # 3. Explicit declarative answer statements (wins over leading-option lines)
    # Operates strictly single-line (never matching across newlines)
    # Matches: "The correct answer is C)", "correct answer is A", "the answer is B", "Answer: D", "Final Answer: C"
    decl_pattern = re.compile(
        r"(?i)\b(?:the\s+)?(?:correct\s+)?(?:final\s+)?(?:answer|choice|option)\s*(?:is|are|[:=\*])\s*[\(\[]?\s*([A-E])(?:\)|\]|\.|\s|$)"
    )
    # Search backwards through lines so the concluding answer wins if multiple
    for line in reversed(lines):
        m = decl_pattern.search(line)
        if m:
            return m.group(1).upper()

    # 4. Leading option rule: applies ONLY when output has a single option line.
    # Several option lines without a declarative statement return None (option-list output).
    lead_options = []
    for line in lines:
        m_lead = re.match(r"^[\(\[]?\s*([A-E])\s*(?:[\)\]\.\:\-]|\s*$)", line)
        if m_lead:
            lead_options.append(m_lead.group(1).upper())

    if len(lead_options) == 1:
        return lead_options[0]
    elif len(lead_options) > 1:
        return None

    # 5. Option / Choice label prefix (e.g. "Option (A)", "Option A is the best answer.")
    opt_prefix = re.search(r"(?i)\b(?:option|choice)\s*[\(\[]?\s*([A-E])(?:\)|\]|\.|\s|$)", clean)
    if opt_prefix:
        return opt_prefix.group(1).upper()

    # 6. Bold option marker: "**A**" or "__B__" (only if single unique marker)
    bold_matches = re.findall(r"(?:\*\*|__)\s*([A-E])\s*(?:\*\*|__)", clean)
    if len(bold_matches) == 1:
        return bold_matches[0].upper()

    # 7. Standalone isolated letter if text is very short (at most 2 lines, <= 6 words, exactly 1 letter)
    # Strictly guards against English indefinite article "A" (e.g. "A car is moving fast", "A dog barked")
    end_matches = re.findall(r"\b([A-E])\b", clean)
    if len(lines) <= 2 and len(clean.split()) <= 6 and len(end_matches) == 1:
        letter = end_matches[0].upper()
        if letter == "A" and re.match(
            r"^A\s+(?!is\b|are\b|was\b|would\b|could\b|should\b)[a-z]", clean
        ):
            return None
        return letter

    return None


def extract_math_answer(text: str) -> float | None:
    """Extract numeric answer from math solution text."""
    if not text:
        return None

    clean = text.strip()

    # 1. LaTeX boxed format: \boxed{123} or \boxed{123.45} or \boxed{$123}
    boxed = re.findall(r"\\boxed\{\s*\\?\$?\s*(-?[\d,]+(?:\.\d+)?)\s*\}", clean)
    if boxed:
        clean_num = boxed[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 2. Standard math benchmark format '#### 1234' or '#### $1234'
    match_hash = re.findall(r"####\s*\\?\$?\s*(-?[\d,]+(?:\.\d+)?)", clean)
    if match_hash:
        clean_num = match_hash[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 3. Explicit 'Final Answer: 123' or 'Answer: $123' or 'Final Answer: \(123\)'
    explicit = re.findall(
        r"(?i)(?:final\s+)?answer\s*[:=\*]*\s*(?:\\[(\[])?\s*\\?\$?\s*(-?[\d,]+(?:\.\d+)?)",
        clean,
    )
    if explicit:
        clean_num = explicit[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 4. Bold answer marker: **310** or **310 ounces** or **$310**
    bold = re.findall(r"\*\*\s*\\?\$?\s*(-?[\d,]+(?:\.\d+)?)\s*(?:[a-zA-Z%]+)?\s*\*\*", clean)
    if bold:
        clean_num = bold[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 5. Declarative conclusion: 'Therefore, ... needs 310 ounces'
    concl = re.findall(
        r"(?i)(?:therefore|thus|hence|in total|she has|he has|they have|there are|there were)\s+[^.\n]*?\\?\$?\s*(-?[\d,]+(?:\.\d+)?)\s*(?:[a-zA-Z%]+)?[.]",
        clean,
    )
    if concl:
        clean_num = concl[-1].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # 6. Fallback: extract last valid number
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


def normalize_text_basic(s: str) -> str:
    """Basic text normalization: lowercase, strip articles and trailing punctuation."""
    s = s.lower().strip()
    s = re.sub(r"^(?:the|a|an)\s+", "", s)
    s = re.sub(r"^(?:in|on|at|around|circa|c\.)\s+", "", s)
    s = re.sub(r"[.,;:'\"!?]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_number_str(s: str) -> str:
    """Normalize comma separators, multipliers, and unit suffixes in numeric strings."""
    s = re.sub(r"(?<=\d),(?=\d)", "", s)
    s = re.sub(
        r"(\d+(?:\.\d+)?)\s*million\b",
        lambda m: str(int(float(m.group(1)) * 1_000_000)),
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"(\d+(?:\.\d+)?)\s*thousand\b",
        lambda m: str(int(float(m.group(1)) * 1_000)),
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"\b(?:inhabitants|people|residents|citizens|persons|meters|km|kilometers|miles)\b",
        "",
        s,
        flags=re.IGNORECASE,
    ).strip()
    return " ".join(s.split())


def parse_date_strict(s: str) -> tuple[Any | None, str]:
    """Parse a date string strictly.

    Returns:
        (parsed_value, granularity) where granularity is 'year_only', 'full_date', or 'none'.
    """
    clean = normalize_text_basic(s)
    if re.fullmatch(r"\d{4}", clean):
        try:
            val = int(clean)
            if 100 <= val <= 2100:
                return val, "year_only"
        except ValueError:
            pass

    fmts = (
        "%d %B %Y",
        "%B %d %Y",
        "%B %d, %Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%b %d %Y",
        "%b %d, %Y",
    )
    for fmt in fmts:
        try:
            dt = datetime.strptime(clean, fmt).date()
            return dt, "full_date"
        except ValueError:
            pass
    return None, "none"


def extract_answer_span(raw_text: str) -> str:
    """Isolate candidate answer value from potential conversational wrappers."""
    clean = raw_text.strip()
    clean = re.sub(r"^(?:Answer:|\s*:\s*)\s*", "", clean, flags=re.IGNORECASE).strip()
    patterns = [
        r"(?i)^(?:the\s+)?answer\s*(?:is|:|=)\s*",
        r"(?i)^according\s+to\s+(?:the\s+)?(?:context|passage|text)[,\s]+(?:the\s+answer\s+is\s+)?",
        r"(?i)^.*?\b(?:was|were)?\s*born\s+(?:on|in)\s+",
        r"(?i)^.*?\b(?:was|were)?\s*died\s+(?:on|in)\s+",
        r"(?i)^.*?\bdied\s+(?:on|in)\s+",
        r"(?i)^.*?\b(?:the\s+)?(?:profession|occupation|job|role)\s+(?:or\s+occupation\s+)?of\s+.*?\s+was\s+(?:a\s+|an\s+|the\s+)?",
        r"(?i)^.*?\b(?:was|is|became|worked\s+as)\s+(?:an?|the)\s+",
        r"(?i)^.*?\b(?:the\s+)?(?:reported\s+)?population\s+(?:of\s+.*?\s+)?(?:was|is)\s+",
        r"(?i)^.*?\b(?:the\s+)?award\s+(?:or\s+prize\s+)?.*?\s+received\s+was\s+",
        r"(?i)^.*?\b(?:was|were|is|has\s+been)\s*awarded\s+(?:the\s+|a\s+|an\s+)?",
        r"(?i)^.*?\b(?:won|received|earned)\s+(?:the\s+|a\s+|an\s+)?",
        r"(?i)^.*?\b(?:was|were)?\s*founded\s+in\s+",
        r"(?i)^.*?\b(?:was|were)?\s*released\s+in\s+",
    ]
    for pat in patterns:
        m = re.search(pat, clean)
        if m:
            clean = clean[m.end() :].strip()
            break

    clean = re.sub(r",?\s*aged\s+\d+.*$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"(?i)\s+(?:residents|people|inhabitants|citizens|individuals)\b.*$", "", clean)
    clean = re.sub(r"(?i)\s+in\s+(?:the\s+year\s+)?\d{4}\b.*$", "", clean)
    clean = re.sub(r"[.,;:'\"!?]+$", "", clean).strip()
    return clean


def score_frozen_exact_match(pred: str, target: str, aliases: list[str] | None = None) -> bool:
    """Evaluate factual accuracy using frozen span-extracted normalized exact match."""
    span = extract_answer_span(pred)
    norm_pred = normalize_number_str(normalize_text_basic(span))
    norm_target = normalize_number_str(normalize_text_basic(target))

    if norm_pred == norm_target:
        return True

    # Hyphen normalization: 'singer-songwriter' vs 'singer songwriter'
    if norm_pred.replace("-", " ") == norm_target.replace("-", " "):
        return True

    if aliases:
        for al in aliases:
            norm_al = normalize_number_str(normalize_text_basic(al))
            if norm_pred == norm_al or norm_pred.replace("-", " ") == norm_al.replace("-", " "):
                return True

    dt_target, gran_target = parse_date_strict(target)
    if gran_target != "none":
        dt_pred, gran_pred = parse_date_strict(span)
        if gran_target == "full_date":
            return gran_pred == "full_date" and dt_pred == dt_target
        elif gran_target == "year_only":
            return gran_pred == "year_only" and dt_pred == dt_target

    num_pred = re.sub(r"[^\d.-]", "", norm_pred)
    num_target = re.sub(r"[^\d.-]", "", norm_target)
    if num_pred and num_target:
        if num_pred == num_target:
            return True
        try:
            val_p = float(num_pred)
            val_t = float(num_target)
            if val_p == val_t or val_p == val_t * 1_000_000 or val_t == val_p * 1_000_000:
                return True
        except ValueError:
            pass

    return False


def score_token_f1(pred: str, target: str) -> float:
    """Compute token-level F1 score on the extracted answer span against gold target.

    Extracts the answer span first so that conversational prefaces (e.g. 'X was born on Y')
    do not artificially penalize precision.
    """
    span = extract_answer_span(pred)
    np = normalize_text_basic(normalize_number_str(span))
    nt = normalize_text_basic(normalize_number_str(target))
    pred_tokens = re.findall(r"\w+", np)
    gold_tokens = re.findall(r"\w+", nt)
    if not pred_tokens or not gold_tokens:
        return 1.0 if pred_tokens == gold_tokens else 0.0
    common = set(pred_tokens) & set(gold_tokens)
    if not common:
        return 0.0
    prec = len(common) / len(pred_tokens)
    rec = len(common) / len(gold_tokens)
    return 2.0 * (prec * rec) / (prec + rec)


def check_key_match(predicted: str, target: str) -> bool:
    """Check if the predicted string contains the target key (case/punctuation normalized)."""
    norm_pred = normalize_text(predicted)
    norm_target = normalize_text(target)
    if not norm_target:
        return False
    return norm_target in norm_pred


def check_exact_match(predicted: str, target: str) -> bool:
    """Check if the predicted string exactly equals the target key (case/punctuation normalized)."""
    norm_pred = normalize_text(predicted)
    norm_target = normalize_text(target)
    if not norm_target:
        return False
    return norm_pred == norm_target


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

    if group == "knowledge_qa" or answer_check in ("normalized_exact_match", "key_match"):
        aliases = item.get("aliases") or item.get("metadata", {}).get("aliases", [])
        is_correct = score_frozen_exact_match(raw_output, str(target), aliases=aliases)
        extracted = extract_answer_span(raw_output)
        return extracted, is_correct

    # Fallback key_match
    is_correct = check_key_match(raw_output, str(target))
    return raw_output.strip(), is_correct
