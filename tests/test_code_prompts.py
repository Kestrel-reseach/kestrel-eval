"""Test code prompts and validation items integrity.

Enforces Step 2 Part 2a requirements:
- Valid entry points and ASCII characters across all code items.
- Standard MBPP prompt structure: natural language description + first test assertion + function name.
- Synthetic code prompt structure: natural language signature + 'Define a top-level function named X, no class'.
- Verified handling of code_val_0033.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.prompts import format_user_prompt


def test_code_items_ascii_and_identifiers():
    code_path = Path("suite/validation/code.jsonl")
    assert code_path.exists(), "suite/validation/code.jsonl must exist"

    with open(code_path) as f:
        items = [json.loads(line) for line in f]

    assert len(items) == 100, f"Expected 100 code validation items, got {len(items)}"

    for item in items:
        item_id = item["id"]
        ep = item.get("metadata", {}).get("entry_point") or item.get("entry_point")
        assert ep, f"[{item_id}] Missing entry_point in metadata"
        assert ep.isidentifier(), f"[{item_id}] Entry point {ep!r} is not a valid Python identifier"
        assert all(ord(c) < 128 for c in ep), f"[{item_id}] Entry point {ep!r} contains non-ASCII characters"

        # Check prompt has no non-ASCII
        prompt = item.get("prompt", "")
        assert all(ord(c) < 128 for c in prompt), f"[{item_id}] Prompt contains non-ASCII characters"


def test_code_val_0033_integrity():
    code_path = Path("suite/validation/code.jsonl")
    with open(code_path) as f:
        item = next(json.loads(line) for line in f if json.loads(line).get("id") == "code_val_0033")

    assert item["metadata"]["entry_point"] == "ap_sum"
    formatted = format_user_prompt(item)
    assert "ap_sum" in formatted
    assert "assert ap_sum(1,5,2)==25" in formatted
    assert "Write a function to find the sum of arithmetic progression." in formatted


def test_mbpp_and_synthetic_prompt_formatting():
    code_path = Path("suite/validation/code.jsonl")
    with open(code_path) as f:
        items = [json.loads(line) for line in f]

    mbpp_items = [it for it in items if it.get("arm") == "public"]
    synthetic_items = [it for it in items if it.get("arm") == "synthetic"]

    assert len(mbpp_items) == 50
    assert len(synthetic_items) == 50

    for it in mbpp_items:
        formatted = format_user_prompt(it)
        ep = it["metadata"]["entry_point"]
        assert f"Write a function named `{ep}`." in formatted
        assert "Your code should satisfy the following test:" in formatted
        assert "assert " in formatted

    for it in synthetic_items:
        formatted = format_user_prompt(it)
        ep = it["metadata"]["entry_point"]
        assert f"Define a top-level function named `{ep}`, no class." in formatted
