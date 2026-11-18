"""Data contamination, leakage, and duplicate detection module (PR 4).

Verifies strict partition independence for Project Kestrel (Step 1):
1. Zero ID overlap across train, validation, and locked-test partitions.
2. Zero exact duplicate prompt/question text between partitions.
3. Near-duplicate prompt detection using character 4-gram Jaccard similarity (threshold = 0.85).
4. Answer-in-prompt leakage verification (ground-truth answer not revealed in question).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_no_id_overlap(partitions: dict[str, list[dict[str, Any]]]) -> None:
    """Verify that no item ID appears in more than one partition."""
    seen: dict[str, str] = {}
    for part_name, items in partitions.items():
        for item in items:
            item_id = item.get("id") or item.get("item_id")
            if not item_id:
                raise ValueError(f"Item missing 'id' or 'item_id': {item}")
            if item_id in seen:
                raise ValueError(
                    f"Item ID {item_id!r} appears in both {seen[item_id]!r} and {part_name!r}"
                )
            seen[item_id] = part_name


def check_exact_prompt_duplicates(
    partitions: dict[str, list[dict[str, Any]]],
) -> list[dict[str, str]]:
    """Check for identical prompt/question strings between different partitions."""
    duplicates: list[dict[str, str]] = []
    seen_prompts: dict[str, tuple[str, str]] = {}  # prompt_clean -> (part_name, item_id)

    for part_name, items in partitions.items():
        for item in items:
            prompt = item.get("prompt") or item.get("question") or ""
            p_clean = " ".join(prompt.strip().lower().split())
            if not p_clean:
                continue
            item_id = str(item.get("id") or item.get("item_id"))
            if p_clean in seen_prompts:
                prev_part, prev_id = seen_prompts[p_clean]
                if prev_part != part_name:
                    duplicates.append(
                        {
                            "part_a": prev_part,
                            "id_a": prev_id,
                            "part_b": part_name,
                            "id_b": item_id,
                            "prompt": prompt[:80],
                        }
                    )
            else:
                seen_prompts[p_clean] = (part_name, item_id)

    return duplicates


def _get_char_ngrams(text: str, n: int = 4) -> set[str]:
    """Extract character n-grams from cleaned text."""
    clean = " ".join(text.lower().split())
    if len(clean) < n:
        return {clean}
    return {clean[i : i + n] for i in range(len(clean) - n + 1)}


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def check_near_duplicates(
    items_a: list[dict[str, Any]],
    items_b: list[dict[str, Any]],
    threshold: float = 0.85,
) -> list[dict[str, Any]]:
    """Detect near-duplicate prompts between two sets of items using 4-gram Jaccard similarity."""
    near_dups: list[dict[str, Any]] = []

    # Precompute n-grams
    ngrams_a = [
        (
            it.get("id") or it.get("item_id"),
            it.get("prompt") or it.get("question") or "",
            _get_char_ngrams(it.get("prompt") or it.get("question") or ""),
        )
        for it in items_a
    ]

    for it_b in items_b:
        id_b = it_b.get("id") or it_b.get("item_id")
        prompt_b = it_b.get("prompt") or it_b.get("question") or ""
        ng_b = _get_char_ngrams(prompt_b)
        if not ng_b:
            continue

        for id_a, prompt_a, ng_a in ngrams_a:
            sim = jaccard_similarity(ng_a, ng_b)
            if sim >= threshold:
                near_dups.append(
                    {
                        "id_a": id_a,
                        "id_b": id_b,
                        "similarity": round(sim, 4),
                        "prompt_a": prompt_a[:80],
                        "prompt_b": prompt_b[:80],
                    }
                )

    return near_dups


def check_answer_leakage(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure the ground-truth answer does not trivially appear inside the question.

    Applies to free-form Q&A and arithmetic where answer should not be leaked in question stem.
    Excludes multiple-choice options lists and passage text in retrieval groups.
    """
    leaks: list[dict[str, Any]] = []
    for it in items:
        group = it.get("group")
        # In MCQ, choice options naturally appear in formatted prompt; check stem only
        question = it.get("question") or it.get("stem") or it.get("prompt", "").split("\n")[0]
        ans = str(it.get("target") or it.get("answer") or it.get("answerKey") or "").strip()

        # Check only non-trivial answers (>= 3 chars and not simple MCQ letters)
        if len(ans) >= 3 and ans.upper() not in ("A", "B", "C", "D"):
            # Check if answer is a standalone word in question
            q_clean = question.lower()
            ans_clean = ans.lower()
            if ans_clean in q_clean:
                # Flag potential leakage
                leaks.append(
                    {
                        "id": it.get("id") or it.get("item_id"),
                        "group": group,
                        "question": question[:80],
                        "answer": ans,
                    }
                )

    return leaks
