"""Synthetic task generators, extractors, and scorers for Project Kestrel."""

from __future__ import annotations

from evaluation.generators.code_generator import generate_code_suite
from evaluation.generators.knowledge_qa_generator import (
    extract_qa_from_article,
    generate_knowledge_qa_suite,
    verify_qa_span,
)
from evaluation.generators.math_generator import generate_math_problem, generate_math_suite
from evaluation.generators.memory_probe_generator import generate_memory_probe_suite
from evaluation.generators.stale_fact_scorer import (
    MemoryProbeScore,
    score_memory_probe_response,
)
from evaluation.generators.wiki_extractor import clean_wikitext, extract_abstract_corpus

__all__ = [
    "MemoryProbeScore",
    "clean_wikitext",
    "extract_abstract_corpus",
    "extract_qa_from_article",
    "generate_code_suite",
    "generate_knowledge_qa_suite",
    "generate_math_problem",
    "generate_math_suite",
    "generate_memory_probe_suite",
    "score_memory_probe_response",
    "verify_qa_span",
]
