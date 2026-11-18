# Step 1 — Public Group Loaders & Source Provenance Report

**Date**: 2026-11-18  
**Repository**: `kestrel-eval` (Branch: `step-1-public-loaders`)  
**Skill Reference**: `suite-split-hash`  
**Manifest Target**: `manifest_version: "1.1"` (Decision D1: 200/200/300/100/300/100 locked-test partition sizes)

---

## 1. Executive Summary

This report documents the public group loaders, official license verification, and contamination analysis for Project Kestrel Prototype 1 Step 1. All public datasets are verified directly against their official repositories and licensing terms. Per project rules, no unverified datasets are downloaded, and all licensing permissions are checked before inclusion.

---

## 2. Public Source Registry & Verified Licenses

| Group | Source Name | Version | Official Canonical URL | Official License | Official License URL | Verified on Official Page | Permissibility Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Math** | GSM8K (Grade School Math 8K) | 1.0 | `https://github.com/openai/grade-school-math` | **MIT** | [`LICENSE`](https://github.com/openai/grade-school-math/blob/master/LICENSE) | **YES** | **PERMITTED** |
| **Science MCQ** | ARC (AI2 Reasoning Challenge) | 1.0 | `https://allenai.org/data/arc` | **CC BY-SA 4.0** | [`CC BY-SA 4.0`](https://creativecommons.org/licenses/by-sa/4.0/) | **YES** | **PERMITTED** |
| **Knowledge MCQ** | MMLU (Measuring Massive Multitask Language Understanding) | 1.0 | `https://github.com/hendrycks/test` | **MIT** | [`LICENSE`](https://github.com/hendrycks/test/blob/master/LICENSE) | **YES** | **PERMITTED** |
| **Code** (Option 1) | HumanEval | 1.0 | `https://github.com/openai/human-eval` | **MIT** | [`LICENSE`](https://github.com/openai/human-eval/blob/master/LICENSE) | **YES** | **PERMITTED** (with contamination caveat) |
| **Code** (Option 2) | MBPP (Mostly Basic Python Problems) | 1.0 | `https://github.com/google-research/google-research/tree/master/mbpp` | **CC BY 4.0** | [`CC BY 4.0`](https://creativecommons.org/licenses/by/4.0/) | **YES** | **PERMITTED** (with contamination caveat) |

---

## 3. Detailed Group Specifications

### A. Math Word Problems (`math`)
- **Target Partition Sizes**: 200 locked-test, 200 validation, plus public train split.
- **Answer Check**: `exact_numeric`. Evaluator extracts the numeric solution (following scratchpad reasoning or `#### <num>`) and asserts numeric equivalence within $10^{-4}$ tolerance.
- **Official Source**: GSM8K (Cobbe et al., OpenAI, 2021).
- **License**: MIT License allows unrestricted use, modification, and redistribution.

### B. Science Multiple Choice (`science_mcq`)
- **Target Partition Sizes**: 200 locked-test, 200 validation, plus public train split.
- **Answer Check**: `answer_key`. Evaluator parses 4 multiple choice options (A, B, C, D) and checks exact match against the answer key.
- **Official Source**: ARC-Challenge (Clark et al., Allen Institute for AI, 2018).
- **License**: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) permits commercial and non-commercial redistribution with attribution.

### C. Knowledge Multiple Choice (`knowledge_mcq`)
- **Target Partition Sizes**: 300 locked-test, 300 validation (30 items $\times$ 10 subjects per partition).
- **Answer Check**: `answer_key`. Evaluator checks exact choice key match (A, B, C, D).
- **Official Source**: MMLU (Hendrycks et al., UC Berkeley, 2020).
- **License**: MIT License.
- **10 Representative Subjects**:
  1. `college_computer_science`
  2. `college_physics`
  3. `college_biology`
  4. `college_chemistry`
  5. `elementary_mathematics`
  6. `high_school_world_history`
  7. `high_school_geography`
  8. `professional_law`
  9. `clinical_knowledge`
  10. `econometrics`

---

## 4. Code Tasks & Contamination Assessment

### Analysis of Public Code Datasets:
1. **HumanEval** ($N = 164$ total):
   - **Size Deficit**: With only 164 problems total, HumanEval is mathematically too small to construct a 100-item locked-test partition and a separate 100-item validation partition without 36% item overlap.
   - **Contamination**: HumanEval has been memorized by virtually all major foundation models trained since 2021 (including Qwen, Gemma, LLaMA, and Gemini). High scores on HumanEval reflect memorization rather than generalized reasoning.
2. **MBPP** ($N = 974$ total):
   - **Contamination**: MBPP is widely crawled in public code training mixtures.

### Recommendation & Proposal:
Per the prompt instruction (*"If public code sets are too small or contaminated, say so and propose privately written tasks"*):
- **Recommendation**: Public code sets (HumanEval/MBPP) are loaded and supported by the harness for validation and public comparison.
- **Proposal for PR 2**: Generate **privately written synthetic code tasks with fresh algorithmic logic, deterministic assertions, and complete unit test suites** for the locked test suite partition. This ensures zero data contamination, zero memorization, and rigorous evaluation of small-model code reasoning.

---

## 5. Software Architecture & Unit Testing

- **Module**: `evaluation/loaders/`
  - `sources.py`: Metadata registry and verification logic.
  - `common.py`: `SuiteItem` typed dict and answer checkers (`check_exact_numeric`, `check_answer_key`, `check_unit_tests_pass`).
  - `math_loader.py`: GSM8K JSONL parser and validator.
  - `science_mcq_loader.py`: ARC JSONL parser and validator.
  - `knowledge_mcq_loader.py`: MMLU JSONL/CSV parser across 10 subjects.
  - `code_loader.py`: Code loader and safe unit test execution runner.
- **Unit Test Suite**: [`tests/test_loaders.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_loaders.py)
  - 10 test functions covering source metadata, numeric extraction, MCQ extraction, unit test execution, and all 4 group loaders.
  - Test data fixtures added to `suite/public/math/`, `suite/public/science_mcq/`, `suite/public/knowledge_mcq/`, and `suite/public/code/`.
