"""Code task loader with unit test execution.

Answers are evaluated via unit_tests_pass.
Sources: HumanEval (OpenAI, 2021) [MIT verified] & MBPP (Google, 2021) [CC BY 4.0 verified].

Contamination Notice:
Public code sets (HumanEval, MBPP) are severely contaminated in modern language models
and HumanEval has only 164 total problems (insufficient for clean 100 locked + 100 val splits).
Privately written synthetic tasks with fresh algorithmic logic are formally proposed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.loaders.common import SuiteItem, check_unit_tests_pass
from evaluation.loaders.sources import get_source_metadata


def parse_code_record(
    raw: dict[str, Any],
    index: int,
    source_key: str = "humaneval",
) -> SuiteItem:
    """Parse a HumanEval or MBPP style code record into a canonical SuiteItem."""
    meta = get_source_metadata(source_key)

    task_id = raw.get("task_id") or raw.get("id") or f"code_{index}"
    prompt = raw.get("prompt") or raw.get("text") or raw.get("question", "")
    test_code = raw.get("test") or raw.get("test_list") or ""
    if isinstance(test_code, list):
        test_code = "\n".join(test_code)

    canonical_sol = raw.get("canonical_solution") or raw.get("code") or ""
    entry_point = raw.get("entry_point") or raw.get("function_name") or ""

    item_id = raw.get("item_id") or f"code-{index:04d}"

    return SuiteItem(
        item_id=item_id,
        group="code",
        prompt=prompt,
        target=canonical_sol,
        answer_check="unit_tests_pass",
        choices=None,
        metadata={
            "source": meta.name,
            "version": meta.version,
            "license": meta.license,
            "license_url": meta.license_url,
            "url": meta.url,
            "verified_on_official_page": meta.verified_on_official_page,
            "contamination_risk": meta.contamination_risk,
            "entry_point": entry_point,
            "test_code": test_code,
            "original_id": task_id,
        },
    )


def load_code_items_from_jsonl(path: Path | str, max_items: int | None = None) -> list[SuiteItem]:
    """Load and parse code tasks from a JSONL file."""
    path = Path(path)
    items: list[SuiteItem] = []
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            source_key = raw.get("source_key", "humaneval")
            items.append(parse_code_record(raw, index=idx, source_key=source_key))
            if max_items is not None and len(items) >= max_items:
                break
    return items


def verify_code_item(item: SuiteItem, run_unit_tests: bool = True) -> list[str]:
    """Validate that a code item has valid prompt, tests, and its canonical solution passes."""
    errors = []
    if not item["item_id"].startswith("code-"):
        errors.append(f"item_id {item['item_id']!r} must start with 'code-'")
    if not item["prompt"]:
        errors.append("prompt cannot be empty")
    test_code = item["metadata"].get("test_code", "")
    if not test_code:
        errors.append("metadata['test_code'] cannot be empty")
    if item["answer_check"] != "unit_tests_pass":
        errors.append(f"answer_check must be 'unit_tests_pass', got {item['answer_check']!r}")

    # Verify canonical solution passes its own unit tests
    if run_unit_tests and item["target"] and test_code:
        passes = check_unit_tests_pass(
            generated_code=item["target"],
            test_code=test_code,
            prompt=item["prompt"],
            entry_point=item["metadata"].get("entry_point"),
        )
        if not passes:
            errors.append(f"Canonical solution for {item['item_id']} failed its own unit tests")

    return errors
