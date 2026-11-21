# Proposals for Owner Decisions: D13 Follow-up, D15 Gate Alignment, and Contamination Protocol

**Document:** `docs/decisions/D13_D15_proposals.md`  
**Date:** 2026-11-19  
**Status:** PROPOSALS FOR OWNER DECISION (Not Decided by Agent)  
**Authors:** Member A  

---

## Proposal A: Fictional Arm Scoring & Reporting Isolation (Decision D13 Clarification)

### Context
In Suite v2.0, the `knowledge_qa` task group contains:
- 200 real Wikipedia QA items per partition (public arm)
- 100 fictional entity QA items per partition (synthetic arm)

### Proposal
1. **Separate Arm Reporting**: In all evaluation reports, run records, and leaderboard summaries, the fictional entity arm (`arm: "synthetic"`, `source: "fictional"`) must be evaluated and scored as its own independent arm.
2. **Never Pooled into Headline Metric**: Fictional entity accuracy will **never** be pooled with real Wikipedia QA into a single blended `knowledge_qa` headline figure.
3. **Explicit Arm Tag**: Every JSONL record in evaluation runs will include `"arm": "public"` or `"arm": "synthetic"`.

---

## Proposal B: Decision D15 — Gate Evaluation Scope Across Public and Synthetic Arms

### Context
The Prototype 1 plan defines the retrieval gate for the knowledge store:
> **Gate G-Q**: Small model B with retrieval improves Knowledge QA accuracy by $\ge +10\text{ pp}$ over B without retrieval.

If the fictional arm is pooled into the store group, its clean retrieval delta (+84 pp in pilot: 0% without retrieval $\to$ 84% with retrieval) would single-handedly pass the +10 pp gate, even if retrieval on real-world knowledge suffered from ranking noise or extraction failures.

### Proposal for Gate D15
1. **Primary Gate G-Q Scope**: Evaluate the formal $+10\text{ pp}$ retrieval improvement gate strictly on the **Real Wikipedia Public Arm** (200 items per partition).
   - This ensures the retrieval-augmented architecture proves its effectiveness on real-world, messy natural language text.
2. **Diagnostic Role of Fictional Arm**: Evaluate the **Fictional Entity Arm** (100 items per partition) as a standalone diagnostic control:
   - Verifies that zero-shot parametric memorization is $\approx 0.0\%$.
   - Quantifies the pure retrieval-grounding capability of the model in the complete absence of pretraining contamination.
3. **Threshold Stability**: No metric thresholds are altered; the gate remains $+10\text{ pp}$, evaluated on the real-world knowledge arm.

---

## Proposal C: Contamination Protocol and Transparency Reporting

### Context
Public benchmarks (GSM8K, ARC-Challenge, MMLU, MBPP) are widely known to exist in the pretraining corpora of modern small language models (Qwen 2.5, SmolLM2, Llama 3.2). 

### Proposal
1. **Transparent Attribution**: All evaluation reports must explicitly distinguish:
   - **Public Benchmark Arms**: Prone to pretraining contamination. Scores reflect standard benchmark capability.
   - **Synthetic Arms** (Procedural Math, Procedural Code, Memory Probe, Fictional Entities): Free from pretraining memorization, isolating algorithmic reasoning, retrieval grounding, and chronological state updates.
2. **Verifier Hold-out Discipline**: Member B's verifier training will use **only** the `train` partition. Validation and locked test partitions remain strictly out-of-sample.

