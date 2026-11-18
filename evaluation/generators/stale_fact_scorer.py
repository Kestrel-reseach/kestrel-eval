"""Scorer for personal-memory probe tasks with stale-fact items.

Design requirements (from Prototype 1 plan, manifest.yaml, and skill suite-split-hash):
- For a stale-fact item, a fact changes over time across synthetic history events.
- Target is the LATEST value.
- Previous values are STALE values.
- If a model outputs the stale value, it is scored as a STALE-FACT ERROR (correct=False).
- Stale-fact error ratio gate (G-M): stale-fact errors must be at most half of plain external memory.
"""

from __future__ import annotations

import re
from typing import TypedDict


class MemoryProbeScore(TypedDict):
    """Detailed score result for a memory probe item."""

    correct: bool
    score: float
    stale_fact_error: bool
    predicted_text: str
    target_value: str
    stale_values_found: list[str]
    notes: str


def normalize_value(val: str) -> str:
    """Normalize text for robust substring and keyword comparison."""
    clean = val.lower().strip()
    clean = re.sub(r"[^\w\s]", " ", clean)
    return " ".join(clean.split())


def score_memory_probe_response(
    prediction: str,
    target: str,
    stale_values: list[str] | None = None,
    is_stale_fact_item: bool = False,
) -> MemoryProbeScore:
    """Evaluate a model prediction on a personal memory probe item.

    Rules:
    1. The target (latest value) must be present in the prediction.
    2. If stale_values are present:
       - If any stale value is endorsed as the answer, flag stale_fact_error=True and score=0.0.
       - If target is present AND no stale value is endorsed, score=1.0 and correct=True.
       - If both latest and stale values are mentioned:
         - If the prediction explicitly states that the stale value is outdated/previous/changed
           and concludes with the latest value, it is correct.
         - If ambiguous or both presented as current, flag as stale_fact_error=True.
    """
    pred_norm = normalize_value(prediction)
    target_norm = normalize_value(target)
    stale_norms = [normalize_value(s) for s in (stale_values or []) if normalize_value(s)]

    # Check for presence of target value
    has_target = target_norm in pred_norm

    # Check for presence of stale values
    stale_matches: list[str] = []
    for s_raw, s_norm in zip(stale_values or [], stale_norms, strict=False):
        if s_norm in pred_norm:
            stale_matches.append(s_raw)

    # If it's not a stale-fact item (static recall), standard key match
    if not is_stale_fact_item or not stale_norms:
        correct = has_target
        return MemoryProbeScore(
            correct=correct,
            score=1.0 if correct else 0.0,
            stale_fact_error=False,
            predicted_text=prediction,
            target_value=target,
            stale_values_found=[],
            notes="Static fact match" if correct else "Target value missing",
        )

    # Stale-fact item evaluation
    if not stale_matches and has_target:
        return MemoryProbeScore(
            correct=True,
            score=1.0,
            stale_fact_error=False,
            predicted_text=prediction,
            target_value=target,
            stale_values_found=[],
            notes="Correct latest value retrieved with no stale contamination",
        )

    if stale_matches and not has_target:
        # Model returned the old value and missed the new one
        return MemoryProbeScore(
            correct=False,
            score=0.0,
            stale_fact_error=True,
            predicted_text=prediction,
            target_value=target,
            stale_values_found=stale_matches,
            notes=f"Stale-fact error: predicted old value(s) {stale_matches!r} instead of latest {target!r}",
        )

    if stale_matches and has_target:
        # Both mentioned. Check if prediction clarifies the change/recency.
        # Look for temporal contrast words: "previously", "used to be", "formerly", "changed to", "updated to"
        recency_patterns = [
            rf"(?:changed|moved|updated|switched|now|currently|latest)\s+(?:to\s+)?{re.escape(target_norm)}",
            rf"{re.escape(stale_norms[0])}\s+(?:was|previously|formerly|old)",
            rf"(?:used to be|formerly|previously)\s+{re.escape(stale_norms[0])}",
        ]
        clarified = any(re.search(pat, pred_norm) for pat in recency_patterns)
        if clarified:
            return MemoryProbeScore(
                correct=True,
                score=1.0,
                stale_fact_error=False,
                predicted_text=prediction,
                target_value=target,
                stale_values_found=stale_matches,
                notes="Correct: identified evolution and chose latest value",
            )
        # Ambiguous or contradictory
        return MemoryProbeScore(
            correct=False,
            score=0.0,
            stale_fact_error=True,
            predicted_text=prediction,
            target_value=target,
            stale_values_found=stale_matches,
            notes="Stale-fact error: ambiguous response containing both current and outdated values without recency distinction",
        )

    # Neither target nor stale found
    return MemoryProbeScore(
        correct=False,
        score=0.0,
        stale_fact_error=False,
        predicted_text=prediction,
        target_value=target,
        stale_values_found=[],
        notes="Incorrect: neither latest nor stale value was retrieved",
    )
