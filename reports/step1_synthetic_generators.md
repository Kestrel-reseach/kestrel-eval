# Step 1 — Synthetic Generators & Stale-Fact Scorer Specification

**Date**: 2026-11-18  
**Repository**: `kestrel-eval` (Branch: `step-1-synthetic-generators`)  
**Skill Reference**: `suite-split-hash`  
**Governing Decisions**:
- **Decision D1**: Locked-test partition sizes: math 200, memory probe 100 (30 stale-fact), code 100.
- **Decision D3**: Synthetic histories only (`personal_data: synthetic_only`).
- **Gate G-M**: Memory slice gate requires stale-fact error ratio $\le 0.50$ of plain external memory.

---

## 1. Executive Summary

This report specifies the deterministic procedural generators developed for synthetic task generation in Project Kestrel Step 1.
All generators take an explicit integer seed (`random.Random(seed)`) to ensure bitwise reproducibility across runs.
Crucially, PR 2 provides:
1. **Math Word Problems**: Multi-step word problems with step-by-step scratchpad derivations and exact numeric answers (`exact_numeric`).
2. **Personal-Memory Probe Suite**: 100% synthetic chronological interaction histories (D3) featuring **30 stale-fact items** with explicit event timestamps, source channels, and a specialized **rejection scorer** that flags outdated values.
3. **Synthetic Code Suite**: Fresh algorithmic programming problems with zero web-leakage risk and comprehensive unit test suites (`unit_tests_pass`).

---

## 2. Math Word Problem Generator (`math_generator.py`)

- **Group Key**: `math`
- **Answer Check**: `exact_numeric`
- **Seed Control**: Takes explicit integer seed (e.g. `20260101`).
- **Algorithmic Problem Families**:
  1. *Shopping & Budgeting*: Multi-item purchases with discounts, coupons, and change calculations.
  2. *Travel & Velocity*: Multi-leg journeys with varying speeds and travel times.
  3. *Work Rates & Productivity*: Craftsmen and collaborative machinery outputs over shifts.
  4. *Financial Balances*: Sequential deposits, compounding accruals, and withdrawals.
  5. *Geometry & Fencing*: Rectangular borders, perimeters, and unit installation costs.
  6. *Tournament Scoring*: Cumulative points with bonuses, penalties, and multipliers.
- **Answer Extraction**: Automatically extracts the final integer/decimal value (marked with `#### <value>`).

---

## 3. Personal-Memory Probe & Stale-Fact Scorer (`memory_probe_generator.py`, `stale_fact_scorer.py`)

### A. Synthetic Chronological Histories (Decision D3)
In strict compliance with `rules.md` ("Never commit real personal data") and Decision D3 ("synthetic histories only"), all memory probe items are generated from procedural synthetic templates. Real personal data is zero.

### B. Partition Composition ($N = 100$ items)
- **30 Stale-Fact Items**:
  - An attribute (e.g. city of residence, manager, daily vehicle, preferred coffee bean, gym split, primary phone, side-project repo) changes across chronological timestamps ($T_1 < T_2 < T_3$).
  - Target: The **latest value** ($V_3$ at $T_3$).
  - Stale Values: Outdated historical values ($V_1$ at $T_1$, $V_2$ at $T_2$) tracked in item metadata.
  - Channels: Realistic synthetic headers, e.g. `[2026-03-12 09:15 | Channel: apartment_lease_email]`.
- **70 Static Recall Items**:
  - Attributes that remain invariant over time (e.g. birthdates, medical allergies, emergency contacts, frequent flyer numbers, terminal fonts).

### C. Stale-Fact Rejection Scorer
The scoring function `score_memory_probe_response()` enforces the following rules:
- **PASS (`correct: True, score: 1.0, stale_fact_error: False`)**:
  - The model outputs the latest value ($V_3$) and does not endorse any stale value.
  - Or, the model explicitly describes the temporal transition (e.g. *"You previously used X, but you recently switched to Y"*).
- **STALE-FACT ERROR (`correct: False, score: 0.0, stale_fact_error: True`)**:
  - The model outputs an outdated value ($V_1$ or $V_2$) instead of the current value.
  - Or, the model outputs both values ambiguously without temporal distinction.
- **MISS (`correct: False, score: 0.0, stale_fact_error: False`)**:
  - The model outputs an irrelevant response where neither current nor stale values appear.

This directly measures the **G-M pass gate**: ensuring stale-fact errors under write-gated memory are $\le 50\%$ of plain external memory.

---

## 4. Synthetic Code Task Generator (`code_generator.py`)

- **Group Key**: `code`
- **Answer Check**: `unit_tests_pass`
- **Rationale**: Replaces/augments public benchmarks (HumanEval N=164 is too small and heavily memorized; MBPP is contaminated) with unmemorized synthetic tasks.
- **Problem Categories**:
  - String run-length compression and decompression.
  - Stable top-k frequency counting.
  - Sliding window extrema.
  - Balanced multi-bracket verification.
  - Longest unique substring calculation.
  - 2D matrix rotations and spiral order traversals.
  - Two-pointer sorted list merging.
  - Prime factorization with multiplicity.
  - Contiguous maximum subarray sums (Kadane's algorithm).
- **Self-Verification**: Every generated task executes its canonical solution against its test harness in an isolated Python subprocess during generation; any failing task raises `RuntimeError` immediately.

---

## 5. Test Suite Verification

- **Test Suite**: [`tests/test_generators.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_generators.py)
  - Math determinism and item verification (`verify_math_item`).
  - Memory probe proportions (30 stale-fact, 70 static) and chronological order ($T_1 < T_2 < T_3$).
  - Rejection scorer: verified detection of latest value, rejection of stale value, and recognition of temporal change explanations.
  - Code generator: determinism and execution of unit tests on all canonical solutions.
