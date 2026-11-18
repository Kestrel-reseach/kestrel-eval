# Project Kestrel — Benchmark Contamination Analysis & Protocol Note

**Document:** `reports/CONTAMINATION.md`  
**Also Referenced As:** `reports/step1_contamination_note.md`  
**Step:** Step 1 (Suite v0, Contamination & Validation Handoff)  
**Author:** Member A (Evaluation, Measurement & Memory Lead)  
**Skill Reference:** `suite-split-hash`  
**Date:** 2026-11-18  

---

## 1. Executive Summary

Evaluation integrity in Project Kestrel Prototype 1 requires distinguishing genuine model reasoning from memorization of web-crawled evaluation benchmarks. Contemporary small language models (B-LLM candidates such as Qwen 2.5, LLaMA 3, Mistral, and Gemma 2) and frontier reference models ($F$, Gemini 2.5 Pro) have ingest pipelines that crawl major portions of the open internet, leading to pervasive contamination on standard academic benchmarks.

To protect against contaminated signals, Project Kestrel enforces:
1. **Source Provenance & Licensing Verification**: All public data sources are audited for permissible licenses and explicit contamination risk.
2. **Dual-Track Evaluation Suite (Public vs Synthetic)**: Every task group contains both public benchmark items and fresh, procedurally generated synthetic items.
3. **Mandatory Reporting Separation**: All evaluation tables must report accuracy on public benchmarks ($\text{Acc}_{\text{public}}$) and privately generated synthetic items ($\text{Acc}_{\text{synthetic}}$) separately, along with the gap ($\Delta = \text{Acc}_{\text{public}} - \text{Acc}_{\text{synthetic}}$).
4. **Physical Quarantine of Locked Test Items**: Locked test partition items are physically stored outside the repository in `kestrel_private/` and are evaluated strictly once at Step 10.

---

## 2. Public Source Provenance & Contamination Audit

The following table documents every public benchmark source evaluated for Project Kestrel, its official license, its presence in pretraining corpora, and its contamination status.

| Group | Source Dataset | Version | Canonical URL | Official License | Official License URL | Verified | Pretraining Crawl Presence | Contamination Risk Level |
| :--- | :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: |
| **Math** | GSM8K | 1.0 | `https://github.com/openai/grade-school-math` | MIT | [`LICENSE`](https://github.com/openai/grade-school-math/blob/master/LICENSE) | Yes | Pervasive in web crawls (Common Crawl, FineWeb, RedPajama); widely used in SFT/RLHF recipes | **HIGH** |
| **Science MCQ** | ARC-Challenge | 1.0 | `https://allenai.org/data/arc` | CC BY-SA 4.0 | [`CC BY-SA 4.0`](https://creativecommons.org/licenses/by-sa/4.0/) | Yes | Broadly crawled in public academic text; standard LLM leaderboard benchmark | **HIGH** |
| **Knowledge MCQ** | MMLU | 1.0 | `https://github.com/hendrycks/test` | MIT | [`LICENSE`](https://github.com/hendrycks/test/blob/master/LICENSE) | Yes | Universal LLM evaluation benchmark; test sets frequently leaked into instruction mixtures | **EXTREME** |
| **Code** | HumanEval | 1.0 | `https://github.com/openai/human-eval` | MIT | [`LICENSE`](https://github.com/openai/human-eval/blob/master/LICENSE) | Yes | Pervasive across all code LLMs trained since 2021; widespread verbatim memorization | **EXTREME** |
| **Code** | MBPP | 1.0 | `https://github.com/google-research/google-research/tree/master/mbpp` | CC BY 4.0 | [`CC BY 4.0`](https://creativecommons.org/licenses/by-dev/master/mbpp) | Yes | Present in GitHub crawls and public coding instruction mixtures | **HIGH** |
| **Knowledge QA** | Wikimedia Dumps (English) | 20261101 | `https://dumps.wikimedia.org/enwiki/20261101/` | CC BY-SA 3.0 / CC BY-SA 4.0 | [`Legal Information`](https://wikimediafoundation.org/wiki/Terms_of_Use) | Yes | Wikipedia text is in pretraining data; however, snapshot date (Nov 2026) and rule-extracted QA require span-grounded reading | **LOW / MITIGATED** |

---

## 3. Synthetic & Privately Generated Groups (Zero-Contamination Design)

To ensure Kestrel Prototype 1 measures genuine task performance rather than memorization, 100% of the locked-test partition and the core validation partition are backed by procedural synthetic generators that produce fresh, unseen problems:

### A. Math Word Problems (`evaluation/generators/math_generator.py`)
- **Design**: Parameterized generator using randomized numerical coefficients, randomized context entities (students, businesses, science labs), and randomized story templates (multi-step retail shopping, geometric perimeter/area, work rates, speed/distance/time, tournament scoring).
- **Ground Truth**: Exact algebraic derivation executed deterministically at generation time.
- **Contamination Risk**: **ZERO**. Problem statements are generated from high-cardinality combinatorial spaces ($>10^7$ variations).

### B. Science MCQ (`evaluation/generators/science_mcq_generator.py`)
- **Design**: Procedural multiple-choice generator spanning physics, chemistry, biology, and astronomy.
- **Distractor Permutation**: Correct answers and 3 plausible distractors are deterministically generated and shuffled per seed.
- **Contamination Risk**: **ZERO**. Templates are procedurally varied with seeded numeric and entity parameters.

### C. Knowledge MCQ (`evaluation/generators/knowledge_mcq_generator.py`)
- **Design**: Parameterized generators spanning 10 collegiate and professional subjects:
  1. `college_biology` (Hardy-Weinberg allele frequencies, DNA base percentages, organelle ATP yields)
  2. `college_computer_science` (Asymptotic Big-O complexities, data structure operations, graph traversal)
  3. `college_physics` (Kinematic equations, work-energy theorem, Snell's law, circuit resistance)
  4. `econometrics` (OLS assumptions, Gauss-Markov theorem, Durbin-Watson tests, $R^2$ interpretations)
  5. `high_school_chemistry` (Stoichiometry, periodic trends, acid-base pH, gas laws)
  6. `high_school_geography` (Sovereign capitals, major mountain elevations, Köppen climates, river lengths)
  7. `high_school_macroeconomics` (Fiscal/monetary policy, GDP deflator, Phillips curve, reserve ratios)
  8. `high_school_world_history` (Treaties, conflict chronologies, ancient civilizations, major empires)
  9. `machine_learning` (Optimization algorithms, regularizers, cross-entropy loss, bias-variance tradeoff)
  10. `professional_law` (Contract consideration, UCC rules, tort duty of care, Fourth Amendment standards)
- **Contamination Risk**: **ZERO**. Combinatorial parameter variations ensure prompts do not duplicate public MMLU questions.

### D. Code Tasks (`evaluation/generators/code_generator.py`)
- **Design**: Procedural function generation with parameter $k$ and varied algorithmic requirements (sliding window, frequency ranking, matrix manipulation, sequence filtering).
- **Verification**: Each generated function is executed in a self-verification sandbox against deterministic test suites before inclusion.
- **Contamination Risk**: **ZERO**. Problem statements and signatures are fresh and not found in HumanEval/MBPP.

### E. Knowledge QA (`evaluation/generators/knowledge_qa_generator.py`)
- **Design**: Deterministic rule-based extraction from 5,000 abstracts of the pinned Wikimedia snapshot (`20261101-pages-articles1.xml-p1p41242.bz2`, SHA-256 `e3fd5a83...`).
- **Grounding**: Every question requires identifying an exact answer substring ($`passage[start:end] == target`$) in the provided passage across 10 grammatical rule families (`birth_year`, `death_year`, `birth_place`, `profession`, `capital`, `elevation`, `discovery`, `founder`, `headquarters`, `alma_mater`).
- **Contamination Risk**: **MITIGATED**. Because the passage is explicitly provided in the prompt, performance measures reading comprehension and span extraction, not parametric memorization.

### F. Personal Memory Probe (`evaluation/generators/memory_probe_generator.py`)
- **Design**: Procedural timestamped personal event streams generated across multiple communication channels (`email`, `chat`, `calendar`, `health_log`, `notes`).
- **Stale Facts**: 30% of items feature temporal updates where an old fact is superseded by a newer fact.
- **Gate G-M Enforcement**: Scorer explicitly rejects stale/deprecated values.
- **Contamination Risk**: **ZERO**. Synthetic personal histories; no real personal data committed per `rules.md`.

---

## 4. Mandatory Evaluation Reporting Protocol

When reporting results for Step 2 (Baselines), Step 5 (Retrieval Augmentation), Step 9 (Memory Consolidation), and Step 10 (Locked Final Run), the following reporting rules must be strictly followed:

### 1. Separate Public vs Synthetic Accuracies
Every evaluation summary table must report:
- $\text{Acc}_{\text{public}}$: Mean accuracy across public benchmark splits (e.g., public GSM8K, ARC, MMLU).
- $\text{Acc}_{\text{synthetic}}$: Mean accuracy across synthetic/privately written tasks (`math`, `science_mcq`, `knowledge_mcq`, `code`, `knowledge_qa`, `memory_probe`).
- $\Delta_{\text{contam}} = \text{Acc}_{\text{public}} - \text{Acc}_{\text{synthetic}}$.

### 2. Interpretation Criteria
- **Normal Generalization**: $\Delta_{\text{contam}} \in [-5\text{ pp}, +5\text{ pp}]$. Model exhibits consistent reasoning across public and novel tasks.
- **Contamination Warning**: $\Delta_{\text{contam}} > +10\text{ pp}$. Indicates that public benchmark performance is significantly inflated by pretraining memorization rather than generalized reasoning.
- **Ground-Truth Gate Enforcement**: All Kestrel pass/kill gates (G-Q, G-F, G-M, G-R) are evaluated against the canonical suite (validation and locked-test), ensuring decisions are based on uncontaminated signals.

---

## 5. Partition Verification Summary

| Partition | Storage Location | Size | SHA-256 Hash Status | Access Rule |
| :--- | :--- | :---: | :--- | :--- |
| **Validation Suite v0** | `suite/validation/` (in-repo) | 1,200 | Frozen & checked in `suite/README.md` | Free access for Member B & A development |
| **Train Split** | `suite/train/` (in-repo) | 1,200 | Frozen & tracked in repo | Used for verifier training & SFT |
| **Locked-Test Partition** | `kestrel_private/locked_test/` (out-of-repo) | 1,200 | Root hash `22fff5e0...` frozen in `manifest.yaml` | **QUARANTINED**. Executed exactly once at Step 10. |
