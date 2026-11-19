# Project Kestrel — Canonical Evaluation Scoring Specification

**Document:** `docs/decisions/scoring_spec.md`  
**Date:** 2026-11-19  
**Status:** FROZEN & AUTHORITATIVE (Decision D14 / Gate Requirement)  
**Authors:** Member A & Member B  

---

## 1. Overview & Golden Rule

This document defines the official, immutable scoring specifications for all 6 task groups across Project Kestrel Prototype 1 (Suite v2.0).
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
- **Primary Metric**: Normalized Exact Match with Canonical Span Extraction (`normalized_exact_match`).
- **Extraction & Normalization Rules**:
  1. **Span Extraction**: Trailing punctuation and conversational sentence wrappers (`"X was born on Y"`, `"According to the text, the answer is Y"`) are stripped by targeting the concluding entity span.
  2. **Case, Punctuation & Articles**: Lowercased, trailing punctuation removed, leading English articles (`the`, `a`, `an`) stripped.
  3. **Date Comparisons**:
     - Both prediction and target are parsed to standard ISO dates (`YYYY-MM-DD`).
     - **Strict Date Rule**: A year alone (`1072`) is **NOT** credited for a full-date question (`24 November 1072`). A year alone is credited if and only if the target key is just a year (`1072`).
  4. **Number Formatting**:
     - Internal commas in numbers are stripped (`912,490` $\to$ `912490`).
     - Textual multipliers are normalized (`17 million` $\to$ `17000000` or numeric `17` when comparing population units).
  5. **Aliases**:
     - Match is credited if the prediction matches the canonical target OR any explicitly verified alias in `item["metadata"]["aliases"]`.
- **Secondary Diagnostic Metrics** (Reported for analysis, not gate criteria):
  - **Token F1**: Word-level harmonic mean of precision and recall.
  - **Restricted Containment**: Substring containment permitted only when prediction is $\le 8$ words and contains no list separators.

### E. Memory Probe (`memory_probe`, Personal History Logs)
- **Primary Metric**: Recent Value Match & Stale Fact Rejection (`key_from_source_history`).
- **Evaluation**:
  1. Evaluates exact match against the latest chronological log entry (`metadata.target`).
  2. For the 30 stale-fact items, explicitly verifies that the model does NOT output deprecated/historical values (`metadata.stale_values`), enforcing Gate G-M.
- **Scoring**: Binary $\{0, 1\}$.
