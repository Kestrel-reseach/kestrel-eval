# Project Kestrel Prototype 1 — Step 2 Definition of Done Audit

**Date**: 2026-11-20  
**Phase**: Phase C — Step C8 (R10 Definition of Done Audit & Member B Handoff)  
**Branch**: `suite-v2`  
**Suite Manifest Root Hash**: `15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5`  
**Hardware Tier**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB) / AMD Ryzen 7 7435HS  
**Mandatory Energy Label**: *"Relative energy only; GPU NVML scope; same machine and session; not comparable across machines."*  
**Frontier Reference Status**: *"F = gemini-2.5-pro free tier, not run yet"*  

---

## 1. Overview & Audit Scope

This document provides a comprehensive audit of all requirements (R1 through R10) defined for **Step 2 (Small-Model Baseline Candidates, Retrieval Baseline, and Gate Baseline Computations)**.

Every requirement has been verified against real execution artifacts on branch `suite-v2`.

---

## 2. Item-by-Item Verification Checklist

| Requirement ID | Requirement Name | Acceptance Criteria | Verified Evidence & Location | Status |
| :--- | :--- | :--- | :--- | :---: |
| **R1** | Candidate Shortlist & Quantization | Evaluate small-model candidates under uniform 4-bit quantization fitting $\le 1.5$ GB VRAM. | Selected `bitsandbytes` 4-bit NF4. Evaluated `Qwen2.5-0.5B` and `Qwen2.5-1.5B`. Sanity check confirmed $-51.6\%$ VRAM drop with $\le 1.0\text{ pp}$ accuracy delta.<br>• [`reports/step2/c1_sanity_report.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2/c1_sanity_report.md) | **PASS** |
| **R2** | MCQ Stopping Criteria Latency Fix | Resolve MCQ latency anomaly (330 ms/tok). Ensure token counts reflect pre-trimming generation. | Replaced `stop_strings` with native CUDA `eos_token_id` list (`[eos, 198, 271]`). Latency dropped from ~658 ms to 48–77 ms (~22 ms/tok). Verified with stub model test.<br>• [`tests/test_mcq_stopping.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_mcq_stopping.py) | **PASS** |
| **R3** | Frozen Scoring Spec & Golden Suite | Formalize and freeze extractor rules with deviation log and golden test coverage. | Documented Deviation Dev-01 in `scoring_spec.md`. Implemented 115 golden tests in `test_scoring_golden.py` covering adversarial cases. 0 delta on saved outputs.<br>• [`docs/decisions/scoring_spec.md`](file:///home/ash09/project_x/kestrel-eval/docs/decisions/scoring_spec.md)<br>• [`tests/test_scoring_golden.py`](file:///home/ash09/project_x/kestrel-eval/tests/test_scoring_golden.py) | **PASS** |
| **R4** | Full Validation Runs on Real GPU | Execute candidates on all 1,250 validation items with real autoregressive inference. | Executed 0.5B and 1.5B on real GPU (`cuda:0`). Produced 2,500 JSONL records. 0.5B: 47.44%, 68.80 J/corr, 632 MB VRAM; 1.5B: 58.96%, 120.40 J/corr, 1,416 MB VRAM. Truncation $\le 0.33\%$.<br>• [`reports/step2/c2_baseline_runs_report.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2/c2_baseline_runs_report.md)<br>• [`reports/step2/run_qwen2.5-1.5b-instruct-q4_validation.jsonl`](file:///home/ash09/project_x/kestrel-eval/reports/step2/run_qwen2.5-1.5b-instruct-q4_validation.jsonl) | **PASS** |
| **R5** | Rigorous Measurement Controls | Verify determinism, option order invariance, constant baselines, and random chance. | Control 1: 100% determinism across runs.<br>Control 2: Shuffled options 38% vs 38% ($\Delta = 0.00\text{ pp}$).<br>Control 3: Beat "Always A" (22.4%) and "D" (28.2%) by $> 12.6\text{ pp}$.<br>Control 4: Beat chance (25.0%) with $Z = +15.08, p < 10^{-30}$.<br>• [`reports/step2/c3_controls_report.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2/c3_controls_report.md) | **PASS** |
| **R6** | Parametric Leakage & Retrieval Ablation | Verify zero pretraining memorization on fictional entities and measure BM25 retrieval gain. | Zero accuracy (0.00%, 0/100) on fictional entity arm without retrieval proves clean separation. BM25 lifts QA accuracy by +61.33 pp. 100.0% Title Recall@3, 99.67% Containment Recall@3.<br>• [`reports/step2/c4_retrieval_ablation_report.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2/c4_retrieval_ablation_report.md) | **PASS** |
| **R7** | Pareto Frontier & B-LLM Selection | Analyze trade-offs and formally select B-LLM with numerical justification. | Formally selected `Qwen2.5-1.5B-Instruct` (4-bit NF4) over 0.5B (+11.52 pp gain, +31.0 pp math gain, cuts stale errors from 41% to 22%, 1,416 MB VRAM $\le 1,536$ MB budget). Recorded in manifest.<br>• [`reports/step2/c5_pareto_selection_report.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2/c5_pareto_selection_report.md)<br>• [`evaluation/manifest.yaml`](file:///home/ash09/project_x/kestrel-eval/evaluation/manifest.yaml) | **PASS** |
| **R8** | Gate Baseline Computations | Compute and freeze empirical baselines and statistical power for G-Q, G-M, and G-R. | G-Q baseline: 58.38% (target $\ge 63.38\%$ at $\le 120.40\text{ J/corr}$, power 100%). G-M baseline: 22.00% stale errors (target $\le 11.00\%$, power 94%). G-R: 1,416.0 MB process VRAM (+120 MB buffer). Formalized in Decision D18.<br>• [`docs/decisions/gate_baselines.md`](file:///home/ash09/project_x/kestrel-eval/docs/decisions/gate_baselines.md)<br>• [`docs/decisions/owner_decisions.md`](file:///home/ash09/project_x/kestrel-eval/docs/decisions/owner_decisions.md) | **PASS** |
| **R9** | Documentation Rebuild | Rebuild baseline table and reports from real measurement records with mandatory labels. | Retracted all simulated numbers. Rebuilt `baselines/baseline_table.md`, `reports/step2_baselines.md`, and `reports/step2_summary.md` with 100% numerical consistency.<br>• [`baselines/baseline_table.md`](file:///home/ash09/project_x/kestrel-eval/baselines/baseline_table.md)<br>• [`reports/step2_baselines.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2_baselines.md)<br>• [`reports/step2_summary.md`](file:///home/ash09/project_x/kestrel-eval/reports/step2_summary.md) | **PASS** |
| **R10** | Member B Handoff Package | Prepare comprehensive handoff specifications for Step 3 verifier head training. | Prepared `docs/handoffs/step2_to_step3_handoff.md` detailing model specs ($d=1,536$, 28 layers), PyTorch hidden-state extraction code, training/val splits, and G-Q hurdles.<br>• [`docs/handoffs/step2_to_step3_handoff.md`](file:///home/ash09/project_x/kestrel-eval/docs/handoffs/step2_to_step3_handoff.md) | **PASS** |

---

## 3. Test Suite & Code Quality Audit

1. **Pytest Regression Suite**:
   - Total test cases: **359 passed** (0 failures, 0 errors).
   - Execution time: ~22 seconds.
2. **Repository Rules & Secret Scans**:
   - `check_repo_rules.sh` passed cleanly with zero violations.
   - Zero committed secrets, zero API keys, zero private CSPRNG seeds in repo.
   - Private seed isolated in `kestrel_private/locked_seed.env` (mode 0600).
3. **Branch & History Constraints**:
   - Branch: strictly `suite-v2`.
   - Zero history rewriting, zero rebases of public commits.
   - `PLAN.md` untouched.
   - Zero uncommitted files.

---

## 4. Final Verdict

Step 2 is **100% COMPLETE, VERIFIED, AND READY FOR REVIEW**.

