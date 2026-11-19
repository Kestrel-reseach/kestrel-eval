# Project Kestrel — Benchmark Contamination Analysis & Protocol Note

> [!CAUTION]
> **CORRECTION (2026-11-19 / Decision D14)**:
> In Suite v1, `math`, `code`, `science_mcq`, and `knowledge_mcq` partitions were constructed using 100% procedural synthetic generators (`math_generator.py`, `code_generator.py`, `science_mcq_generator.py`, `knowledge_mcq_generator.py`). No public benchmark items from GSM8K, ARC-Challenge, MMLU, HumanEval, or MBPP were included in Suite v1. The public sources below describe the reference benchmarks that are being downloaded into `data/raw/` to construct the separate public arms for Suite v2.0.

**Document:** `reports/CONTAMINATION.md`  
**Also Referenced As:** `reports/step1_contamination_note.md`  
**Step:** Step 1 (Suite v0, Contamination & Validation Handoff)  
**Author:** Member A (Evaluation, Measurement & Memory Lead)  
**Skill Reference:** `suite-split-hash`  
**Date:** 2026-11-18 (Updated 2026-11-19)  

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

## 3. Suite v2.0 Dual-Arm Architecture (Public vs. Synthetic Reference)

Per Owner Decision D14 (Option B), Suite v2.0 establishes clean, separate arms:

### A. Math Word Problems (`math`, N=200/split)
- **Public Arm (N=100)**: Real GSM8K test problems (Cobbe et al., 2021). Evaluated for public academic comparability. High pretraining contamination risk.
- **Synthetic Arm (N=100)**: 16 procedural template families with combinatorial parameters. Zero contamination reference.

### B. Science MCQ (`science_mcq`, N=200/split)
- **100% Public Arm (N=200)**: Genuine AI2 ARC-Challenge questions (Clark et al., 2018). Synthetic arm dropped after pre-registered A3 artifact audit revealed option-ordering leakage. High contamination risk.

### C. Knowledge MCQ (`knowledge_mcq`, N=300/split)
- **100% Public Arm (N=300)**: Genuine MMLU questions spanning 10 academic and professional disciplines (30 items/subject). Synthetic arm dropped after pre-registered A3 artifact audit revealed distractor leakage. Extreme contamination risk.

### D. Code Tasks (`code`, N=100/split)
- **Public Arm (N=50)**: Real MBPP problems (Austin et al., Google 2021). High contamination risk.
- **Synthetic Arm (N=50)**: 36 procedural algorithmic functions with sandboxed self-verifying test suites. Zero contamination reference.

### E. Knowledge QA (`knowledge_qa`, N=300/split)
- **Real Wikipedia Arm (N=200)**: Extraction from 5,000 Wikipedia abstracts (`20261101-pages-articles1.xml-p1p41242.bz2`). Capped family share ≤ 30%.
- **Fictional Entity Arm (N=100 / D13)**: Purely fictional personas and settlements with 0% Wikipedia collision. Guaranteed 0% parametric pretraining memorization, verified in 50-item pilot (0% no-retrieval vs. 84% retrieval accuracy).

### F. Personal Memory Probe (`memory_probe`, N=100/split)
- **100% Synthetic Arm (D3)**: Procedural timestamped personal event logs across 16 stale-fact categories and 20 static categories. Zero contamination reference.

---

## 4. Mandatory Evaluation Reporting Protocol

When reporting baseline candidate evaluations (Step 2 R4), retrieval augmentation (Step 5), and final runs:
1. **Report Public and Synthetic Arms Separately**:
   - $\text{Acc}_{\text{public}}$: Mean accuracy on public benchmark items.
   - $\text{Acc}_{\text{synthetic}}$: Mean accuracy on procedural synthetic and fictional items.
   - $\Delta_{\text{contam}} = \text{Acc}_{\text{public}} - \text{Acc}_{\text{synthetic}}$.
2. **Interpretation**:
   - $\Delta_{\text{contam}} > +10\text{ pp}$ indicates that public performance is inflated by pretraining memorization.
   - Synthetic and fictional arms provide the unbiased ground-truth evaluation of model reasoning and retrieval.

---

## 5. Partition Verification Summary (Suite v2.0)

| Partition | Storage Location | Size | SHA-256 Hash Status | Access Rule |
| :--- | :--- | :---: | :--- | :--- |
| **Validation Suite v2.0** | `suite/validation/` (in-repo) | 1,200 | Frozen in `suite/README.md` | Free access for Member B & A development |
| **Train Split** | `suite/train/` (in-repo) | 1,200 | Tracked in repo | Used for verifier training & SFT |
| **Locked-Test Partition** | `kestrel_private/locked_test/` (out-of-repo) | 1,200 | Root hash `39cbe48e...` frozen in `manifest.yaml` | **QUARANTINED**. Executed exactly once at Step 10. |
