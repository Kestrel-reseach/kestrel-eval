# Proposal: Burn-and-Replace for Knowledge QA Locked Items

**Document:** `docs/decisions/burn_and_replace_proposal.md`  
**Date:** 2026-11-18  
**Status:** PROPOSED (Pending Co-Owner Review; Do NOT Execute)  
**Author:** Member A (Evaluation & Measurement Lead)  

---

## 1. Incident Summary

During PR 3 (Knowledge QA from Wikipedia snapshot), a human review sample was generated per the prompt instruction ("Write 50 random items per partition to a file for human review"). This resulted in 50 items from the `locked_test` partition being formatted into markdown and committed to `reports/step1_knowledge_qa_samples.md` in commit `6ec22c2`.

Per Decision D12, locked test items were authorized to be exposed only to Google AI Studio at Step 10 for reference evaluation under strict one-time use safeguards. Exposure on a public GitHub repository breaches the physical quarantine of those 50 items.

---

## 2. Immediate Containment Actions Taken

1. **File Removal**: `reports/step1_knowledge_qa_samples.md` has been removed via `git rm` in branch `step-1-closing-pass`.
2. **Review Generation Isolated**: `scripts/generate_kqa_samples.py` was refactored to sample exclusively from the `validation` partition (`reports/step1_knowledge_qa_validation_samples.md`).
3. **Repository Cleanliness Verified**: Automated leak checking (`scripts/check_locked_leak.py`) confirmed that **zero tracked files** in the repository now contain any locked item IDs.
4. **No History Rewriting**: Per `rules.md` and project non-negotiables, git history was not rewritten and force-pushes remain forbidden.

---

## 3. List of Affected Locked Items (50 Items)

The 50 affected items in the locked-test partition of Knowledge QA are the 50 items drawn by the PRNG sampler (indices 12, 18, 28, 38, 39, 43, 50, 53, 56, 77, 81, 90, 101, 102, 103, 111, 112, 114, 118, 129, 145, 148, 154, 157, 158, 161, 171, 174, 177, 194, 199, 200, 207, 216, 217, 219, 224, 240, 242, 243, 248, 250, 258, 260, 261, 264, 278, 291, 292, 293 out of 300).

SHA-256 digest of sorted affected IDs:
`c61ba7a840e53a35b0e5ee0dcf3f222ca3891ca118835061619934fc9b311310`

*(Zero locked item identifiers, prompts, or answers appear in this repository file.)*

---

## 4. Burn-and-Replace Proposal Options for Co-Owners

The pinned English Wikipedia abstract corpus contains 6,000 articles, of which only ~900 were utilized across all three splits. There is abundant clean headroom to replace the compromised items.

### Option A: Regenerate All 300 Locked Knowledge QA Items (Recommended)
- **Method**: Run the procedural generator for the locked partition with a new PRNG seed offset (e.g., `seed = base_seed + 140`) to draw 300 fresh items from unselected abstracts.
- **Impact**:
  - Validation (300 items) and Train (300 items) remain 100% identical and undisturbed.
  - The other 5 groups (`math`, `science_mcq`, `knowledge_mcq`, `code`, `memory_probe`) remain 100% undisturbed.
  - Updates the `knowledge_qa` hash and root hash in `evaluation/manifest.yaml`.
  - Manifest version bumped from v1.1 to v1.2 with an explicit owner decision commit.
- **Advantage**: Clean, deterministic, completely restores full zero-exposure integrity to the locked test partition.

### Option B: Replace Only the 50 Affected Items
- **Method**: Keep the 250 unexposed locked items and swap in 50 fresh items generated from unused corpus abstracts.
- **Impact**: Requires non-contiguous index management; updates the partition hash and manifest to v1.2.

---

## 5. Required Owner Action

Do not execute either option until co-owners review this proposal and confirm via an explicit approval prompt (e.g., "APPROVED: EXECUTE BURN-AND-REPLACE OPTION A").
