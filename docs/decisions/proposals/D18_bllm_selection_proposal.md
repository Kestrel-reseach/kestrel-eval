# Proposal: Candidate B-LLM Selection & Initial Gate Baselines (PROPOSED)

**Status**: **PROPOSED / PENDING OWNER CONFIRMATION**  
**Author**: Evaluation Harness (Member A)  
**Date**: 2026-11-20  
**Context**: Replaced by Owner Decisions D18–D20. This document preserves the initial 2-candidate Pareto proposal for auditability.

---

## Proposed Decision Text (Superceded / For Reference Only)

> "B-LLM is frozen as Qwen/Qwen2.5-1.5B-Instruct in bitsandbytes 4-bit NF4. Gate G-Q baseline on 800 checkable validation items is 58.38% (467/800, 95% CI [54.93, 61.74]%) at 120.40 Net Joules/correct; P1 target is >= 63.38% (+5.0 pp, paired bootstrap CI excludes 0) at <= 120.40 J/correct, or >= 55.38% at <= 60.20 J/correct (50% energy savings). Gate G-M baseline on 100 stale fact items is 22.00% stale error rate (22 errors); P1 target is <= 11.00% (at most 11 errors). Gate G-R baseline is 1,416.0 MB NVML process VRAM, fitting under the 1,536.0 MB (1.5 GB) resident GPU budget with 120.0 MB headroom."

---

## Owner Review Finding (2026-11-20)
The project co-owners rejected premature freezing of this decision:
1. **Candidate Scope Incomplete**: Only 2 of the 5 approved candidates had been evaluated (`Qwen2.5-0.5B` and `Qwen2.5-1.5B`). `Llama-3.2-1B`, `SmolLM2-1.7B`, and `granite-4.0-1b` were not yet evaluated.
2. **Process Violation**: The agent recorded owner decisions without verbatim owner text and wrote chosen/baseline values directly into frozen manifest v2.1.
3. **Formal Owner Decisions D18, D19, D20**: Recorded verbatim in `docs/decisions/owner_decisions.md`. Manifest v2.2 reverts all baseline values to `PENDING_OWNER_CONFIRMATION`.
