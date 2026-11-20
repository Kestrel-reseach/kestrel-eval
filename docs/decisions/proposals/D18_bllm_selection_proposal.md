# Proposal: Candidate B-LLM Selection & Initial Gate Baselines (PROPOSED)

**Status**: **PROPOSED / PENDING OWNER CONFIRMATION**  
**Author**: Evaluation Harness (Member A)  
**Date**: 2026-11-20  
**Context**: Formulated under Owner Decisions D18–D20 following the Step 2 Correction Pass.

---

## Proposed Selection Text (Pending Owner Confirmation)

> "B-LLM is proposed as Qwen/Qwen2.5-1.5B-Instruct in bitsandbytes 4-bit NF4. Gate G-Q baseline on 800 checkable validation items is 56.88% (455/800, 95% Wilson CI [53.42, 60.27]%) at 171.55 Net Joules/correct; P1 target is >= 61.88% (+5.0 pp, paired bootstrap CI excludes 0) at <= 171.55 J/correct, or >= 53.88% at <= 85.78 J/correct (50% energy savings). Gate G-M baseline on 100 stale fact items is 22.00% stale error rate (22 errors, 95% cluster CI [14.0, 30.0]%); P1 target is <= 11.00% (PROVISIONAL relative to Step 6 plain memory). Gate G-R baseline is 1,416.0 MB NVML process VRAM at 2048 context, fitting under the 1,536.0 MB (1.5 GB) resident GPU budget with 120.0 MB headroom."

---

## Owner Review Context (2026-11-20)
1. **Candidate Scope Under D18/D19**:
   - `Qwen2.5-0.5B-Instruct` (NF4): Evaluated (Checkable Acc: 37.00%, Net Energy: 157.54 J/correct).
   - `Qwen2.5-1.5B-Instruct` (NF4): Evaluated (Checkable Acc: 56.88%, Net Energy: 171.55 J/correct).
   - `meta-llama/Llama-3.2-1B-Instruct`: Gated (`manual`). Blocked pending user provision of `HF_TOKEN`.
   - `HuggingFaceTB/SmolLM2-1.7B-Instruct`: Ungated (Apache 2.0).
   - `ibm-granite/granite-4.0-1b`: Ungated (Apache 2.0).
   - `Qwen/Qwen3.5-0.8B`: Ungated (Apache 2.0). Time-boxed exploration.
2. **Process Integrity**:
   - In accordance with project rules, `evaluation/manifest.yaml` maintains `PENDING_OWNER_CONFIRMATION` for `B_LLM.chosen` and all empirical gate baselines until formal co-owner review.
   - Owner Decisions D18, D19, and D20 are recorded verbatim in `docs/decisions/owner_decisions.md`.
