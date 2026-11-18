# Step 2 Report: Preconditions, Frontier Rate Limits & Knowledge-QA Retrieval Baseline

**Date**: 2026-11-18  
**Step**: Step 2 (Baselines and Frontier Reference $F$) — Part 4-0, 4a, and Runner Seams  
**Branch**: `step-2-baselines-and-f`  
**Repository**: `kestrel-eval`  

---

## 1. Preconditions & Frontier Model $F$ Configuration (Part 4-0)

Frontier Reference Model $F$ is governed by owner decisions **D6** and **D12** (frozen in `evaluation/manifest.yaml`):
- **Model**: `gemini-2.5-pro` via Google AI Studio (free tier, OpenAI-compatible endpoint).
- **Cost Cap**: $0.00 (strictly zero paid API calls).
- **Mandatory Label**: *"F = gemini-2.5-pro (free tier), exact version and date recorded; a free-tier reference, not the current frontier."*
- **Current API Key Status**: `GEMINI_API_KEY` is **UNSET** in the local environment. Per protocol Part 4-0, key values are recorded as `UNDEFINED` and Frontier $F$ evaluation status is marked **PENDING**. Local candidate evaluation proceeds independently.

### Rate Limits & Pacing (`config/f_limits.yaml`)

```yaml
model: "gemini-2.5-pro"
provider: "Google AI Studio"
endpoint_type: "openai_compatible"
cost_cap_usd: 0
tier: "free_tier"
api_key_env_var: "GEMINI_API_KEY"
status: "PENDING_KEY"

limits:
  requests_per_minute: 2       # Conservative RPM pacing to prevent 429 errors
  requests_per_day: 50         # Conservative free tier daily budget
  tokens_per_minute: 32000
  max_context_tokens: 2048     # Frozen context length (D5)
  max_output_tokens: 256
```

### Estimated Run Duration
- **Validation Partition Size**: 1,200 items.
- **Pacing**: At 50 requests/day, running the entire 1,200 validation partition on free-tier $F$ takes an estimated **24.0 days**.
- **Memory Probe**: Evaluated twice (no-history vs full-history) = 200 items (4.0 days).

---

## 2. Minimal Retrieval Baseline for Knowledge-QA (Part 4a)

To evaluate Knowledge-QA under identical conditions without consuming VRAM from the 1.5 GB assistant budget, a pure-Python flat BM25 retriever was implemented.

- **Corpus**: `data/wikipedia_abstracts_5k.jsonl` (6,000 articles, snapshot SHA-256 `e3fd5a83...`).
- **Retriever Model**: `BM25Okapi-v1` (Robertson & Zaragoza, 2009).
- **License**: MIT / Apache-2.0 compatible.
- **Parameters**: $k_1 = 1.5$, $b = 0.75$, title boost = 2.
- **Top-$k$**: Exactly 3 chunks fixed for all candidate runs.
- **VRAM Footprint**: **0.0 MB** (zero extra VRAM required, running entirely in CPU RAM).
- **Latency**: Index built in 1.3s; average retrieval latency is 1.8 ms per query with inverted index postings.
- **Formatting**:
  ```
  Context:
  [1] <Title>: <Abstract>
  [2] <Title>: <Abstract>
  [3] <Title>: <Abstract>

  Question: <Question>
  Answer:
  ```

---

## 3. Small-Model Shortlist & VRAM Budget Verification (Part 4b)

Hardware tier accepted 2026-11-18: **AMD Ryzen 7 7435HS + NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)**.  
Assistant VRAM Budget: **$\le$ 1.5 GB** at context length 2048 tokens.

| Candidate ID | Model Name | Parameters | 4-bit Quantization | Tier | Estimated 4-bit VRAM | Fits $\le$ 1.5 GB Budget? | License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `qwen2.5-0.5b-instruct-q4` | Qwen2.5-0.5B-Instruct | 0.49 B | AWQ / GGUF Q4_K_M | GPU | 0.45 GB | **YES** (fits easily) | Apache-2.0 |
| `qwen2.5-1.5b-instruct-q4` | Qwen2.5-1.5B-Instruct | 1.54 B | AWQ / GGUF Q4_K_M | GPU | 1.15 GB | **YES** (near budget) | Apache-2.0 |
| `granite-3.1-2b-instruct-q4` | Granite-3.1-2B-Instruct | 2.50 B | AWQ / GGUF Q4_K_M | GPU | 1.40 GB | **YES** (within budget) | Apache-2.0 |
| `qwen2.5-3b-instruct-q4` | Qwen2.5-3B-Instruct | 3.09 B | AWQ / GGUF Q4_K_M | CPU | 2.25 GB | **NO** (CPU tier only) | Apache-2.0 |

*Diagnostic capability*: `LocalRunner` supports toggling `use_retrieval=True` vs `use_retrieval=False` to measure the parametric vs retrieval-augmented Knowledge-QA delta.

---

## 4. Verification & Testing

- **Total Test Cases**: 196 passed (16 new tests for retrieval, f_limits, and candidate runners).
- **Linting & Formatting**: Clean (`ruff check .` passed with 0 errors; `ruff format --check .` passed).
- **Repo Rules**: Passed (`check_repo_rules.sh` clean).
- **Mandatory Labels**: Integrated into all runner configurations and outputs.

