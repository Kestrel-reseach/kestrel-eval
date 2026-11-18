"""Knowledge Multiple Choice Question (MCQ) loader (MMLU 10-subject format).

Answers are evaluated via answer_key matching (A, B, C, D).
Source: MMLU (Hendrycks et al., 2020). License: MIT (verified).
"""

from __future__ import annotations

import csv
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

MMLU_10_SUBJECTS: tuple[str, ...] = (
    "college_computer_science",
    "college_physics",
    "college_biology",
    "college_chemistry",
    "elementary_mathematics",
    "high_school_world_history",
    "high_school_geography",
    "professional_law",
    "clinical_knowledge",
    "econometrics",
)


def parse_mmlu_record(
    raw: dict[str, Any],
    index: int,
    subject: str = "general",
    source_key: str = "mmlu",
) -> SuiteItem:
    """Parse an MMLU item into a canonical SuiteItem."""
    meta = get_source_metadata(source_key)

    question = raw.get("question", "").strip()
    choices = [str(c).strip() for c in raw.get("choices", [])]
    raw_target = str(raw.get("target") or raw.get("answer", "")).strip().upper()
    target_key = extract_mcq_answer_key(raw_target) or raw_target

    # Convert numeric index 0-3 to A-D if needed
    if target_key in {"0", "1", "2", "3"}:
        target_key = chr(ord("A") + int(target_key))

    item_id = raw.get("item_id") or f"knowledge_mcq-{index:04d}"
    prompt = format_mcq_prompt(question, choices)

    return SuiteItem(
        item_id=item_id,
        group="knowledge_mcq",
        prompt=prompt,
        target=target_key,
        answer_check="answer_key",
        choices=choices,
        metadata={
            "source": meta.name,
            "version": meta.version,
            "license": meta.license,
            "license_url": meta.license_url,
            "url": meta.url,
            "verified_on_official_page": meta.verified_on_official_page,
            "contamination_risk": meta.contamination_risk,
            "subject": subject,
            "original_id": raw.get("id", f"mmlu_{subject}_{index}"),
        },
    )


def load_mmlu_csv(
    path: Path | str,
    subject: str,
    start_index: int = 1,
    max_items: int | None = None,
) -> list[SuiteItem]:
    """Load items from an official MMLU CSV file (question, choice_A, choice_B, choice_C, choice_D, answer)."""
    path = Path(path)
    items: list[SuiteItem] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader, start=start_index):
            if len(row) < 6:
                continue
            question = row[0]
            choices = row[1:5]
            answer = row[5]
            raw = {
                "question": question,
                "choices": choices,
                "answer": answer,
                "id": f"{subject}_{row_idx}",
            }
            items.append(parse_mmlu_record(raw, index=row_idx, subject=subject))
            if max_items is not None and len(items) >= max_items:
                break
    return items


def load_knowledge_mcq_items_from_jsonl(
    path: Path | str, max_items: int | None = None
) -> list[SuiteItem]:
    """Load items from a formatted JSONL file."""
    path = Path(path)
    items: list[SuiteItem] = []
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            items.append(parse_mmlu_record(raw, index=idx, subject=raw.get("subject", "general")))
            if max_items is not None and len(items) >= max_items:
                break
    return items


def verify_knowledge_mcq_item(item: SuiteItem) -> list[str]:
    """Validate that a knowledge MCQ item has valid 4 options and valid A-D answer key."""
    errors = []
    if not item["item_id"].startswith("knowledge_mcq-"):
        errors.append(f"item_id {item['item_id']!r} must start with 'knowledge_mcq-'")
    if not item["prompt"]:
        errors.append("prompt cannot be empty")
    if item["target"] not in {"A", "B", "C", "D"}:
        errors.append(f"target {item['target']!r} must be one of ['A', 'B', 'C', 'D']")
    if not item["choices"] or len(item["choices"]) != 4:
        errors.append(f"choices must have exactly 4 options, got {len(item.get('choices') or [])}")
    if item["answer_check"] != "answer_key":
        errors.append(f"answer_check must be 'answer_key', got {item['answer_check']!r}")
    if not check_answer_key(item["target"], item["target"]):
        errors.append("target fails self-consistency answer_key check")
    return errors
