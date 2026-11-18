# Knowledge QA Corpus & Span-Verified Factual Items (PR 3)

**Step**: Step 1 (PR 3 — Knowledge QA from Wikipedia Snapshot)  
**Branch**: `step-1-knowledge-qa`  
**Date**: 2026-11-18  

---

## 1. Pinned Corpus Snapshot (Decision D2)

Per Decision D2 (*"one dated English Wikipedia dump, URL + sha256, ~5k-article abstract subset"*), we pinned the foundational articles partition from the official English Wikipedia dump:

- **Corpus File**: `enwiki-20261101-pages-articles1.xml-p1p41242.bz2`
- **Official Dump URL**: `https://dumps.wikimedia.org/enwiki/20261101/enwiki-20261101-pages-articles1.xml-p1p41242.bz2`
- **File Size**: `300,158,691` bytes (286.25 MB)
- **Official Wikimedia MD5**: `0409fa36394b206b3f9940688e7b08ba` (Exact match with `enwiki-20261101-md5sums.txt`)
- **Official Wikimedia SHA-1**: `eda718207f2a9596f42745ee70433767bf3e1fb8` (Exact match with `enwiki-20261101-sha1sums.txt`)
- **Authoritative SHA-256**: `e3fd5a837f2a6b3a26c3596d0667600073a86c9fc29dc60ef0b2de605c754387`
- **Storage**: Local archive under `data/raw/` (gitignored per repository rules).

Both `docs/decisions/owner_decisions.md` and `evaluation/manifest.yaml` have been updated with these authoritative checksums and URLs.

---

## 2. Abstract Extraction Pipeline

Implemented in [`evaluation/generators/wiki_extractor.py`](file:///home/ash09/project_x/kestrel-eval/evaluation/generators/wiki_extractor.py):

1. **Streaming XML Processing**:
   - Uses `xml.etree.ElementTree.iterparse` over the bzip2 stream with `elem.clear()` for constant $O(1)$ memory overhead.
   - Filters strictly for Namespace 0 (encyclopedia articles), excluding redirects, disambiguation pages, list indices, and non-article meta pages.

2. **Wikitext Stripping**:
   - Strips XML/HTML comments (`<!-- ... -->`) and `<ref>...</ref>` citation tags.
   - Iteratively removes wikitables (`{| ... |}`) and templates (`{{ ... }}`).
   - Normalizes media links and internal wikilinks (`[[Target|Anchor]]` $\rightarrow$ `Anchor`).
   - Removes bold/italic markup (`'''`, `''`) and bullet markers.
   - Extracts clean lead introductory abstracts ending at clean sentence boundaries.

3. **Extracted Corpus**:
   - Extracted 6,000 clean article abstracts into `data/wikipedia_abstracts_5k.jsonl`.
   - Extraction completed in **24.01 seconds**.

---

## 3. Rule-Based QA Generation with 100% Span Verification

Implemented in [`evaluation/generators/knowledge_qa_generator.py`](file:///home/ash09/project_x/kestrel-eval/evaluation/generators/knowledge_qa_generator.py):

### Rule Families & Semantic Entity Alignment
To guarantee factual accuracy and avoid absurd questions (e.g. asking when a concept or country was born), rules enforce strict semantic entity alignment:

| Rule Family | Target Entity & Pattern | Example Question | Ground Truth Answer |
| :--- | :--- | :--- | :--- |
| `born_date` | Person biographical profile (`(born Date)`) | *"When was Constantin Brâncuși born?"* | `February 19, 1876` |
| `death_date` | Deceased biography (`(Birth Date – Death Date)`) | *"When did Antonio Vivaldi die?"* | `28 July 1741` |
| `profession` | Whitelisted occupation nouns from biographical leads | *"What was the profession or occupation of Claude Shannon?"* | `mathematician` |
| `founded_year` | Organizations, universities, companies (`founded in YYYY`) | *"In what year was Great Internet Mersenne Prime Search founded?"* | `1996` |
| `capital_city` | Sovereign states and territories (`capital of Territory`) | *"What territory or country is Brussels the capital of?"* | `Belgium` |
| `city_location` | Municipalities and cities (`is a city in Region`) | *"In which region or country is Cedar Falls, Iowa located?"* | `Black Hawk County` |
| `population` | Cities, islands, and regions (`population of Number`) | *"What was the reported population of Atlanta?"* | `498,715` |
| `surface_area` | Geographic entities (`area of Quantity`) | *"What is the surface area of Bahrain?"* | `780 sq km` |
| `award_won` | Recognized awards, medals, and prizes (`won the Award`) | *"What award or prize did Halle Berry receive?"* | `Academy Award` |
| `work_creator` | Novels, books, films, plays (`is a novel by Author`) | *"Who created or wrote Nineteen Eighty-Four?"* | `George Orwell` |
| `release_year` | Creative works (`is a YYYY film/album`) | *"In what year was Blade Runner released or published?"* | `1982` |

### Strict Span Checking Invariant
For every generated QA item:
$$\text{passage}[\text{span}[0] : \text{span}[1]] \equiv \text{answer}$$
- Every answer substring is guaranteed to be present at its exact character offset.
- Answers are verified to not appear inside the prompt question.
- No external LLMs (neither F nor candidate models) were used in question generation or filtering.

---

## 4. Partition Slicing & Review Samples

- **Partition Slicing**:
  - `validation`: 300 items (`kqa_val_0001` through `kqa_val_0300`)
  - `locked_test`: 300 items (stored privately out of repository in `kestrel_private/`; hash recorded in `manifest.yaml`)
  - `train`: 300 items (`kqa_train_0001` through `kqa_train_0300`)
- **Human Review Document**:
  - 50 randomly sampled items from the `validation` partition have been written to `reports/step1_knowledge_qa_validation_samples.md` for human inspection.
