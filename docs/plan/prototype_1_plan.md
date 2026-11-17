# Project Kestrel — Prototype 1: Detailed Execution Plan

What this is: a step-by-step plan to build and measure the first Kestrel prototype on the two-tier hardware (Ryzen 7 5800H CPU, RTX 3060 Laptop 6 GB with a 1–1.5 GB VRAM budget for the assistant, free Colab T4 for training). It is a plan, not a result. Nothing here has been built or tested. All thresholds marked *(proposed)* are drafts for the owner to accept or change before Step 0 freezes them.

## 1. Links
- Charter and gates: 00 — Program Charter v2: Token-Free Jarvis-Class Assistant
- Experimental protocol, baselines, pass rule, JSONL schema: 27 — Riya Experimental Implementation Plan: Curiosity, Control, Memory & Continual Learning
- Model shortlist: 19 — 2026 Small-Model & Architecture Landscape: What Competes Now
- Power measurement protocol: 29 — Always-On Two-Tier Efficiency, Power Measurement & Win Conditions
- Output-path evidence: 28 — Token-Free Language Output: Latent Sentences & Parallel Decoders
- Outside views and priority list: 31 — Outside Views: 16 Models Asked, Combined Priority List
- Why big labs do not build this: 32 — Why Big Labs Don't Build This (and What They Do)

## 2. What Kestrel is, and what prototype 1 takes from it
Kestrel separates what the model knows from how hard it thinks. It has four parts. Prototype 1 builds the first, second and fourth as real components around an existing pretrained model, and builds the third only as a small side experiment.

| Kestrel part | Prototype 1 form | Honest label |
| --- | --- | --- |
| Verifier-gated halting | A trained verifier head on the existing small model. A query loops (retry, refine, retrieve, escalate) until the verifier is confident or a budget runs out. | Real, buildable now |
| Knowledge store | A large index on SSD (embeddings plus text chunks), read by lookup, read only when confidence is low. | Plain retrieval-augmented generation until trained jointly. |
| Looped reasoning core | A toy model of about 100M parameters, trained on synthetic checkable tasks on the T4. | Research branch. |
| Test-time memory writes | Write-gated external memory with sources, timestamps and decay. Titans-style learned module only after that passes. | Step 6 is real. Step 9 is optional. |

## 3. The claim, and how it is tested

### Locked evaluation suite (Step 1)
| Group | Size | Purpose | Answer check |
| --- | --- | --- | --- |
| Math word problems | 200 | Checkable reasoning | Exact numeric match |
| Science multiple choice (ARC-Challenge style) | 200 | Checkable reasoning | Answer key |
| Knowledge multiple choice (MMLU style, 10 subjects) | 300 | Broad knowledge | Answer key |
| Code tasks with unit tests | 100 | Checkable reasoning | Tests pass |
| Knowledge QA over a fixed corpus snapshot | 300 | Tests the store | Exact or judged match against a key |
| Personal-memory probe | 100 (30 are stale-fact items) | Tests memory | Key from the source history |

### Pass gates for prototype 1 (proposed)
- **G-Q, quality versus baseline:** on checkable and store groups, P1 beats B-LLM by >= 5 pp (paired bootstrap 95% CI excludes zero) at no more than baseline energy per correct task. Or matches B-LLM accuracy at <= 50% energy.
- **G-F, gap to frontier:** report gap to F and fraction of B-LLM-to-F gap closed (>= 25% on checkable is strong).
- **G-M, memory slice:** P1 >= F (no history), within 5 pp of F (full history). Stale-fact errors <= 50% of plain external memory.
- **G-R, resources:** <= 1.5 GB resident VRAM, <= 4 GB resident RAM proposed, joules per correct task reported with p50/p95 latency.
- **No regression:** adding a component must not drop earlier-step results by > 3 pp.

## 4. Steps
- Step 0: Freeze and instrument (~1 week)
- Step 1: Build the locked suite (~1 week)
- Step 2: Baselines and frontier reference (~1 week)
- Step 3: Verifier head (~1–1.5 weeks)
- Step 4: Verifier-gated halting (~1 week)
- Step 5: Knowledge store on SSD (~1–1.5 weeks)
- Step 6: Write-gated memory with sources and decay (~1 week)
- Step 7: Integrate Kestrel-lite (~1 week)
- Step 8: Looped-core toy (optional branch, 3–5 T4 sessions)
- Step 9: Titans-style memory module (optional branch, 1–2 weeks)
- Step 10: Final evaluation and report (~1 week)

