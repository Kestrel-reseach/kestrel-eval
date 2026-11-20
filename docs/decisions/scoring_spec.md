# Project Kestrel — Canonical Evaluation Scoring Specification

**Document:** `docs/decisions/scoring_spec.md`  
**Date:** 2026-11-19  
**Status:** FROZEN & AUTHORITATIVE (Decisions D14, D15, D16 / Suite v2.1)  
**Frozen at Git Commit:** `778e7b1` (Branch `suite-v2`, updated with Deviation Dev-01 for Suite v2.1)  
**Tuning Provenance:** Developed and calibrated strictly against Suite v1 mock/pilot outputs prior to Suite v2 generation. Zero tuning was performed on Suite v2 validation or locked partitions.  
**Authors:** Member A & Member B  

---

## 1. Overview & Golden Rule

This document defines the official, immutable scoring specifications for all 6 task groups across Project Kestrel Prototype 1 (Suite v2.1).
Per project rules:
> **"Never change a metric or threshold after seeing results."**  
All metrics defined herein are frozen prior to any baseline candidate evaluation (R4) or Frontier reference ($F$) runs.

---

## 2. Group Scoring Specifications

### A. Math Word Problems (`math`, GSM8K & Synthetic Word Problems)
- **Primary Metric**: Strict Numeric Equivalence (`exact_numeric`).
- **Extraction Protocol**:
  1. Searches for explicit final answer tags: `#### <number>`, `Final Answer: <number>`, `Answer: <number>`.
  2. Searches for LaTeX boxed notation: `\boxed{<number>}`.
  3. Falls back to trailing numeric values on the concluding line of the solution.
- **Evaluation**: The extracted number $x_{\text{pred}}$ is compared against ground truth $x_{\text{target}}$ within tolerance:
  $$|x_{\text{pred}} - x_{\text{target}}| \le 10^{-4} \times \max(1.0, |x_{\text{target}}|)$$
- **Scoring**: Binary $\{0, 1\}$.

### B. Multiple-Choice Questions (`science_mcq` & `knowledge_mcq`)
- **Primary Metric**: Option Key Match (`answer_key`).
- **Extraction Protocol (Rule F8a Precedence)**:
  1. Exact single letter match (`A`, `B`, `C`, `D` or `(A)`, `[B]`).
  2. LaTeX boxed format (`\boxed{A}`).
  3. Single-line declarative statements: `"the correct answer is X"`, `"Answer: X"`, `"Final Answer: X"`. Declarative statements always win over option lists.
  4. Single option line: If and only if the output consists of a single leading option line (`"C) Metamorphic rock"`), returns `'C'`.
  5. Option list rejection: If multiple lines begin with option markers (`A)`, `B)`, etc.) and no declarative statement is present, returns `None` (uncompleted list).
- **Evaluation**: Extracted letter must exactly equal ground truth target letter $k \in \{\text{A}, \text{B}, \text{C}, \text{D}\}$.
- **Scoring**: Binary $\{0, 1\}$.

### C. Code Generation (`code`, MBPP / HumanEval & Synthetic Functions)
- **Primary Metric**: Executable Unit Test Pass Rate (`unit_tests_pass`).
- **Execution Protocol**:
  1. Extracted Python code is parsed from ```python ... ``` code fences (or raw text).
  2. The code is assembled with `metadata.entry_point` and `metadata.test_code`.
  3. Executed in a sterile, temporary subprocess sandbox with resource limits (`RLIMIT_AS` 1 GB, wall timeout 5.0 s, network isolation).
- **Evaluation**: Passes if and only if the test harness exits with return code 0 (zero assertion errors or exceptions).
- **Scoring**: Binary $\{0, 1\}$.

### D. Knowledge Question Answering (`knowledge_qa`, Wikipedia & Fictional Store)
- **Primary Metric**: **Normalized Match** (`normalized_match`).  
  *Note:* Literal Exact Match (`literal_exact_match`, raw string equality without span extraction or date normalization) is reported side-by-side for comparison and full transparency.
- **Extraction & Normalization Rules**:
  1. **Span Extraction**: Trailing punctuation and conversational sentence wrappers (`"X was born on Y"`, `"According to the text, the answer is Y"`) are stripped by targeting the concluding entity span.
  2. **Case, Punctuation & Articles**: Lowercased, trailing punctuation removed, leading English articles (`the`, `a`, `an`) stripped.
  3. **Date Comparisons**:
     - Both prediction and target are parsed to standard ISO dates (`YYYY-MM-DD`).
     - **Strict Date Rule**: A year alone (`1072`) is **NOT** credited for a full-date question (`24 November 1072`). A year alone is credited if and only if the target key is just a year (`1072`).
  4. **Number & Unit Formatting**:
     - Internal commas in numbers are stripped (`912,490` $\to$ `912490`).
     - Textual multipliers are normalized (`17 million` $\to$ `17000000`).
     - Common trailing entity/unit words (`inhabitants`, `people`, `residents`) are handled so that numbers with units match the numeric count.
  5. **Profession Lists vs. Single Target**:
     - A prediction that emits a multi-element list (e.g. `"singer, actress, dancer, and model"`) does **NOT** match a single target occupation (e.g. `"actress"`). The answer must match the specific targeted occupation or a verified alias.
  6. **Aliases**:
     - Match is credited if the prediction matches the canonical target OR any explicitly verified alias in `item["metadata"]["aliases"]`.
- **Secondary Diagnostic Metrics** (Reported for analysis, not gate criteria):
  - **Literal Exact Match**: Raw exact string equality after standard whitespace trim.
  - **Token F1**: Word-level harmonic mean of precision and recall. Token F1 is computed on the extracted answer span (via `score_token_f1`), resolving the earlier discrepancy where evaluating raw conversational text penalized precision.
  - **Restricted Containment**: Substring containment permitted only when prediction is $\le 8$ words and contains no list separators.

### E. Memory Probe (`memory_probe`, Personal History Logs)
- **Primary Metric**: Recent Value Match & Stale Fact Rejection (`key_from_source_history`).
- **Evaluation**:
  1. Evaluates exact match against the latest chronological log entry (`metadata.target`).
  2. For the 100 stale-fact items (expanded from 30 per Owner Decision D16), explicitly verifies that the model does NOT output deprecated/historical values (`metadata.stale_values`), enforcing Gate G-M with $n_{\text{eff}} = 100$.
- **Scoring**: Binary $\{0, 1\}$.

---

## 3. Golden Test Suite Verification

Scoring integrity is continuously verified against a 115-case golden test suite (`tests/test_scoring_golden.py`). This fixture covers:
- Multiple-choice edge cases (declarative overrides, uncompleted lists, single option lines, boxed keys).
- Adversarial MCQ cases (guarding against English indefinite article "A", split lines, option lists, lowercase letters, two letters, empty output).
- Strict numeric equivalence with tolerances and LaTeX formatting.
- Subprocess sandbox isolation for code unit test execution.
- Strict date parsing, numeric unit normalization, multi-occupation list rejection, and alias handling for knowledge QA.
- Stale fact rejection and chronological log retrieval for memory probe.

---

## 4. Deviation Log (Post-Freeze Refinements)

### Deviation Dev-01: MCQ Extractor Refinement & Article Guard
- **Version**: 2.1.1
- **Date**: 2026-11-20
- **Scope**: `evaluation/extractors.py:extract_mcq_answer`
- **Reason**: 
  1. Permits valid model outputs emitting a single bare letter on line 1 followed by newline explanations (e.g., `"A\n\nExplanation: ..."`).
  2. Extends bracket recognition to include square brackets (e.g. `"[D]"`) and explicit option prefixes (e.g. `"Option (A)"`, `"Option A is the best answer."`).
  3. **Adversarial Article Guard**: Strictly guards against false positives from the English indefinite article "A" (e.g. `"A car is moving fast"` $\to$ `None`, `"A dog barked"` $\to$ `None`) and multi-line lowercase broken continuations (`"A\ncar is moving fast"` $\to$ `None`).
- **Effect on Scores**:
  - Re-scored against all 120 saved R2 verification outputs (`reports/step2/r2_verification_samples.jsonl`): **0 score deltas (0 changes)**.
  - Re-scored against all 300 Phase B calibration pilot records (`reports/step2/phase_b_pilot_records.jsonl`): **0 score deltas (0 changes)**.
  - Verified across 115 golden test cases in `tests/test_scoring_golden.py` (100% pass).

---

## 5. Peak VRAM Metric Definition (Gate G-R Standard)

For Gate G-R compliance, **Peak VRAM** is formally defined as:
- **Canonical Metric**: **NVML process-level used memory** (resident GPU VRAM allocated to the model inference process, queried via `pynvml.nvmlDeviceGetComputeRunningProcesses` or equivalent NVML process query).
- **Measurement Condition**: Measured after warm-up at a **2048-token context length**.
- **Side-by-Side Reporting**: PyTorch memory stats (`torch.cuda.memory_allocated()` and `torch.cuda.memory_reserved()`) must be reported alongside NVML process memory for diagnostic transparency, capturing framework caching and CUDA runtime overhead.
- **Enforcement**: Defined in `evaluation/metrics.py:get_vram_breakdown_mb()` and applied uniformly across all candidate and frontier evaluation scripts.

---

## 6. Run Protocol & Truncation Safeguard Rule

- **Truncation Safeguard**: Token generation caps calibrated during pilot runs (Phase B) are preliminary estimates. During the full 1,250-item baseline evaluation run (Phase C), truncation rates must be re-checked for every group.
- **Violation Threshold**: If any task group exhibits a truncation rate of **$\ge 1.0\%$**, the run is flagged as a truncation violation.
- **Action Required**: The generation cap for that group must be increased and the group re-evaluated.
- **Integrity Rule**: **Items are never dropped or omitted** from the suite to satisfy truncation criteria.



