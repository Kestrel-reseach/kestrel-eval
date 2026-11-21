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
    "smollm2-1.7b-instruct-q4": ModelCandidate(
        candidate_id="smollm2-1.7b-instruct-q4",
        model_name="SmolLM2-1.7B-Instruct",
        hf_repo_id="HuggingFaceTB/SmolLM2-1.7B-Instruct",
        approx_params_b=1.71,
        quantization="4-bit (bitsandbytes NF4)",
        tier="cpu",
        estimated_4bit_vram_gb=1.73,
        context_length=2048,
        license="Apache-2.0",
        revision_hash="31b70e2",
        notes="Disqualified: Measured NVML process VRAM = 1,732.0 MB at 2048 ctx; exceeds 1.5 GB budget.",
    ),
    "granite-4.0-1b-instruct-q4": ModelCandidate(
        candidate_id="granite-4.0-1b-instruct-q4",
        model_name="Granite-4.0-1B",
        hf_repo_id="ibm-granite/granite-4.0-1b",
        approx_params_b=1.49,
        quantization="4-bit (bitsandbytes NF4)",
        tier="cpu",
        estimated_4bit_vram_gb=1.60,
        context_length=2048,
        license="Apache-2.0",
        revision_hash="6a7381b",
        notes="Disqualified: Measured NVML process VRAM = 1,602.0 MB at 2048 ctx; exceeds 1.5 GB budget.",
    ),
    "llama-3.2-1b-instruct-q4": ModelCandidate(
        candidate_id="llama-3.2-1b-instruct-q4",
        model_name="Llama-3.2-1B-Instruct",
        hf_repo_id="meta-llama/Llama-3.2-1B-Instruct",
        approx_params_b=1.23,
        quantization="4-bit (bitsandbytes NF4)",
        tier="gpu",
        estimated_4bit_vram_gb=1.45,
        context_length=2048,
        license="Llama 3.2 Community",
        revision_hash="e527041",
        notes="Gated repo on HuggingFace Hub; blocked without HF_TOKEN environment variable.",
    ),
    "qwen3.5-0.8b-instruct-q4": ModelCandidate(
        candidate_id="qwen3.5-0.8b-instruct-q4",
        model_name="Qwen3.5-0.8B",
        hf_repo_id="Qwen/Qwen3.5-0.8B",
        approx_params_b=0.80,
        quantization="4-bit (bitsandbytes NF4)",
        tier="gpu",
        estimated_4bit_vram_gb=1.22,
        context_length=2048,
        license="Apache-2.0",
        revision_hash="2fc0636",
        notes="Measured NVML process VRAM = 1,220.0 MB at 2048 ctx (+316 MB headroom). Explored under D19.",
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
