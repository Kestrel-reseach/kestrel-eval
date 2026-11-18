# Decision Record: Target Hardware Tier and Alternate Test Hardware

**Date**: 2026-11-18  
**Status**: `PENDING OWNER CONFIRMATION in writing (PR or issue comment)` *(Not final)*  
**Source / Provenance**: Agent-drafted on branch `update-plan-step0-step3-results`, reviewed and merged by Member B (`@sreevarshan-xenoz`) in PR #7 (`kestrel-eval`) and PR #6 (`kestrel`). **No owner-written record exists.**

---

## 1. Background & Hardware Context

The authoritative Prototype 1 specification (`PLAN.md`) defines the following target hardware tiers:
- **Target GPU Tier**: NVIDIA GeForce RTX 3060 Laptop (6 GB VRAM, 192-bit bus, ~60–80 W TGP tier).
- **Target CPU Tier**: AMD Ryzen 7 5800H (8 cores / 16 threads, Zen 3).

On 2026-11-18, during local test execution by Member A, the target RTX 3060 / Ryzen 5800H laptop was unavailable. The local execution host was identified as:
- **Test GPU Tier**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM, 128-bit bus, 35–60 W dynamic TGP tier, UUID `REDACTED`).
- **Test CPU Tier**: AMD Ryzen 7 7435HS (8 cores / 16 threads, Zen 3+ without integrated Radeon graphics).

---

## 2. Disclosure of Acceptance Provenance

- **Provenance**: The text recording acceptance of the RTX 3050 Laptop 4 GB as an alternate test tier was drafted by an autonomous agent on branch `update-plan-step0-step3-results` based on conversational discussion from Member A.
- **Merge Action**: Member B (`@sreevarshan-xenoz`) reviewed and squash-merged the text into `main` via PR #7 in `kestrel-eval` (commit `07979e5`) and PR #6 in `kestrel` (commit `a785411`).
- **Owner Record**: There is **no written record, PR comment, or commit authored by the project owner himself** confirming this hardware tier change.
- **Current Status**: Marked as `PENDING OWNER CONFIRMATION` (Decision D8) until confirmed in writing by the project owner.

---

## 3. Non-Transferability of Results

> [!WARNING]
> **Results obtained on the NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM) are NOT transferable to the RTX 3060 tier.**

1. **VRAM Constraints**:
   - The RTX 3050 has 4,096 MiB VRAM total.
   - The assistant budget is fixed at 1.0–1.5 GB resident VRAM. On a 4 GB card, remaining VRAM for display, OS desktop, and context memory is tighter than on a 6 GB card.
2. **Power & Thermal Differences**:
   - The RTX 3050 operates in a 35–60 W dynamic TGP envelope, whereas the RTX 3060 operates in a 60–80 W+ envelope.
   - Energy per task, clock scaling, and thermal throttling behaviors differ substantially between these silicon dies (GA107 vs GA106).
3. **Formal Verification Policy**:
   - Measurements collected on the RTX 3050 test tier must be explicitly labeled as produced by the `RTX 3050 Laptop GPU (4 GB) test tier`.
   - Gate G-R thresholds (1–1.5 GB resident VRAM) remain frozen and unmodified.
   - Formal target-tier verification for Prototype 1 requires re-running on the official RTX 3060 hardware once accessible.
