---
name: baseline-runs
description: >
  Protocol for running small-model baseline candidates (Step 2).
  Load this skill when setting up or reviewing Step 2 baseline runs.
---

# Skill: baseline-runs

## Goal

Choose **B-LLM** — the best quantized small model — by measurement on the
validation partition, using the same harness as every other system.

## Candidates (from PLAN.md Step 2)

Confirm versions and sizes before downloading; models dated after early 2026
are unverified.

| Candidate | Approx size | 4-bit VRAM | Note |
|-----------|-------------|------------|------|
| Qwen3.5-0.8B-Instruct | 0.8 B | ~0.6 GB | Fits GPU tier easily |
| Qwen3.5-2B-Instruct | 2 B | ~1.4 GB | Near the 1.5 GB limit |
| Granite-4.0-Nano-1.5B | 1.5 B | ~1.0 GB | Confirm version |
| LFM2 | confirm | confirm | Confirm before download |

A 3B model at 4-bit does not fit the 1–1.5 GB VRAM budget; it is CPU-tier only.

## Per-candidate checklist

For each candidate, record in the same JSONL schema:

1. Quantize to 4-bit (GGUF or AWQ; record method and tool version).
2. Load model; measure peak VRAM with `torch.cuda.max_memory_allocated()` or
   NVML after the first forward pass.
3. Run on the validation partition with **plain retrieval** (no Kestrel parts).
4. For each item, write a JSONL record with all required fields.
5. Compute: accuracy, 95% CI, joules per correct task, resident GB, p50/p95 latency.

## Choosing B-LLM

Do **not** choose by name or reputation. Choose by the
accuracy-versus-energy-versus-memory trade-off on the validation partition.
Write the choice and the numerical justification in the manifest and in the PR
description.

## Frontier reference F

- Run F once on **public and synthetic items only** (never on the memory probe
  with real personal data).
- For the memory probe: run F twice — with no history (lower bound) and with
  the full history pasted into the prompt (upper bound).
- Record the model name, API version, cost and timestamp.
- Stay within the owner's cost cap (write UNDEFINED until the owner sets it).

## Kill gate

If no candidate fits the VRAM budget with usable accuracy (> random baseline),
lower the target model size or move the base to the CPU tier and rewrite G-R
in the manifest before continuing.

## Output

Deliverable: a table in `baselines/baseline_table.md` with one row per
candidate and system (F, B-LLM, each candidate), one column per metric:

```
| System | Group | Accuracy | 95% CI | J/correct | Resident GB | p50 ms | p95 ms |
```

Fill every cell. Mark unmeasured cells as UNMEASURED.

