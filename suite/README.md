# Project Kestrel — Suite v2.1 Handoff (Validation & Train Partitions)

> [!IMPORTANT]
> **Suite v2.1 Provenance & Dual-Arm Architecture (Owner Decisions D14, D16, D17)**:  
> Suite v2.1 implements private CSPRNG seed and salt generation for the locked test partition (D17), stores locked credentials in `$KESTREL_PRIVATE_DIR/locked_seed.env` (mode 0600), retires all v1 exposed locked personas with 25 private unique entities, and expands the memory probe to 150 items per partition (100 stale + 50 static per D16) to ensure statistical power under paired analysis.  
> The 5 benchmark groups (math, science_mcq, knowledge_mcq, code, knowledge_qa) in validation and train partitions remain **100.0% bit-for-bit identical** to Suite v2.0.

**Target Audience:** Member B (Core Modeling, Verification & Baselines)  
**Deliverable:** Evaluation Suite v2.1 — Validation & Train Partitions  
**Repository:** `kestrel-eval`  
**Date:** 2026-11-19  

---

## 1. Overview & Core Principles

Suite v2.1 provides the **1,250-item validation partition** and **1,250-item train partition** for Project Kestrel Prototype 1, structured across 6 task groups per **Decision D1** (`sizes_are: per_partition`, 3,750 total items across validation, locked-test, and train).

### Core Principles for Modeling (Member B):
1. **Develop and Tune Against Validation Only**: All model candidate selection, verifier threshold exploration, and retrieval tuning must use `split="validation"`.
2. **Train Partition for Verifier Training**: Member B's verifier head (Step 3 / Step 6) trains on `suite/train/`. For checkable groups, the raw public train files (`data/raw/`) also provide extensive additional training data.
3. **Verifier Family-Level Hold-Out Rule**: When evaluating verifier generalization, **Member B must hold out whole template families** (e.g. hold out 3-4 procedural math families, or an entire MMLU subject, or specific code algorithmic families) or hold out an entire task group. This guarantees the verifier learns genuine reasoning rather than memorizing template-specific syntactic idioms.
4. **Physical Isolation of Locked-Test**: The 1,250 locked-test items are physically quarantined outside the repository in `kestrel_private/locked_test/`. The loader enforces a strict permission guard (`PermissionError`). Locked-test is evaluated exactly **once** at Step 10.
5. **Dual-Arm Reporting**: Accuracy must always be reported separately for public benchmark arms (`Acc_public`) and synthetic/fictional arms (`Acc_synthetic`).

---

## 2. Suite v2.1 Composition Matrix

Each partition contains exactly **1,250 items** across the 6 task groups.

| Task Group | Partition | Arm | N (Items) | Template Families | Largest Family & Share | 95% CI Half-Width |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **math** | Validation | Public (GSM8K) | 100 | 1 | `gsm8k` (100, 50.0%) | ±9.80 pp |
| | Validation | Synthetic | 100 | 16 | Various (6–8, ~7.0%) | ±9.80 pp |
| | **Total** | **Combined** | **200** | **17** | **gsm8k (100, 50.0%)** | **±6.93 pp** |
| **science_mcq** | Validation | Public (ARC-Challenge) | 200 | 1 | `arc_challenge` (200, 100%) | ±6.93 pp |
| | **Total** | **100% Public** | **200** | **1** | **arc_challenge (200, 100%)** | **±6.93 pp** |
| **knowledge_mcq** | Validation | Public (MMLU 10 subj) | 300 | 10 | Equal (30 per subj, 10.0%) | ±5.66 pp |
| | **Total** | **100% Public** | **300** | **10** | **10 subjects (30 each, 10%)**| **±5.66 pp** |
| **code** | Validation | Public (MBPP) | 50 | 1 | `mbpp` (50, 50.0%) | ±13.86 pp |
| | Validation | Synthetic | 50 | 50 | 36 algorithmic types (1–2, ~2%) | ±13.86 pp |
| | **Total** | **Combined** | **100** | **51** | **mbpp (50, 50.0%)** | **±9.80 pp** |
| **knowledge_qa** | Validation | Real Wikipedia | 200 | 8 | `born_date` (55, 27.5% ≤ 30%) | ±6.93 pp |
| | Validation | Fictional (D13) | 100 | 4 | `born_date` / `death_date` (25, 25%) | ±9.80 pp (cluster: ±10.0 pp)|
| | **Total** | **Combined** | **300** | **8** | **born_date (80, 26.7% ≤ 30%)**| **±5.66 pp** |
| **memory_probe** | Validation | Synthetic (D3/D16) | 150 | 36 | 16 stale + 20 static | ±8.00 pp |
| | **Total** | **100% Synthetic** | **150** | **36** | **stale categories (100, 66.7%)**| **±8.00 pp** |
| **TOTAL** | **Validation** | **All Arms** | **1,250** | **123** | — | **±2.77 pp** |

*(The train partition and private locked-test partition adhere to the exact same group and arm composition).*

---

## 3. JSONL Record Schema (v2.1)

Every line in each `.jsonl` partition file is a valid JSON object adhering to the canonical schema:

### Universal Fields
- `id` / `item_id` (str): Canonical item identifier (e.g., `math_val_0001`, `sci_val_0042`, `kqa_lock_0150`).
- `group` (str): One of `math`, `science_mcq`, `knowledge_mcq`, `code`, `knowledge_qa`, `memory_probe`.
- `split` (str): `"validation"`, `"train"`, or `"locked_test"`.
- `prompt` (str): Model input prompt.
- `target` (str): Canonical ground-truth answer.
- `answer_check` (str): Primary frozen scoring metric name (`exact_numeric`, `answer_key`, `unit_tests_pass`, `normalized_exact_match`, `key_from_source_history`).
- `arm` (str): Data arm (`"public"`, `"synthetic"`, `"real_wikipedia"`, or `"fictional_entity"`).
- `template_family` (str): Granular template/subject identifier used for verifier hold-out partitioning (e.g. `gsm8k`, `travel`, `college_physics`, `is_palindrome`, `born_date`).
- `metadata` (dict): Extended provenance, source licensing, test harnesses, and entity attributes.

---

## 4. Benchmark Sources & Licensing

All public data sources are verified official releases with permissive academic/commercial licenses:

| Benchmark | Task Group | Version / Citation | License | Verified URL / Source |
| :--- | :--- | :--- | :--- | :--- |
| **GSM8K** | `math` (Public Arm) | Cobbe et al., 2021 | MIT | `https://github.com/openai/grade-school-math` |
| **ARC-Challenge** | `science_mcq` (100% Public) | Clark et al., 2018 | CC BY-SA 4.0 | `https://allenai.org/data/arc` |
| **MMLU** | `knowledge_mcq` (100% Public) | Hendrycks et al., 2020 | MIT | `https://github.com/hendrycks/test` |
| **MBPP** | `code` (Public Arm) | Austin et al., Google 2021 | CC BY 4.0 | `https://github.com/google-research/google-research/tree/master/mbpp` |
| **Wikipedia Abstracts** | `knowledge_qa` (Real Arm) | 2026-11-01 Foundation Dump | CC BY-SA 4.0 | Wikimedia Foundation (`dumps.wikimedia.org`) |
| **Fictional Entities** | `knowledge_qa` (Diagnostic Arm) | Project Kestrel (D13) | Project-Internal | Zero pretraining memorization reference |
| **Procedural Synthetic**| `math`, `code`, `memory_probe` | Project Kestrel | Project-Internal | Clean synthetic reference |

---

## 5. Verified File Hashes & Manifest v2.1

### Validation Partition (`suite/validation/`)
- `math.jsonl`: `36d28203fe4d3493e5cab1fa70828fe449410c8e11b6672934e78b977fef3408`
- `science_mcq.jsonl`: `e4a7ab87a6dd4b7e8b93152a1a65640cc4cae43d97dee93048473f40bf80a270`
- `knowledge_mcq.jsonl`: `69e9180eb213d3e0f444578723c0649f8781b424cb147b2cdb1fe9d3063c39bd`
- `code.jsonl`: `42d95b87814603c31fdcb5ebf7089b804620b20d6a85ea729088801378b8e7aa`
- `knowledge_qa.jsonl`: `9a501f364c45c9b44065ffc7ae07883516cef5ba64cb60d14ad52d95c6a2b73e`
- `memory_probe.jsonl`: `09b3fded3e53dd9db5b6a15236861bbe22d457963a27ed4d7038e3c40721ad44`

### Train Partition (`suite/train/`)
- `math.jsonl`: `027c36789149ca8da464eefb18c28681f7ebf69dfb4e97924b852484e7f3a0b0`
- `science_mcq.jsonl`: `4241c43a3c88cf07df8940f3bdd5095850fbe6370e1fb0efa54004784e71d2c2`
- `knowledge_mcq.jsonl`: `f7bb363b86e4bcfdae475b465288ed9c7aa61a3df646a5c113a9c8e2eebc3a49`
- `code.jsonl`: `d8f0fce3e375c1e99a3cd00742d6f88797df05d1dbb535e16ac0c4490c385fdc`
- `knowledge_qa.jsonl`: `23f09ab70a9636dd206e916a303eae67cb7d9278bc3894f11d28987c0e005bc5`
- `memory_probe.jsonl`: `0d736e8c3a34de2f635eb0aeb820f8e402c564d436f70bad2766b19089634689`

### Locked-Test Partition (`kestrel_private/locked_test/`, Out-of-Repo)
- `math.jsonl`: `2516fc845447352775e891845c2e1fcee4a6c02399aba3d4e69f737093fe9c51`
- `science_mcq.jsonl`: `aef023c27437e13fbe4af271aa589ac6f140ccbd72ea5c8177b7ee6e3313fcc6`
- `knowledge_mcq.jsonl`: `d83ce8a19a891dd159bff24d48b1bc5a9d250ddeb625387a5656859693c0799e`
- `code.jsonl`: `e807c55ff462535e80b81ee8cf640733c67abe2997ed86e44ec91511c066c20e`
- `knowledge_qa.jsonl`: `e1147853c87a5ac141dec5b77fd8373c926387c6ae087d93fd58cfd31d0c78ca`
- `memory_probe.jsonl`: `5468373aa172f81c9b4291e279cb74996a729911a48ff36341a10f84ba2dc0af`
- **Locked Root Hash (Suite v2.1)**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`
- **Superseded v2.0 Root Hash**: `39cbe48e161f75a1bd4b57e8abf555012fe7b3b515092d96cf5e843bb3a97b68`
- **Superseded v1.0 Root Hash**: `73a38ea8f35f606346903d6d6ec142ee85c184d00fa5ff7f6c382d55e9ef0fa5`

---

## 6. Python Usage Example

```python
from evaluation.suite import load_suite_partition

# 1. Load validation items for a specific group
math_items = load_suite_partition("validation", group="math")
public_math = [it for it in math_items if it.get("arm") == "public"]
synthetic_math = [it for it in math_items if it.get("arm") == "synthetic"]

print(f"Math validation: {len(public_math)} public GSM8K items, {len(synthetic_math)} synthetic items.")

# 2. Inspect template families for verifier hold-out
families = {it.get("template_family") for it in math_items}
print(f"Available template families: {families}")
```
