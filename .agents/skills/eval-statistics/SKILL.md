---
name: eval-statistics
description: >
  Statistical analysis for Kestrel Prototype 1 gate arithmetic.
  Load this skill when computing confidence intervals, checking gates,
  or reporting accuracy figures.
---

# Skill: eval-statistics

## Confidence intervals

Use **paired bootstrap** (not standard error) for all gate comparisons.

```python
import random

def paired_bootstrap_ci(
    a_correct: list[bool],
    b_correct: list[bool],
    *,
    n_bootstrap: int = 10_000,
    seed: int = 20260101,
    ci_level: float = 0.95,
) -> tuple[float, float]:
    """Return (lower, upper) CI on accuracy_A - accuracy_B."""
    rng = random.Random(seed)
    n = len(a_correct)
    deltas = []
    for _ in range(n_bootstrap):
        idx = [rng.randrange(n) for _ in range(n)]
        da = sum(a_correct[i] for i in idx) / n
        db = sum(b_correct[i] for i in idx) / n
        deltas.append(da - db)
    deltas.sort()
    alpha = (1 - ci_level) / 2
    lo = deltas[int(alpha * n_bootstrap)]
    hi = deltas[int((1 - alpha) * n_bootstrap)]
    return lo, hi
```

A gate **passes** when the entire CI excludes zero in the direction of the
hypothesis (e.g., both bounds positive for "P1 > B-LLM").

## Realistic CI widths (95 %)

| Group size | Half-width |
|------------|-----------|
| 100 items  | ±9–10 pp  |
| 200 items  | ±6–7 pp   |
| 300 items  | ±5–6 pp   |

The 100-item groups (code, memory probe) are exploratory; treat as
directional evidence, not conclusive results.

## Gate arithmetic

| Gate | Formula | Passes when |
|------|---------|-------------|
| G-Q (accuracy) | `acc_P1 - acc_BLLM >= 5 pp`, CI excludes 0 | Both CI bounds > 0 |
| G-Q (energy)   | `energy_P1 <= energy_BLLM` | — |
| G-Q (alt.)     | `acc_P1 ≈ acc_BLLM`, `energy_P1 <= 0.50 × energy_BLLM` | — |
| G-M stale      | `stale_errors_P1 <= 0.50 × stale_errors_plain` | — |
| no-regression  | `acc_step_i - acc_prev >= -3 pp` | — |

## Fixed seeds

All bootstrap resamples use a fixed seed from `manifest.yaml`:

```python
seed = manifest["seeds"]["eval_run"]  # 20260102
```

Do not change seeds after any results have been computed.

## Reporting format

```
Group: math (n=200, validation)
System A (P1): accuracy = 0.72 (144/200)
System B (B-LLM): accuracy = 0.65 (130/200)
Difference: +7.0 pp; 95% CI [+1.2 pp, +12.9 pp] — CI excludes 0 ✓
Gate G-Q: PASSES (accuracy criterion)
```

