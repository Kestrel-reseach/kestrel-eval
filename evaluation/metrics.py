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
    "MANDATORY_ENERGY_LABEL",
    "accuracy",
    "accuracy_by_group",
    "compute_half_width",
    "config_hash",
    "format_energy_table",
    "format_half_widths_table",
    "gate_q_accuracy",
    "gate_q_energy",
    "joules_per_correct_task",
    "load_records",
    "paired_bootstrap_ci",
    "peak_vram_gb",
    "percentile_latency",
]

MANDATORY_ENERGY_LABEL: str = "Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."

Record = dict[str, Any]


# ── Loading ────────────────────────────────────────────────────────────────────


def load_records(
    path: Path, *, group: str | None = None, split: str = "validation"
) -> list[Record]:
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
    """Total energy across all attempts divided by number of correct tasks.

    Joules per correct task measures the total energy cost of the system
    (including failed passes, retries, and incorrect answers) amortized over
    the number of correct solutions among items with energy measurements.

    Returns None when no energy data is present or zero tasks were correct.
    """
    measured = [r for r in records if r.get("energy_joules") is not None]
    if not measured:
        return None

    correct_count = sum(1 for r in measured if r.get("correct"))
    if correct_count == 0:
        return None

    total_energy = sum(r["energy_joules"] for r in measured)
    return total_energy / correct_count


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
    for r in p1_records + bllm_records:
        if r.get("simulated") or r.get("inference_mode") == "simulated":
            raise ValueError(
                "Provenance guard violated: Simulated records cannot enter pass gates per kestrel-core.md."
            )
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
    for r in p1_records + bllm_records:
        if r.get("simulated") or r.get("inference_mode") == "simulated":
            raise ValueError(
                "Provenance guard violated: Simulated records cannot enter pass gates per kestrel-core.md."
            )
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


# ── Sample size & CI half-width helper ─────────────────────────────────────────


def compute_half_width(n: int, p: float = 0.5, ci_level: float = 0.95) -> float:
    """Return the asymptotic Wald 95% binomial CI half-width in percentage points.

    Args:
        n: Sample size.
        p: Baseline proportion (default 0.5 for maximum variance).
        ci_level: Confidence level (default 0.95 -> z ≈ 1.95996).
    """
    if n <= 0:
        return 0.0
    # Normal quantile for ci_level
    # for 0.95: z ≈ 1.959963984540054
    z = 1.959963984540054 if ci_level == 0.95 else 1.96
    se = math.sqrt(p * (1.0 - p) / n)
    return z * se * 100.0


def format_half_widths_table() -> str:
    """Return a formatted comparison table of 95% half-widths for both sizes_are readings."""
    groups = [
        ("math", 200),
        ("science_mcq", 200),
        ("knowledge_mcq", 300),
        ("code", 100),
        ("knowledge_qa", 300),
        ("memory_probe", 100),
    ]
    lines = [
        "Group          | Listed | Reading A: total (n_locked, ±pp) | Reading B: per_partition (n_locked, ±pp)",
        "---------------|--------|-----------------------------------|-----------------------------------------",
    ]
    for name, listed in groups:
        n_a = int(listed * 0.20)
        hw_a = compute_half_width(n_a)
        n_b = listed
        hw_b = compute_half_width(n_b)
        lines.append(
            f"{name:<14} | {listed:<6} | n={n_a:<3} (±{hw_a:.1f} pp)                  | n={n_b:<3} (±{hw_b:.1f} pp)"
        )
    return "\n".join(lines)


def format_energy_table(
    headers: list[str],
    rows: list[list[Any]],
    *,
    mandatory_label: str | None = None,
) -> str:
    """Format a markdown table containing energy results.

    Enforcement rule:
    Any table or report presenting energy measurements MUST explicitly contain the exact
    mandatory label:
    'Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.'
    If the mandatory label is missing or incorrect, this function refuses to generate
    the report and raises ValueError.
    """
    if mandatory_label != MANDATORY_ENERGY_LABEL:
        raise ValueError(
            "Refusing to generate energy report without mandatory label: "
            f"'{MANDATORY_ENERGY_LABEL}'"
        )

    for row in rows:
        for cell in row:
            if isinstance(cell, str) and "simulated" in cell.lower():
                raise ValueError(
                    "Provenance guard violated: Simulated data cannot enter energy tables per kestrel-core.md."
                )

    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return f"> [!IMPORTANT]\n> {mandatory_label}\n\n" + "\n".join(
        [header_line, sep_line] + row_lines
    )
