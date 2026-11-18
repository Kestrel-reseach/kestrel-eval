# Owner Decision Proposal D13: Knowledge-QA Ceiling & Counter-Contamination Design

**Document:** `docs/decisions/D13_proposal.md`  
**Date:** 2026-11-18  
**Status:** PROPOSED (For Co-Owner Review; Does NOT Alter Frozen Suite)  
**Author:** Member A (Evaluation & Measurement Lead)  

---

## 1. Problem Statement: The Retrieval Ceiling

In Project Kestrel Prototype 1, Gate G-Q / Step 5 requires demonstrating that SSD-backed retrieval augmentation improves question-answering accuracy by at least **+10 percentage points** over the closed-book baseline.

However, the current Knowledge QA group extracts facts from foundational English Wikipedia articles across 10 grammatical rule families. Small language models (1B to 7B parameters) have ingested large portions of Wikipedia during pretraining, creating a high risk that candidate models will answer questions from parametric memory alone.

If a small model already achieves 65–75% closed-book accuracy by memorization, achieving a +10 pp gain from retrieval is constrained by an artificial ceiling, potentially failing Gate G-Q despite functioning retrieval hardware.

---

## 2. Memorization Risk Audit Across 10 Question Families

| Rule Family | Target Fact Type | Example Question Pattern | Small LM Memorization Likelihood | Reason / Corpus Exposure |
| :--- | :--- | :--- | :---: | :--- |
| `profession` | Primary occupation of notable entity | *"What was the profession of [Entity]?"* | **VERY HIGH** (>85%) | High co-occurrence of famous names and occupations in pretraining text. |
| `capital_city` | Capital of territory/state | *"What territory is [City] the capital of?"* | **VERY HIGH** (>85%) | World capitals are pervasive in general language model trivia. |
| `born_date` | Exact birth date | *"When was [Person] born?"* | **HIGH** (~70%) | Biographical infoboxes are heavily represented in pretraining datasets. |
| `death_date` | Exact death date | *"When did [Person] die?"* | **HIGH** (~70%) | Frequently crawled historical data. |
| `award_won` | Prestigious prize or award | *"What award or prize did [Entity] receive?"* | **HIGH** (~65%) | Nobel, Pulitzer, Academy, and Hugo award lists are ubiquitous. |
| `work_creator` | Author/director of novel or film | *"Who created or wrote [Title]?"* | **HIGH** (~75%) | Prominent creative works and their authors are widely memorized. |
| `founded_year` | Founding year of organization | *"In what year was [Org] founded?"* | **MODERATE** (~50%) | Well-known universities/companies are memorized; minor entities are not. |
| `city_location`| Region/county of municipality | *"In which region is [City] located?"* | **MODERATE** (~45%) | Major metropolitan areas are memorized; county-level facts are rarely recalled. |
| `population` | Census population count | *"What was the reported population of [City]?"* | **LOW** (<25%) | Exact multi-digit figures are rarely stored accurately in parametric weights. |
| `surface_area` | Geographic surface area in sq km | *"What is the surface area of [Entity]?"* | **LOW** (<20%) | Exact numerical geographic dimensions are almost universally hallucinated. |

---

## 3. Proposal for Decision D13

To ensure that the +10 pp retrieval gate is testable and reflects genuine retrieval rather than memorization, we propose that the owners adopt one of the following two paths for future evaluation suites:

### Option 1: Diagnostic Fictional / Post-Cutoff Partition (Recommended for Step 5 Gate Verification)
- Construct a dedicated 100-item diagnostic split consisting of:
  - Procedurally generated synthetic articles and entities (e.g. fictional scientists, newly founded fictional labs, synthetic geographic territories) styled identically to Wikipedia abstracts.
  - Pinned recent 2026 events post-dating common LLM pretraining cutoffs.
- **Advantage**: Closed-book accuracy without retrieval is guaranteed to be near 0% ($\pm 3\%$). When retrieval is activated, accuracy jumps to 70–80%, cleanly and unambiguously verifying the +10 pp retrieval gate without contamination or ceiling effects.
- **Suite Impact**: Does not alter the frozen 3,600-item suite for standard reporting; operates as an explicit diagnostic partition for Gate G-Q.

### Option 2: Numerical & Low-Frequency Filtering
- Filter future Knowledge QA candidate items to prioritize `population`, `surface_area`, and obscure municipalities where closed-book accuracy is empirically measured $<30\%$.

---

## 4. Next Step for Owners

Review this analysis before baseline runs are finalized. This proposal is recorded for discussion and does not alter the frozen manifest or existing suite hashes.
