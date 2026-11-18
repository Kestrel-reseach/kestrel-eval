"""Synthetic task generators and scorers for Project Kestrel (PR 2)."""

from __future__ import annotations

from evaluation.generators.code_generator import generate_code_suite
from evaluation.generators.math_generator import generate_math_problem, generate_math_suite
from evaluation.generators.memory_probe_generator import generate_memory_probe_suite
from evaluation.generators.stale_fact_scorer import (
    MemoryProbeScore,
    score_memory_probe_response,
)

__all__ = [
    "MemoryProbeScore",
    "generate_code_suite",
    "generate_math_problem",
    "generate_math_suite",
    "generate_memory_probe_suite",
    "score_memory_probe_response",
]
