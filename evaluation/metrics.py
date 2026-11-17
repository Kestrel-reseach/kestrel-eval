"""Quality, energy and memory metrics for Kestrel Prototype 1 — Step 0 scaffold.

Implements the metrics needed for gate arithmetic (G-Q, G-F, G-M, G-R).
Bootstrap CI and per-group accuracy are ready to use.  Energy and memory
aggregation plugs in once Step 2 runs produce real JSONL records.

Usage::

    from evaluation.metrics import accuracy, joules_per_correct_task, gate_q

    acc, ci = accuracy(records, group="math")
    j_per_correct = joules_per_correct_task(records)
    passed, detail = gate_q(p1_records, bllm_records, groups=["math", "code"])
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

__all__ = [
    "accuracy",
    "accuracy_by_group",
    "config_hash",
    "gate_q_accuracy",
    "gate_q_energy",
    "joules_per_correct_task",
    "paired_bootstrap_ci",
    "percentile_latency",
    "peak_vram_gb",
    "load_records",
]

Record = dict[str, Any]


# ── Loading ────────────────────────────────────────────────────────────────────


def load_records(path: Path, *, group: str | None = None, split: str = "validation") -> list[Record]:
    """Load JSONL records, optionally filtered by group prefix and split."""
    records = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("split") != split:
                continue
            if group is not None and not rec.get("item_id", "").startswith(group):
                continue
            records.append(rec)
    return records


# ── Accuracy ──────────────────────────────────────────────────────────────────


def accuracy(records: list[Record]) -> float:
    """Fraction of records where ``correct`` is True."""
    if not records:
        return 0.0
    return sum(1 for r in records if r.get("correct")) / len(records)


def accuracy_by_group(records: list[Record]) -> dict[str, float]:
    """Return per-group accuracy, keyed by the prefix before the first '-'."""
    groups: dict[str, list[Record]] = defaultdict(list)
    for rec in records:
        item_id = rec.get("item_id", "")
        group = item_id.split("-")[0] if "-" in item_id else item_id
        groups[group].append(rec)
    return {group: accuracy(recs) for group, recs in groups.items()}


# ── Bootstrap CI ──────────────────────────────────────────────────────────────


def paired_bootstrap_ci(
    a_correct: list[bool],
    b_correct: list[bool],
    *,
    n_bootstrap: int = 10_000,
    seed: int = 20260101,
    ci_level: float = 0.95,
) -> tuple[float, float]:
    """Paired bootstrap 95 % CI on accuracy_A - accuracy_B.

    Returns (lower_bound, upper_bound) in percentage points.
    Gate passes when both bounds exclude zero in the direction of the hypothesis.

    Args:
        a_correct: Per-item correctness for system A (P1).
        b_correct: Per-item correctness for system B (B-LLM).
        n_bootstrap: Number of bootstrap resamples.
        seed: Fixed seed for reproducibility (use manifest eval_run seed).
        ci_level: Confidence level, e.g. 0.95 for 95 %.
    """
    if len(a_correct) != len(b_correct):
        raise ValueError("a_correct and b_correct must have the same length")
    if not a_correct:
        return 0.0, 0.0

    rng = random.Random(seed)
    n = len(a_correct)
    deltas: list[float] = []
    for _ in range(n_bootstrap):
        idx = [rng.randrange(n) for _ in range(n)]
        da = sum(a_correct[i] for i in idx) / n
        db = sum(b_correct[i] for i in idx) / n
        deltas.append((da - db) * 100)  # convert to percentage points
    deltas.sort()
    alpha = (1 - ci_level) / 2
    lo = deltas[int(math.floor(alpha * n_bootstrap))]
    hi = deltas[int(math.floor((1 - alpha) * n_bootstrap))]
    return lo, hi


# ── Energy ────────────────────────────────────────────────────────────────────


def joules_per_correct_task(records: list[Record]) -> float | None:
    """Total energy divided by number of correct tasks.

    Returns None when no energy data is present.
    """
    correct_energy = [
        r["energy_joules"]
        for r in records
        if r.get("correct") and r.get("energy_joules") is not None
    ]
    if not correct_energy:
        return None
    return sum(correct_energy) / len(correct_energy)


# ── Latency ───────────────────────────────────────────────────────────────────


def percentile_latency(records: list[Record], percentile: float) -> float | None:
    """Return the p-th percentile of ``wall_time_ms`` across records.

    Args:
        percentile: e.g. 50 for p50, 95 for p95.
    """
    times = sorted(r["wall_time_ms"] for r in records if r.get("wall_time_ms") is not None)
    if not times:
        return None
    idx = int(math.ceil(percentile / 100 * len(times))) - 1
    return times[max(0, idx)]


# ── Memory ────────────────────────────────────────────────────────────────────


def peak_vram_gb(records: list[Record]) -> float | None:
    """Maximum ``peak_vram_mb`` across records, converted to GB."""
    vrams = [r["peak_vram_mb"] for r in records if r.get("peak_vram_mb") is not None]
    if not vrams:
        return None
    return max(vrams) / 1024.0


# ── Gate helpers ──────────────────────────────────────────────────────────────


def gate_q_accuracy(
    p1_records: list[Record],
    bllm_records: list[Record],
    *,
    threshold_pp: float = 5.0,
    seed: int = 20260101,
) -> dict[str, Any]:
    """Evaluate the G-Q accuracy criterion.

    P1 must beat B-LLM by at least ``threshold_pp`` percentage points,
    with the 95 % CI excluding zero.

    Returns a dict with 'passes', 'difference_pp', 'ci_lo', 'ci_hi', 'detail'.
    """
    p1_correct = [bool(r.get("correct")) for r in p1_records]
    bllm_correct = [bool(r.get("correct")) for r in bllm_records]
    diff_pp = (accuracy(p1_records) - accuracy(bllm_records)) * 100
    ci_lo, ci_hi = paired_bootstrap_ci(p1_correct, bllm_correct, seed=seed)
    passes = diff_pp >= threshold_pp and ci_lo > 0
    return {
        "passes": passes,
        "difference_pp": round(diff_pp, 2),
        "ci_lo": round(ci_lo, 2),
        "ci_hi": round(ci_hi, 2),
        "threshold_pp": threshold_pp,
        "detail": (
            f"{diff_pp:+.1f} pp, 95% CI [{ci_lo:+.1f}, {ci_hi:+.1f}]"
            f" — {'PASSES' if passes else 'FAILS'}"
        ),
    }


def gate_q_energy(
    p1_records: list[Record],
    bllm_records: list[Record],
    *,
    energy_cap_ratio: float = 1.0,
) -> dict[str, Any]:
    """Evaluate the G-Q energy criterion.

    P1 energy per correct task must be at most ``energy_cap_ratio`` times B-LLM's.
    Returns a dict with 'passes', 'p1_j_per_correct', 'bllm_j_per_correct', 'ratio'.
    """
    p1_j = joules_per_correct_task(p1_records)
    bllm_j = joules_per_correct_task(bllm_records)
    if p1_j is None or bllm_j is None or bllm_j == 0:
        return {
            "passes": False,
            "p1_j_per_correct": p1_j,
            "bllm_j_per_correct": bllm_j,
            "ratio": None,
            "detail": "UNMEASURED — energy data missing",
        }
    ratio = p1_j / bllm_j
    passes = ratio <= energy_cap_ratio
    return {
        "passes": passes,
        "p1_j_per_correct": round(p1_j, 4),
        "bllm_j_per_correct": round(bllm_j, 4),
        "ratio": round(ratio, 4),
        "detail": (
            f"P1 / B-LLM energy ratio = {ratio:.3f} "
            f"(cap {energy_cap_ratio:.2f}) — {'PASSES' if passes else 'FAILS'}"
        ),
    }


# ── Config hash ───────────────────────────────────────────────────────────────


def config_hash(config: dict[str, Any]) -> str:
    """SHA-256 of the config dict (sorted keys, UTF-8 JSON)."""
    canonical = json.dumps(config, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

