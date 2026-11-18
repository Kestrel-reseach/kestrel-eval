"""Evaluation suite group loaders and official source registry."""

from __future__ import annotations

from evaluation.loaders.code_loader import (
    load_code_items_from_jsonl,
    parse_code_record,
    verify_code_item,
)
from evaluation.loaders.common import (
    SuiteItem,
    check_answer_key,
    check_exact_numeric,
    check_unit_tests_pass,
    extract_last_number,
    extract_mcq_answer_key,
    format_mcq_prompt,
)
from evaluation.loaders.knowledge_mcq_loader import (
    MMLU_10_SUBJECTS,
    load_knowledge_mcq_items_from_jsonl,
    load_mmlu_csv,
    parse_mmlu_record,
    verify_knowledge_mcq_item,
)
from evaluation.loaders.math_loader import (
    load_math_items_from_jsonl,
    parse_gsm8k_record,
    verify_math_item,
)
from evaluation.loaders.science_mcq_loader import (
    load_science_mcq_items_from_jsonl,
    parse_arc_record,
    verify_science_mcq_item,
)
from evaluation.loaders.sources import (
    PUBLIC_SOURCES,
    SourceMetadata,
    get_source_metadata,
)

__all__ = [
    "MMLU_10_SUBJECTS",
    "PUBLIC_SOURCES",
    "SourceMetadata",
    "SuiteItem",
    "check_answer_key",
    "check_exact_numeric",
    "check_unit_tests_pass",
    "extract_last_number",
    "extract_mcq_answer_key",
    "format_mcq_prompt",
    "get_source_metadata",
    "load_code_items_from_jsonl",
    "load_knowledge_mcq_items_from_jsonl",
    "load_math_items_from_jsonl",
    "load_mmlu_csv",
    "load_science_mcq_items_from_jsonl",
    "parse_arc_record",
    "parse_code_record",
    "parse_gsm8k_record",
    "parse_mmlu_record",
    "verify_code_item",
    "verify_knowledge_mcq_item",
    "verify_math_item",
    "verify_science_mcq_item",
]
