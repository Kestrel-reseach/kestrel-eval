# Step 1: Locked Suite Partitioning, Hashing & Leakage Report (PR 4)

> [!NOTE]
> **Suite v1 Superseded by Suite v2.0 (Decision D14 / Manifest v2.0)**:  
> The Suite v1 hashes below are superseded by Suite v2.0. The official locked root hash for Suite v2.0 is `39cbe48e161f75a1bd4b57e8abf555012fe7b3b515092d96cf5e843bb3a97b68`. Superseded v1 locked files have been archived in `/home/ash09/project_x/kestrel_private/superseded_v1_locked_test/`. See `suite/README.md` and `evaluation/manifest.yaml`.

**Date**: 2026-11-18 (Updated 2026-11-19)  
**Branch**: `step-1-splits-hashes-leakage`  
**Governing Decisions**: D1 (group & partition sizes), D2 (Wikipedia snapshot subset), D3 (synthetic memory probe), D4 (frozen gates), D8 (test hardware tier)

---

## 1. Suite Partition Structure (Decision D1)

Per Decision D1, group sizes apply per partition: 1,200 items in locked-test, 1,200 items in validation, and 1,200 items in train (3,600 total items).

| Group | Key | Partition Size | Total (3 splits) | Answer Check | Evaluation Type |
|---|---|---|---|---|---|
| Math word problems | `math` | 200 | 600 | `exact_numeric` | Multi-step reasoning with arithmetic scratchpads |
| Science MCQ | `science_mcq` | 200 | 600 | `answer_key` | Physics, Chemistry, Biology, Earth & Space (A-D) |
| Knowledge MCQ | `knowledge_mcq` | 300 | 900 | `answer_key` | MMLU 10 representative subjects (30 items × 10 subjects) |
| Code tasks | `code` | 100 | 300 | `unit_tests_pass` | Synthetic algorithmic tasks with verified unit tests |
| Knowledge QA | `knowledge_qa` | 300 | 900 | `key_match` | Wikipedia 2026-11 snapshot with character span match |
| Personal-memory probe | `memory_probe` | 100 | 300 | `key_from_source_history` | 30 stale-fact items + 70 static recall items |
| **Total Partition Size** | | **1,200** | **3,600** | | |

---

## 2. Statistical Precision: 95% Confidence Interval Half-Widths

Under worst-case binomial variance ($p = 0.5$, $\text{Var}(p) = 0.25$):
$$\text{Half-Width} = 1.96 \times \sqrt{\frac{p(1-p)}{N}} \times 100\%$$

- **$N = 100$ (`code`, `memory_probe`)**: $\pm 9.80\text{ percentage points}$
- **$N = 200$ (`math`, `science_mcq`)**: $\pm 6.93\text{ percentage points}$
- **$N = 300$ (`knowledge_mcq`, `knowledge_qa`)**: $\pm 5.66\text{ percentage points}$
- **Total Partition ($N = 1,200$)**: $\pm 2.83\text{ percentage points}$

This satisfies the plan requirement of detecting a 5 pp margin (G-Q) on checkable and store groups with high statistical power.

---

## 3. Locked-Test Hashes & Root Hash

In accordance with `rules.md` and `kestrel-core.md`, locked-test items are stored **strictly outside the git repository** at `KESTREL_PRIVATE_DIR` (`/home/ash09/project_x/kestrel_private/locked_test/`). Only their SHA-256 file hashes and the root hash are recorded in `evaluation/manifest.yaml`.

| Group | Locked-Test SHA-256 Digest |
|---|---|
| `math` | `25c052ee25cac22aa193d8386f425ec334bf89de9f0598064ae2f9dff1a52f1d` |
| `science_mcq` | `08e82a53794b6314d74aaefcd9bf58a21bef0ab2940579e2c2da7565bdd84172` |
| `knowledge_mcq` | `4fc1c7de12ea4f9da57b50733eb78f77369c856e46e1e23d4a4629a5871c10a6` |
| `code` | `3ea39eaea70d62d2cd77f533633a307a45e195e7d5a57a903ae8fcb471b9c7da` |
| `knowledge_qa` | `f994d4793291d59e4809a1e7588324fc1842a4d726900446e7394feffaa532b0` |
| `memory_probe` | `f0f819178d78523a8640161651816d8d50c50ce76974a6cc1ad39932cf019acd` |
| **Root Hash** | **`22fff5e005245148f85e29c75029e85034ada793ee6b7e7c33b130e8fd9e99b7`** |

*Root hash computed as SHA-256 over lexicographically sorted group key:hash lines.*

---

## 4. Partition Independence & Leakage Verification

Automated partition integrity checks executed via `evaluation/leakage.py`:
1. **Item ID Overlap**: Checked across all 3,600 items. **Zero overlaps found** (`check_no_id_overlap` passed).
2. **Exact Prompt Duplication**: Checked across all 3 partitions. **Zero duplicate prompts found** (`dups == []`).
3. **Answer-in-Prompt Leakage**: Evaluated for all items. **Zero ground-truth answer leaks in question text found** (`leaks == []`).
4. **Near-Duplicate Detection**: 4-gram Jaccard similarity detector implemented and verified in `tests/test_suite_and_leakage.py`.

---

## 5. Physical Separation and Isolation

- **In-Repository**:
  - `suite/validation/`: 1,200 JSONL items (available for local model development, verifier training, and validation tuning).
  - `suite/train/`: 1,200 JSONL items (available for training heads / prompts).
- **Out-of-Repository (`KESTREL_PRIVATE_DIR`)**:
  - `/home/ash09/project_x/kestrel_private/locked_test/`: 1,200 JSONL items.
  - Zero locked-test data files are tracked or present inside `kestrel-eval` repository (verified by `test_no_locked_test_data_in_repo()`).
  - No model evaluation or API call will touch this partition until Step 10.
