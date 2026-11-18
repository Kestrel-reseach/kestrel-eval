"""Small-model local runner with BM25 retrieval, energy harness and VRAM tracking.

Protocol: Step 2 Part 4b (Small-Model Candidate Evaluation).
Complies with ModelRunner protocol for RunMatrix.

Features:
    - Fixed top-k (k=3) BM25 retrieval for knowledge_qa items
    - Diagnostic toggle: with retrieval vs without retrieval
    - Relative GPU energy measurement via EnergyHarness (NVML)
    - Peak VRAM tracking via torch.cuda.max_memory_allocated()
    - Wall time latency tracking (ms)
    - Full correctness evaluation via consolidated item checker
"""

from __future__ import annotations

import time
from typing import Any, Callable

from energy.harness import EnergyHarness
from evaluation.candidates import ModelCandidate, get_candidate
from evaluation.loaders.common import check_item_correctness
from evaluation.retrieval import BM25Retriever

try:
    import torch
except ImportError:
    torch = None  # type: ignore[assignment]


class LocalRunner:
    """Runner for local small-model candidate evaluation on the validation partition."""

    def __init__(
        self,
        candidate: ModelCandidate | str,
        *,
        retriever: BM25Retriever | None = None,
        use_retrieval: bool = True,
        harness: EnergyHarness | None = None,
        generate_fn: Callable[[str], str] | None = None,
        mock_mode: bool = False,
    ) -> None:
        if isinstance(candidate, str):
            self.candidate = get_candidate(candidate)
        else:
            self.candidate = candidate

        self.retriever = retriever
        self.use_retrieval = use_retrieval
        self.harness = harness
        self.generate_fn = generate_fn
        self.mock_mode = mock_mode

    def run_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Run a single suite item and return a partial JSONL record."""
        t0 = time.perf_counter()
        group = item.get("group", "")
        retrieval_hits = 0
        bytes_read = 0

        # Handle Knowledge-QA retrieval
        if group == "knowledge_qa" and self.use_retrieval and self.retriever is not None:
            prompt, hits = self.retriever.augment_knowledge_qa_prompt(item, top_k=3)
            retrieval_hits = len(hits)
            bytes_read = sum(len(h["text"].encode("utf-8")) for h in hits)
        else:
            prompt = item.get("prompt", "")

        # Measure energy via harness if available
        token = None
        if self.harness is not None and not self.mock_mode:
            try:
                token = self.harness.start()
            except Exception:  # noqa: BLE001
                token = None

        # Reset peak memory before inference
        if torch is not None and torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        # Generate prediction
        if self.generate_fn is not None:
            prediction = self.generate_fn(prompt)
        elif self.mock_mode:
            # Deterministic mock prediction matching target
            target = item.get("target") or item.get("answer", "")
            prediction = str(target)
        else:
            # Default stub prediction
            prediction = ""

        # Measure elapsed time
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Measure energy
        energy_j = 0.0
        energy_status = "relative_only"
        if self.harness is not None and token is not None:
            try:
                sample = self.harness.stop(token)
                energy_j = sample.gross_joules
            except Exception:  # noqa: BLE001
                energy_status = "unmeasured"

        # Measure peak VRAM
        peak_vram_mb = 0.0
        if torch is not None and torch.cuda.is_available():
            peak_vram_mb = torch.cuda.max_memory_allocated() / (1024.0 * 1024.0)

        # Check correctness
        correct = check_item_correctness(item, prediction)
        tokens_generated = max(1, len(prediction.split()))

        return {
            "bytes_read_from_ssd": bytes_read,
            "correct": correct,
            "energy_joules": round(energy_j, 4),
            "energy_status": energy_status,
            "passes": 1,
            "peak_vram_mb": round(peak_vram_mb, 2),
            "retrieval_hits": retrieval_hits,
            "tokens_generated": tokens_generated,
            "verifier_score": None,
            "wall_time_ms": round(elapsed_ms, 2),
        }
