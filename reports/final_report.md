# Kestrel Prototype 1 — Final Report (Step 10)

> Relative energy only; GPU NVML scope; same machine and session; not comparable across machines.
> F = gemini-flash-lite-latest (gemini-3.5-flash-lite, free tier, D21); a free-tier reference, not the current frontier.

## The three numbers (validation)

- Quality gap to F: **23.49 pp** (3.09% of the gap closed)
- Energy per correct task: **297.02 J** (B-LLM 171.55 J)
- Resident memory: **1.385 GB** (B-LLM 1.383 GB)

## Gate verdicts

- **G_Q**: FAIL
- **G_F**: reported (not promised)
- **G_M**: PASS
- **G_R**: PASS
- **no_regression**: PASS (no-regression sanity only)
- **step3_verifier**: PASS
- **step4_halting**: FAIL
- **step5_store**: PASS
- **step6_memory**: PASS

## Failed components

- **Step 4 verifier-gated halting**: gate failed; fixed two-pass kept per kill rule (reports/halting_step4.json)
- **G-Q product quality gate**: P1 57.63% vs B-LLM 56.88%; delta 0.75 pp with CI including zero; energy above cap (reports/integration_step7.json)

## Ablations

- **ablation_no_verifier**: 63.2% accuracy, 213.83 J/correct
- **ablation_no_knowledge_store**: 49.6% accuracy, 272.08 J/correct
- **ablation_no_memory**: 54.4% accuracy, 248.87 J/correct
- **ablation_no_fixed_two_pass**: 65.12% accuracy, 123.39 J/correct

## Locked-test partition

**RUN** — One-time locked-test evaluation completed across F, B-LLM, and P1 using frozen manifest v2.3 config on Ryzen 7 7435HS + RTX 3050 4 GB.

| System | Full Suite (1,250) | Checkable G-Q/G-F (800) | Store QA (300) | Memory (150) | Net J/Correct | Resident GB |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **F** | 80.16% (1002/1250) | 84.12% (673/800) | 64.67% (194/300) | 90.0% (135/150) | unmeasured | — |
| **B_LLM** | 66.08% (826/1250) | 63.62% (509/800) | 69.0% (207/300) | 73.33% (110/150) | 110.04 J | 1.217 GB |
| **P1** | 69.04% (863/1250) | 63.5% (508/800) | 71.33% (214/300) | 94.0% (141/150) | 196.95 J | 1.223 GB |

### Locked-test gate verdicts

- **G_Q**: FAIL
- **G_F**: reported (not promised)
- **G_M**: PASS
- **G_R**: PASS

## Decision

**publish_negative_result** — G-Q and G-R must both pass for prototype 2 (evaluated on locked_test: G-Q=FAIL, G-R=PASS).
