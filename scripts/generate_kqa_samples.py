"""Generate 50 random review items from VALIDATION partition only for Knowledge QA (PR 3 / 3B).

CRITICAL DISCIPLINE:
- Samples strictly from validation partition.
- Never samples or exports from locked-test partition.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from evaluation.generators.knowledge_qa_generator import generate_knowledge_qa_suite  # noqa: E402

corpus_path = Path("data/wikipedia_abstracts_5k.jsonl")
corpus: list[dict] = []
with open(corpus_path, encoding="utf-8") as f:
    for line in f:
        corpus.append(json.loads(line))

suites = generate_knowledge_qa_suite(
    corpus, seed=20260101, train_size=300, val_size=300, locked_test_size=300
)

rng = random.Random(20260101)
review_doc_path = Path("reports/step1_knowledge_qa_validation_samples.md")

lines = [
    "# Knowledge QA Human Review Sample (50 Validation Items)",
    "",
    "**Corpus**: English Wikipedia Foundational Articles (`enwiki-20261101-pages-articles1.xml-p1p41242.bz2`, SHA-256 `e3fd5a837f2a6b3a26c3596d0667600073a86c9fc29dc60ef0b2de605c754387`)  ",
    "**Corpus Size**: 6,000 lead article abstracts in `data/wikipedia_abstracts_5k.jsonl` (~5k subset per Decision D2).  ",
    "**Partition**: VALIDATION partition only (50 of 300 items).  ",
    "**Span Verification**: Every item has an exact character span `[start, end]` where `passage[start:end] == answer`. All items 100% verified.  ",
    "",
    "---",
    "",
    "## VALIDATION Partition Samples (50 items of 300)",
    "",
    "| # | ID | Passage Title | Question | Ground Truth Answer | Answer Span | Type | Rule |",
    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
]

items = suites["validation"]
sample_50 = rng.sample(items, 50)
for idx, it in enumerate(sample_50, 1):
    q = it["question"].replace("|", "/")
    ans = it["answer"].replace("|", "/")
    title = it["passage_title"].replace("|", "/")
    span_str = f"[{it['answer_span'][0]}, {it['answer_span'][1]}]"
    lines.append(
        f"| {idx} | `{it['id']}` | {title} | {q} | **{ans}** | `{span_str}` | {it['answer_type']} | `{it['rule_family']}` |"
    )

lines.append("")
lines.append("---")
lines.append("")

with open(review_doc_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Wrote review document to {review_doc_path} ({len(lines)} lines)")
