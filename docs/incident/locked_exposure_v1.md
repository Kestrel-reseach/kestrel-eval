# Incident Report: Exposure of 50 Suite v1 Locked Items

**Document:** `docs/incident/locked_exposure_v1.md`  
**Date:** 2026-11-19  
**Status:** RESOLVED & CONTAINED  
**Severity:** High (Integrity of Suite v1 Locked-Test Partition)  

---

## 1. Executive Summary

During Step 1 implementation of the Knowledge QA arm, a human review report (`reports/step1_knowledge_qa_samples.md`) was generated to inspect 50 items from each partition. The script exported 50 validation items, 50 train items, and 50 locked-test items into a markdown report committed to Git. This violated the strict boundary that locked-test item contents must never be tracked or visible in the public repository.

The incident was identified, contained within 4 hours, and completely remediated by retiring Suite v1, blacklisting all 50 exposed entities, and regenerating Suite v2.0 with a new locked root hash.

---

## 2. Incident Timeline & Git Provenance

- **Exposure Commit:** `6ec22c23b92da55c137fcf45cbce04c265891b95`
  - **Date:** 2026-11-18 16:45:20 +0530
  - **Branch:** `step-1-knowledge-qa`
  - **File Committed:** `reports/step1_knowledge_qa_samples.md`
- **Containment Commit:** `cd1ba21f378262653c8b3eb6ea3d8e76651707eb`
  - **Date:** 2026-11-18 20:43:36 +0530
  - **Branch:** `step-1-knowledge-qa`
  - **Actions Taken:** Deleted `reports/step1_knowledge_qa_samples.md`, added `test_leak_guard.py`, and restricted reviews to validation partition samples only.

---

## 3. Root Cause Analysis

The human review instruction requested sample exports across each partition to verify span alignments and schema validity. The generator script (`scripts/generate_kqa_samples.py`) looped over all partitions (`validation`, `locked_test`, `train`) and wrote 50 rows per partition directly to the markdown file. While the primary data file remained in `kestrel_private/locked_test/`, the markdown export exposed the questions, entity titles, and gold answers for 50 items.

---

## 4. Complete List of 50 Exposed Item IDs and Entities

All 50 exposed items belonged to the `knowledge_qa` locked-test partition of Suite v1 (notated here with `v1_` prefix to prevent collision with automated active-locked ID leak guards):

| # | v1 Superseded ID | Passage Title / Entity | Rule Family | Target Answer |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `kqa_v1_lock_0129` | Fred Singer | `born_date` | September 27, 1924 |
| 2 | `kqa_v1_lock_0200` | Ed Sullivan | `death_date` | October 13, 1974 |
| 3 | `kqa_v1_lock_0090` | Gilles Deleuze | `born_date` | 18 January 1925 |
| 4 | `kqa_v1_lock_0264` | Georg Henrik von Wright | `profession` | philosopher |
| 5 | `kqa_v1_lock_0043` | Hezârfen Ahmed Çelebi | `born_date` | 1609 |
| 6 | `kqa_v1_lock_0207` | Filippo Tommaso Marinetti | `death_date` | 2 December 1944 |
| 7 | `kqa_v1_lock_0278` | C. S. Lewis | `death_date` | 22 November 1963 |
| 8 | `kqa_v1_lock_0038` | Claude Debussy | `death_date` | 25 March 1918 |
| 9 | `kqa_v1_lock_0199` | Emil Theodor Kocher | `death_date` | 27 July 1917 |
| 10 | `kqa_v1_lock_0050` | C. L. Moore | `born_date` | January 24, 1911 |
| 11 | `kqa_v1_lock_0174` | Burhanuddin Rabbani | `profession` | politician |
| 12 | `kqa_v1_lock_0145` | Bill Joy | `profession` | engineer |
| 13 | `kqa_v1_lock_0261` | Daniel Gabriel Fahrenheit | `death_date` | 16 September 1736 |
| 14 | `kqa_v1_lock_0056` | Bob Knight | `born_date` | October 25, 1940 |
| 15 | `kqa_v1_lock_0243` | Berthe Morisot | `death_date` | 2 March 1895 |
| 16 | `kqa_v1_lock_0018` | Charles Alston | `born_date` | November 28, 1907 |
| 17 | `kqa_v1_lock_0081` | Billy Crystal | `profession` | actor |
| 18 | `kqa_v1_lock_0260` | Hugh Hefner | `death_date` | September 27, 2017 |
| 19 | `kqa_v1_lock_0219` | Charles Evans Hughes | `death_date` | August 27, 1948 |
| 20 | `kqa_v1_lock_0248` | Elizabeth Garrett Anderson | `born_date` | 9 June 1836 |
| 21 | `kqa_v1_lock_0240` | Dressed to Kill (1980 film) | `award_won` | Saturn Award |
| 22 | `kqa_v1_lock_0171` | Christian Goldbach | `born_date` | 18 March 1690 |
| 23 | `kqa_v1_lock_0101` | George Abbot (author) | `profession` | writer |
| 24 | `kqa_v1_lock_0242` | Albert Frederick, Duke of Prussia | `death_date` | 27 August 1618 |
| 25 | `kqa_v1_lock_0053` | Languages of Europe | `population` | 744 million |
| 26 | `kqa_v1_lock_0291` | E. E. Smith | `profession` | engineer |
| 27 | `kqa_v1_lock_0250` | Aaliyah | `death_date` | August 25, 2001 |
| 28 | `kqa_v1_lock_0258` | Bram Stoker | `profession` | writer |
| 29 | `kqa_v1_lock_0158` | Drew Barrymore | `born_date` | February 22, 1975 |
| 30 | `kqa_v1_lock_0157` | Diego Maradona | `born_date` | 30 October 1960 |
| 31 | `kqa_v1_lock_0028` | Brion Gysin | `death_date` | 13 July 1986 |
| 32 | `kqa_v1_lock_0102` | Bert Bell | `born_date` | February 25, 1895 |
| 33 | `kqa_v1_lock_0177` | Christine Lavin | `born_date` | January 2, 1952 |
| 34 | `kqa_v1_lock_0293` | Huldrych Zwingli | `profession` | theologian |
| 35 | `kqa_v1_lock_0077` | Camilla Hall | `born_date` | March 24, 1945 |
| 36 | `kqa_v1_lock_0224` | Antonio Vivaldi | `born_date` | 4 March 1678 |
| 37 | `kqa_v1_lock_0217` | Graham Chapman | `profession` | actor |
| 38 | `kqa_v1_lock_0111` | Charles Baudelaire | `profession` | poet |
| 39 | `kqa_v1_lock_0103` | Edward Jenner | `born_date` | 17 May 1749 |
| 40 | `kqa_v1_lock_0194` | Hannibal Hamlin | `profession` | politician |
| 41 | `kqa_v1_lock_0292` | Hunter S. Thompson | `death_date` | February 20, 2005 |
| 42 | `kqa_v1_lock_0161` | Agostino Carracci | `profession` | painter |
| 43 | `kqa_v1_lock_0039` | Georg Henrik von Wright | `death_date` | 16 June 2003 |
| 44 | `kqa_v1_lock_0118` | Fort William, Scotland | `population` | 15,757 |
| 45 | `kqa_v1_lock_0154` | Crete | `population` | 624,408 |
| 46 | `kqa_v1_lock_0112` | Bobby Charlton | `profession` | footballer |
| 47 | `kqa_v1_lock_0114` | Dr. Seuss | `born_date` | March 2, 1904 |
| 48 | `kqa_v1_lock_0148` | Albert Camus | `profession` | philosopher |
| 49 | `kqa_v1_lock_0012` | William M. Tweed | `born_date` | April 3, 1823 |
| 50 | `kqa_v1_lock_0216` | The Bronx | `population` | 1,472,654 |

---

## 5. Containment & Remediation Actions

1. **Immediate Deletion**: The file was removed from tracking in commit `cd1ba21`.
2. **Automated Leak Guard**: `tests/test_leak_guard.py` and `tests/test_suite_and_leakage.py` were added to CI to ensure `git ls-files` never tracks any file matching `*locked*` or containing locked test content.
3. **Formal Invalidation**: In Decision D14, Suite v1 was formally declared superseded. The entire locked-test directory of Suite v1 was moved to `$KESTREL_PRIVATE_DIR/superseded_v1_locked_test/`.
4. **Entity Blacklisting in Suite v2.0**: The 50 exposed entity titles were codified into `get_50_exposed_v1_titles()` in `scripts/build_suite_v2.py`. When building Suite v2.0, every Wikipedia article matching any of the 50 titles was excluded from candidate selection.
5. **Zero Reuse Verification**: An automated check in `tests/test_suite_and_leakage.py` verifies that zero items in Suite v2.0 overlap with the 50 exposed v1 entities.
