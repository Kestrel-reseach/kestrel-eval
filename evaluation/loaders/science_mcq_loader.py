"""Science Multiple Choice Question (MCQ) loader (ARC-Challenge format).

Answers are evaluated via answer_key matching (A, B, C, D).
Source: AI2 Reasoning Challenge (Clark et al., 2018). License: CC BY-SA 4.0 (verified).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.loaders.common import (
    SuiteItem,
    check_answer_key,
    extract_mcq_answer_key,
    format_mcq_prompt,
)
from evaluation.loaders.sources import get_source_metadata


def parse_arc_record(
    raw: dict[str, Any],
    index: int,
    source_key: str = "arc_challenge",
) -> SuiteItem:
    """Parse an ARC-style dict into a canonical SuiteItem."""
    meta = get_source_metadata(source_key)

    # Standard ARC fields: 'question': {'stem': ..., 'choices': [{'text': ..., 'label': ...}]}, 'answerKey': ...
    if "question" in raw and isinstance(raw["question"], dict):
        stem = raw["question"].get("stem", "").strip()
        raw_choices = raw["question"].get("choices", [])
        choices_text = [c.get("text", "").strip() for c in raw_choices]
    else:
        stem = raw.get("stem") or raw.get("question", "").strip()
        choices_text = [str(c).strip() for c in raw.get("choices", [])]

    raw_key = raw.get("answerKey") or raw.get("target") or raw.get("answer", "")
    target_key = extract_mcq_answer_key(str(raw_key)) or str(raw_key).strip().upper()

    # Map numeric labels (1, 2, 3, 4) to letters (A, B, C, D)
    num_to_letter = {"1": "A", "2": "B", "3": "C", "4": "D"}
    if target_key in num_to_letter:
        target_key = num_to_letter[target_key]

    prompt = format_mcq_prompt(stem, choices_text)
    item_id = raw.get("item_id") or f"science_mcq-{index:04d}"

    return SuiteItem(
        item_id=item_id,
        group="science_mcq",
        prompt=prompt,
        target=target_key,
        answer_check="answer_key",
        choices=choices_text,
        metadata={
            "source": meta.name,
            "version": meta.version,
            "license": meta.license,
            "license_url": meta.license_url,
            "url": meta.url,
            "verified_on_official_page": meta.verified_on_official_page,
            "contamination_risk": meta.contamination_risk,
            "stem": stem,
            "original_id": raw.get("id", f"arc_{index}"),
        },
    )


def load_science_mcq_items_from_jsonl(
    path: Path | str, max_items: int | None = None
) -> list[SuiteItem]:
    """Load and parse science MCQ items from an ARC-style JSONL file."""
    path = Path(path)
    items: list[SuiteItem] = []
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            items.append(parse_arc_record(raw, index=idx))
            if max_items is not None and len(items) >= max_items:
                break
    return items


def verify_science_mcq_item(item: SuiteItem) -> list[str]:
    """Validate that a science MCQ item conforms to schema and has valid 4 options and key."""
    errors = []
    if not item["item_id"].startswith("science_mcq-"):
        errors.append(f"item_id {item['item_id']!r} must start with 'science_mcq-'")
    if not item["prompt"]:
        errors.append("prompt cannot be empty")
    if item["target"] not in {"A", "B", "C", "D"}:
        errors.append(f"target {item['target']!r} must be one of ['A', 'B', 'C', 'D']")
    if not item["choices"] or len(item["choices"]) < 2:
        errors.append("choices must have at least 2 options")
    if item["answer_check"] != "answer_key":
        errors.append(f"answer_check must be 'answer_key', got {item['answer_check']!r}")
    if not check_answer_key(item["target"], item["target"]):
        errors.append("target fails self-consistency answer_key check")
    return errors
