"""Small-model baseline candidate shortlist and budget verification (Step 2 Part 4b).

Defines the verified candidate models evaluated for B-LLM selection on the
validation partition (1,200 items).

Constraints:
    - Target GPU tier: RTX 3050 Laptop 4 GB (alternate tier accepted 2026-11-18)
    - Assistant VRAM budget: <= 1.5 GB
    - Context length: 2048 tokens (Owner Decision D5)
    - Models dated after early 2026 require verification per rules.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelCandidate:
    """Specification of a baseline model candidate."""

    candidate_id: str
    model_name: str
    hf_repo_id: str
    approx_params_b: float
    quantization: str
    tier: str  # "gpu" | "cpu"
    estimated_4bit_vram_gb: float
    context_length: int
    license: str
    revision_hash: str
    notes: str


# Verified Candidate Shortlist for Step 2
CANDIDATE_SHORTLIST: dict[str, ModelCandidate] = {
    "qwen2.5-0.5b-instruct-q4": ModelCandidate(
        candidate_id="qwen2.5-0.5b-instruct-q4",
        model_name="Qwen2.5-0.5B-Instruct",
        hf_repo_id="Qwen/Qwen2.5-0.5B-Instruct",
        approx_params_b=0.49,
        quantization="4-bit (AWQ / GGUF Q4_K_M)",
        tier="gpu",
        estimated_4bit_vram_gb=0.45,
        context_length=2048,
        license="Apache-2.0",
        revision_hash="a3c9320",
        notes="Ultra-compact candidate; easily fits well within the 1.5 GB VRAM budget.",
    ),
    "qwen2.5-1.5b-instruct-q4": ModelCandidate(
        candidate_id="qwen2.5-1.5b-instruct-q4",
        model_name="Qwen2.5-1.5B-Instruct",
        hf_repo_id="Qwen/Qwen2.5-1.5B-Instruct",
        approx_params_b=1.54,
        quantization="4-bit (AWQ / GGUF Q4_K_M)",
        tier="gpu",
        estimated_4bit_vram_gb=1.15,
        context_length=2048,
        license="Apache-2.0",
        revision_hash="86c0784",
        notes="High-capability compact candidate; fits near the 1.5 GB assistant budget.",
    ),
    "granite-3.1-2b-instruct-q4": ModelCandidate(
        candidate_id="granite-3.1-2b-instruct-q4",
        model_name="Granite-3.1-2B-Instruct",
        hf_repo_id="ibm-granite/granite-3.1-2b-instruct",
        approx_params_b=2.5,
        quantization="4-bit (AWQ / GGUF Q4_K_M)",
        tier="gpu",
        estimated_4bit_vram_gb=1.40,
        context_length=2048,
        license="Apache-2.0",
        revision_hash="4b912da",
        notes="Enterprise-oriented IBM Granite small model candidate; fits within 1.5 GB.",
    ),
    "qwen2.5-3b-instruct-q4": ModelCandidate(
        candidate_id="qwen2.5-3b-instruct-q4",
        model_name="Qwen2.5-3B-Instruct",
        hf_repo_id="Qwen/Qwen2.5-3B-Instruct",
        approx_params_b=3.09,
        quantization="4-bit (AWQ / GGUF Q4_K_M)",
        tier="cpu",
        estimated_4bit_vram_gb=2.25,
        context_length=2048,
        license="Apache-2.0",
        revision_hash="b823e51",
        notes="CPU-tier reference; exceeds the 1.5 GB GPU assistant VRAM budget.",
    ),
}


def verify_vram_budget(candidate: ModelCandidate, max_budget_gb: float = 1.5) -> bool:
    """Verify whether a candidate model qualifies for the GPU tier budget."""
    if candidate.tier == "cpu":
        return False
    return candidate.estimated_4bit_vram_gb <= max_budget_gb


def get_candidate(candidate_id: str) -> ModelCandidate:
    """Retrieve a candidate specification by candidate_id."""
    if candidate_id not in CANDIDATE_SHORTLIST:
        raise KeyError(
            f"Unknown candidate {candidate_id!r}. Available: {list(CANDIDATE_SHORTLIST.keys())}"
        )
    return CANDIDATE_SHORTLIST[candidate_id]


def list_gpu_candidates(max_budget_gb: float = 1.5) -> list[ModelCandidate]:
    """Return all candidates verified to fit within the GPU VRAM budget."""
    return [
        c
        for c in CANDIDATE_SHORTLIST.values()
        if verify_vram_budget(c, max_budget_gb=max_budget_gb)
    ]


def format_candidate_summary(candidate: ModelCandidate) -> dict[str, Any]:
    """Format candidate metadata for inclusion in run configs or reports."""
    return {
        "candidate_id": candidate.candidate_id,
        "model_name": candidate.model_name,
        "hf_repo_id": candidate.hf_repo_id,
        "approx_params_b": candidate.approx_params_b,
        "quantization": candidate.quantization,
        "tier": candidate.tier,
        "estimated_4bit_vram_gb": candidate.estimated_4bit_vram_gb,
        "context_length": candidate.context_length,
        "license": candidate.license,
        "revision_hash": candidate.revision_hash,
    }
