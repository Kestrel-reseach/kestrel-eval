---
name: suite-split-hash
description: >
  Locked evaluation suite structure, partition splitting and hashing.
  Load this skill when building or reviewing the locked suite (Step 1).
---

# Skill: suite-split-hash

## Suite groups

| Group | Key | Size | Answer check |
|-------|-----|------|--------------|
| Math word problems | `math` | 200 | exact numeric match |
| Science MCQ (ARC style) | `science_mcq` | 200 | answer key |
| Knowledge MCQ (MMLU style, 10 subjects) | `knowledge_mcq` | 300 | answer key |
| Code tasks with unit tests | `code` | 100 | unit tests pass |
| Knowledge QA over fixed corpus | `knowledge_qa` | 300 | key match |
| Personal-memory probe (30 stale-fact items) | `memory_probe` | 100 | key from source history |

Sizes are totals across all partitions.

## Partition fractions (from manifest.yaml)

```
train: 60 %   (120 / 120 / 180 / 60 / 180 / 60 items)
validation: 20 %
locked_test: 20 %
```

## Splitting algorithm

```python
import hashlib, json

def split_items(
    items: list[dict],
    seed: int,
    fractions: dict[str, float],
) -> dict[str, list[dict]]:
    """Deterministic split by hash of (seed, item_id)."""
    def bucket(item_id: str) -> float:
        digest = hashlib.sha256(f"{seed}:{item_id}".encode()).hexdigest()
        return int(digest[:8], 16) / 0xFFFFFFFF

    result = {name: [] for name in fractions}
    cuts = []
    cumulative = 0.0
    for name, frac in fractions.items():
        cumulative += frac
        cuts.append((cumulative, name))

    for item in items:
        b = bucket(item["item_id"])
        for threshold, name in cuts:
            if b <= threshold:
                result[name].append(item)
                break
    return result
```

Seed: `manifest["seeds"]["suite_split"]` (20260101).

## Hashing partitions

```python
import hashlib, json

def hash_partition(items: list[dict]) -> str:
    """SHA-256 of sorted item IDs."""
    ids = sorted(item["item_id"] for item in items)
    return hashlib.sha256(json.dumps(ids).encode()).hexdigest()
```

Store hashes in `manifest.yaml` under `locked_test_hashes` before any tuning.

## Leakage check

After splitting, verify no `item_id` appears in more than one partition:

```python
def check_no_overlap(partitions: dict[str, list[dict]]) -> None:
    seen = {}
    for name, items in partitions.items():
        for item in items:
            iid = item["item_id"]
            if iid in seen:
                raise ValueError(f"{iid!r} appears in both {seen[iid]!r} and {name!r}")
            seen[iid] = name
```

## Contamination note

Public items (ARC, MMLU, math benchmarks) may be in the training data of the
frontier model F and B-LLM. Report accuracy on public and privately-written
synthetic items **separately** in every table.

## Personal-memory probe

- 100 items total; 30 are stale-fact items.
- A stale-fact item records a fact that changes over the history; the **later**
  value is the answer key.
- Use synthetic histories only unless the owner approves real items one by one.
- Never commit real personal histories to the repository.

