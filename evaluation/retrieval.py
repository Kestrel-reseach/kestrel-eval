"""Minimal reproducible flat retriever for Knowledge-QA (Step 2 Part 4a).

Implements a deterministic, zero-VRAM BM25Okapi flat retriever over the
6,000-article Wikipedia abstract corpus snapshot (data/wikipedia_abstracts_5k.jsonl).

Metadata:
    Retriever: BM25Okapi-v1
    Algorithm: Robertson & Zaragoza (2009)
    Parameters: k1=1.5, b=0.75
    VRAM Footprint: 0.0 MB (Pure CPU / standard library)
    License: MIT / Apache-2.0 compatible
    Top-k: 3 (fixed for all candidates)
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict


class RetrievedDoc(TypedDict):
    """Metadata and content for a single retrieved document chunk."""

    article_id: str
    title: str
    text: str
    score: float
    rank: int


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return re.findall(r"\w+", text.lower())


@dataclass
class BM25Retriever:
    """Deterministic, pure-Python BM25Okapi flat index over Wikipedia abstracts."""

    k1: float = 1.5
    b: float = 0.75
    title_boost: int = 2

    def __post_init__(self) -> None:
        self.docs: list[dict[str, Any]] = []
        self.doc_lens: list[int] = []
        self.avgdl: float = 0.0
        self.postings: dict[str, list[tuple[int, int]]] = {}
        self.idf: dict[str, float] = {}
        self.is_indexed: bool = False

    @classmethod
    def from_jsonl(
        cls,
        corpus_path: Path | str,
        k1: float = 1.5,
        b: float = 0.75,
        title_boost: int = 2,
    ) -> BM25Retriever:
        """Instantiate and build a BM25 index from a JSONL abstract corpus."""
        retriever = cls(k1=k1, b=b, title_boost=title_boost)
        retriever.index_corpus(corpus_path)
        return retriever

    def index_corpus(self, corpus_path: Path | str) -> None:
        """Load and index documents from the corpus JSONL file."""
        path = Path(corpus_path)
        if not path.exists():
            raise FileNotFoundError(f"Corpus not found at {path}")

        docs: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))

        self.docs = docs
        n_docs = len(docs)
        if n_docs == 0:
            self.is_indexed = True
            return

        doc_lens: list[int] = []
        postings: dict[str, list[tuple[int, int]]] = {}
        df: Counter[str] = Counter()

        for doc_idx, doc in enumerate(docs):
            title = doc.get("title", "")
            abstract = doc.get("abstract", "")
            # Boost title terms to prioritize direct entity matches
            boosted_title = (title + " ") * self.title_boost
            tokens = tokenize(boosted_title + abstract)
            doc_lens.append(len(tokens))

            tf = Counter(tokens)
            for term, count in tf.items():
                if term not in postings:
                    postings[term] = []
                postings[term].append((doc_idx, count))
                df[term] += 1

        self.doc_lens = doc_lens
        self.avgdl = sum(doc_lens) / n_docs
        self.postings = postings

        # Calculate standard BM25 IDF: ln((N - df + 0.5) / (df + 0.5) + 1.0)
        idf: dict[str, float] = {}
        for term, freq in df.items():
            idf[term] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)
        self.idf = idf
        self.is_indexed = True

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedDoc]:
        """Retrieve top-k documents for a query with deterministic tie-breaking."""
        if not self.is_indexed or not self.docs:
            return []

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        scores: dict[int, float] = {}
        k1 = self.k1
        b = self.b
        avgdl = self.avgdl

        for term in q_tokens:
            term_idf = self.idf.get(term)
            if term_idf is None:
                continue
            for doc_idx, count in self.postings.get(term, []):
                dl = self.doc_lens[doc_idx]
                numerator = count * (k1 + 1.0)
                denominator = count + k1 * (1.0 - b + b * (dl / avgdl))
                term_score = term_idf * (numerator / denominator)
                scores[doc_idx] = scores.get(doc_idx, 0.0) + term_score

        if not scores:
            return []

        # Deterministic sort: descending by score, tie-break by article_id ascending
        ranked = sorted(
            scores.items(),
            key=lambda x: (-x[1], self.docs[x[0]].get("article_id", "")),
        )

        results: list[RetrievedDoc] = []
        for rank, (doc_idx, score) in enumerate(ranked[:top_k], start=1):
            doc = self.docs[doc_idx]
            results.append(
                {
                    "article_id": doc.get("article_id", f"doc_{doc_idx}"),
                    "title": doc.get("title", ""),
                    "text": doc.get("abstract", ""),
                    "score": round(score, 4),
                    "rank": rank,
                }
            )
        return results

    def augment_knowledge_qa_prompt(
        self,
        item: dict[str, Any],
        top_k: int = 3,
    ) -> tuple[str, list[RetrievedDoc]]:
        """Augment a Knowledge-QA item with top-k retrieved corpus passages.

        Returns:
            A tuple of (augmented_prompt, retrieved_docs).
        """
        question = item.get("question")
        if not question:
            # Fallback if question field not standalone
            prompt = item.get("prompt", "")
            m = re.search(r"Question:\s*(.*?)(?:\nAnswer:|$)", prompt, re.DOTALL)
            question = m.group(1).strip() if m else prompt

        hits = self.retrieve(question, top_k=top_k)

        context_blocks = []
        for doc in hits:
            context_blocks.append(f"[{doc['rank']}] {doc['title']}: {doc['text']}")

        context_text = "\n\n".join(context_blocks)
        augmented_prompt = f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"
        return augmented_prompt, hits
