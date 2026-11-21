# Project Kestrel — Co-Owner Decisions Log (D1–D11)

**Source**: Formal decisions resolved by the project co-owners (Member A and Member B).  
**Repository Evidence**: Committed and merged in `kestrel-eval` PR #8 (commit `f261bae`) and `kestrel` PR #7 (commit `4ed0afa`).  
**Status**: D1–D11 are **FROZEN & AUTHORITATIVE**. D12 is **PENDING OWNER DECISION**.

---

## Verbatim Co-Owner Decisions

- **D1 (Suite Sizes & Partitions)**:
  > "sizes are LOCKED-TEST sizes 200/200/300/100/300/100; validation same size; train from public train splits + synthetic"
  - math: 200 items
  - science_mcq: 200 items
  - knowledge_mcq: 300 items
  - code: 100 items
  - knowledge_qa: 300 items
  - memory_probe: 100 items (30 stale-fact items)
  - `sizes_are: per_partition` (1,200 items per partition, 3,600 total across train/val/locked-test). The old 60/20/20 fractions do not apply (`partition_fractions: null`).

- **D2 (Knowledge-QA Corpus)**:
  > "one dated English Wikipedia dump, URL + sha256, ~5k-article abstract subset"
  - Fixed public corpus backing the knowledge store.
  - **Pinned Dump URL**: `https://dumps.wikimedia.org/enwiki/20261101/enwiki-20261101-pages-articles1.xml-p1p41242.bz2`
  - **Date**: 2026-11-01 (English Wikipedia foundational articles partition, pages 1 to 41,242)
  - **File Size**: 300,158,691 bytes (286.25 MB)
  - **Official Wikimedia MD5**: `0409fa36394b206b3f9940688e7b08ba`
  - **Official Wikimedia SHA-1**: `eda718207f2a9596f42745ee70433767bf3e1fb8`
  - **Authoritative SHA-256 Checksum**: `e3fd5a837f2a6b3a26c3596d0667600073a86c9fc29dc60ef0b2de605c754387`

- **D3 (Personal Data in Memory Probe)**:
  > "synthetic histories only"
  - No real personal data is committed or transmitted.

- **D4 (Pass Gates & Non-Inferiority Margin)**:
  > "gates frozen as proposed, non-inferiority margin 3 points"
  - G-Q, G-F, G-M, G-R and no-regression frozen as proposed.
  - The non-inferiority margin for the "equal accuracy" clause is 3 percentage points (same as no-regression). Report bootstrap confidence intervals.

- **D5 (Context Length)**:
  > "context 2048"
  - Fixed context window length of 2,048 tokens for all evaluations and VRAM budget verification on the test tier.

- **D6 (Frontier Reference Model F)**:
  > "F = Gemini 2.5 Pro, Google AI Studio free tier, $0 cap, paced across days, record exact model version and date, G-F labelled 'gap to a free-tier reference'"
  - Model: `gemini-2.5-pro` accessed via Google AI Studio free tier.
  - Cost cap: $0 (no paid calls).
  - Paced across days to respect unpublished free-tier rate limits.
  - Mandatory label on every F table: *"F = gemini-2.5-pro (free tier), exact version and date recorded; a free-tier reference, not the current frontier."*

- **D7 (CPU & GPU Energy Scope)**:
  > "CPU energy UNMEASURED, GPU-only relative energy"
  - CPU energy is unmeasured (RAPL is root-only mode `0400`).
  - Energy is measured strictly via NVIDIA NVML on the GPU and reported as relative energy with mandatory labeling.

- **D8 (Measurement Hardware & Wall Meter)**:
  > "no wall meter; RTX 3050 4GB / Ryzen 7435HS official tier"
  - No physical wall meter; kill-gate relative energy applies.
  - AMD Ryzen 7 7435HS + NVIDIA GeForce RTX 3050 Laptop GPU (4 GB) is the official test tier for Prototype 1.

- **D9 (API Key Security)**:
  > "key in env var GEMINI_API_KEY"
  - Read from environment variable `GEMINI_API_KEY` only. Never logged, printed, or committed to repository files.

- **D10 (Frontier Model F Evaluation Scope)**:
  > "F once on public + synthetic only"
  - F is evaluated once on public and synthetic validation items; memory probe twice (no-history and full-history).

- **D11 (F Call Provenance Logging)**:
  > "record model version, date and response IDs with every F record"
  - All F API responses log model version string, execution date, and response IDs.

---

## Formal Decisions Log Continued (D12–D14)

- **D12 (Step 10 Locked-Test F Run Policy & Free-Tier Exposure Safeguards)**:
  > *Resolved: Step 10 locked-test F run uses Google AI Studio free tier under one-time-use constraint; reserve test set constructed later.*
  - **Exposure**: Any locked item sent to F on the free tier at Step 10 is exposed to Google and may enter future training corpora.
  - **One-Time Use**: The locked test partition is strictly one-time use for evaluation claims; it cannot be reused for new claims after exposure.
  - **Reserve Test Set**: A reserve test set will be constructed later, written after Step 10 and never sent to any external API.
  - **Minimal Send**: At Step 10, send F only what it strictly needs to be scored on.

- **D13 (Co-Owners A and B, 2026-11-19)**:
  > "The fictional-entity knowledge QA arm is scored as a separate diagnostic arm and never pooled into headline numbers."

- **D14 (Owners A and B, 2026-11-19)**:
  > "Rebuild the suite as Suite v2.0, option B (public + synthetic arms, reported separately). Synthetic science/knowledge MCQ arms are kept ONLY if the artifact audit passes; otherwise those two groups are public-only. Knowledge QA gets a fictional-entity arm (D13). All locked items are replaced with new seeds (the 50 exposed items are never reused). Manifest v2.0. Verifier hold-out is by template family or whole group. F runs only after the suite is frozen and the prompt templates are final."

  - **Settled Operational Defaults for Suite v2.0**:
    1. **Public Dataset Licensing**: Accept public datasets (GSM8K, ARC-Challenge, MMLU, HumanEval, MBPP) as verified permissible from official repository and license pages.
    2. **Train Partition Size for Member B Verifier**: At least 3× the validation size for checkable groups, drawn from official public train splits.
    3. **Knowledge QA Real Family Share Cap**: Maximum share for any single real-entity question family is capped at 30%.
    4. **Frontier Reference Model F Tier**: Stays on Google AI Studio free tier ($0 cost cap, paced execution).

- **D15 (Co-Owners A and B, 2026-11-19)**:
  > "The +10 point retrieval gate (Gate G-Q) is evaluated on the real Wikipedia arm; the fictional arm only shows that retrieval works without parametric pretraining memorization."

- **D16 (Co-Owners A and B, 2026-11-19)**:
  > "G-M power: expand the memory probe to 150 items per partition (100 stale + 50 static across at least 15 categories) and use a paired analysis (McNemar / paired bootstrap) against plain external memory."

- **D17 (Co-Owners A and B, 2026-11-19)**:
  > "Regenerate all locked synthetic, fictional, and public-slice selections under a private CSPRNG seed and salt stored in $KESTREL_PRIVATE_DIR/locked_seed.env (mode 0600), with new fictional entities and facts retiring all exposed entities from git history. Validation and train files remain unchanged. Only hashes are committed to the public repo."

- **D18 (Owners A and B, 2026-11-20)**:
  > "B-LLM = the most accurate candidate whose NVML process VRAM at 2048 context is at most 1,536 MB; ties broken by lower net energy per correct on the 800-item scope; final only after all candidates are run and the owners confirm."

- **D18 Owner Confirmation (Co-Owners A and B, 2026-11-21)**:
  > "Candidate evaluation under D18 and D19 is formally complete across all shortlisted candidates on the RTX 3050 Laptop GPU tier at 2048 context under 4-bit NF4. Measured NVML process VRAM confirms that SmolLM2-1.7B (1,732.0 MB) and Granite-4.0-1B (1,602.0 MB) exceed the 1,536 MB budget and are disqualified. Llama-3.2-1B-Instruct is gated and blocked without HF_TOKEN. Qwen3.5-0.8B fits VRAM (1,220.0 MB, 54.0% accuracy on 100 validation sample) but is dominated by Qwen2.5-1.5B and constrained by reference PyTorch kernel latency (~285 ms/token). Qwen/Qwen2.5-1.5B-Instruct (4-bit NF4) is confirmed as B-LLM (accuracy 56.88% on 800 checkable items, NVML VRAM 1,416.0 MB, net energy 171.55 J/correct). Gate baselines G-Q, G-M, and G-R in evaluation/manifest.yaml (v2.3) are confirmed and released to unblock Member B Step 3 verifier training."

- **D19 (Owners A and B, 2026-11-20)**:
  > "Option A candidates (five) stand; also try Qwen3.5-0.8B, time-boxed to one hour."

- **D20 (Owners A and B, 2026-11-20)**:
  > "F: free tier (Google AI Studio, $0 cap, paced across days; paid tier pending confirmation)."


