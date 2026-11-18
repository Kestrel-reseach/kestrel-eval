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

## Pending Decision

- **D12 (Step 10 Locked-Test F Run Policy & Free-Tier Exposure Safeguards)**:
  > *PENDING OWNER WRITTEN CONFIRMATION: whether the Step 10 locked-test F run uses the Google AI Studio free tier (where content may be used for product improvement) or a paid tier.*
  - **Consequences & Safeguards to Record**:
    1. **Exposure**: Any locked item sent to F on the free tier at Step 10 is exposed to Google and may enter future training corpora.
    2. **One-Time Use**: The locked test partition is strictly one-time use for evaluation claims; it cannot be reused for new claims after exposure.
    3. **Reserve Test Set**: A reserve test set will be constructed later, written after Step 10 and never sent to any external API.
    4. **Minimal Send**: At Step 10, send F only what it strictly needs to be scored on.
    5. **Credits / Paid Tier Exploration**: Co-owners will explore startup cloud credits for a zero-data-retention paid tier prior to Step 10. If unavailable, free-tier execution proceeds under the one-time-use constraint.

