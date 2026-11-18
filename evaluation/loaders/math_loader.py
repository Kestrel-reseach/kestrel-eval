"""Math word problem loader (GSM8K format).

Answers are evaluated via exact_numeric matching.
Source: GSM8K (Cobbe et al., 2021). License: MIT (verified).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.loaders.common import SuiteItem, check_exact_numeric, extract_last_number
from evaluation.loaders.sources import get_source_metadata


def parse_gsm8k_record(
    raw: dict[str, Any],
    index: int,
    source_key: str = "gsm8k",
) -> SuiteItem:
    """Convert a raw GSM8K dict with 'question' and 'answer' into a canonical SuiteItem."""
    meta = get_source_metadata(source_key)
    question = raw["question"].strip()
    raw_answer = raw["answer"].strip()

    # Extract target number after '####' or last number
    target_num = extract_last_number(raw_answer)
    target_str = (
        str(int(target_num))
        if target_num is not None and target_num.is_integer()
        else str(target_num)
    )

    item_id = raw.get("item_id") or f"math-{index:04d}"

    return SuiteItem(
        item_id=item_id,
        group="math",
        prompt=question,
        target=target_str,
        answer_check="exact_numeric",
        choices=None,
        metadata={
            "source": meta.name,
            "version": meta.version,
            "license": meta.license,
            "license_url": meta.license_url,
            "url": meta.url,
            "verified_on_official_page": meta.verified_on_official_page,
            "contamination_risk": meta.contamination_risk,
            "scratchpad": raw_answer,
            "original_id": raw.get("id", f"gsm8k_{index}"),
        },
    )


def load_math_items_from_jsonl(path: Path | str, max_items: int | None = None) -> list[SuiteItem]:
    """Load and parse math word problem items from a GSM8K-style JSONL file."""
    path = Path(path)
    items: list[SuiteItem] = []
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            items.append(parse_gsm8k_record(raw, index=idx))
            if max_items is not None and len(items) >= max_items:
                break
    return items


def verify_math_item(item: SuiteItem) -> list[str]:
    """Validate that a math item has valid fields and self-consistent target number."""
    errors = []
    if not item["item_id"].startswith("math-"):
        errors.append(f"item_id {item['item_id']!r} must start with 'math-'")
    if not item["prompt"]:
        errors.append("prompt cannot be empty")
    if extract_last_number(item["target"]) is None:
        errors.append(f"target {item['target']!r} must be a parseable numeric value")
    if item["answer_check"] != "exact_numeric":
        errors.append(f"answer_check must be 'exact_numeric', got {item['answer_check']!r}")
    # Self-consistency check
    if not check_exact_numeric(item["target"], item["target"]):
        errors.append(f"target {item['target']!r} fails self-consistency numeric check")
    return errors
