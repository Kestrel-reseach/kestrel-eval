"""Unit tests for the minimal BM25 flat retriever (Step 2 Part 4a)."""

import json
from pathlib import Path

import pytest

from evaluation.retrieval import BM25Retriever, tokenize


@pytest.fixture
def mini_corpus(tmp_path: Path) -> Path:
    """Create a temporary small corpus for isolated tests."""
    corpus_file = tmp_path / "mini_corpus.jsonl"
    data = [
        {
            "article_id": "art_001",
            "title": "Marie Curie",
            "abstract": "Marie Curie was a Polish and naturalised-French physicist and chemist who conducted pioneering research on radioactivity.",
        },
        {
            "article_id": "art_002",
            "title": "Albert Einstein",
            "abstract": "Albert Einstein was a German-born theoretical physicist who developed the theory of relativity.",
        },
        {
            "article_id": "art_003",
            "title": "Radioactivity",
            "abstract": "Radioactivity is the process by which an unstable atomic nucleus loses energy by radiation.",
        },
        {
            "article_id": "art_004",
            "title": "Quantum Mechanics",
            "abstract": "Quantum mechanics is a fundamental theory in physics that describes the physical properties of nature at atomic scales.",
        },
    ]
    with corpus_file.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return corpus_file


def test_tokenize():
    """Verify tokenizer lowercases and splits words correctly."""
    tokens = tokenize("Marie Curie, born in Warsaw (1867)!")
    assert tokens == ["marie", "curie", "born", "in", "warsaw", "1867"]


def test_bm25_retrieval_ranking(mini_corpus: Path):
    """Verify BM25 ranks the exact entity match first."""
    retriever = BM25Retriever.from_jsonl(mini_corpus)
    hits = retriever.retrieve("Who conducted research on radioactivity, Marie Curie?", top_k=2)

    assert len(hits) == 2
    assert hits[0]["title"] == "Marie Curie"
    assert hits[0]["article_id"] == "art_001"
    assert hits[0]["rank"] == 1
    assert hits[0]["score"] > hits[1]["score"]


def test_bm25_top_k_bound(mini_corpus: Path):
    """Verify retriever strictly returns at most requested top_k documents."""
    retriever = BM25Retriever.from_jsonl(mini_corpus)
    hits = retriever.retrieve("physicist", top_k=3)
    assert len(hits) <= 3
    for rank, hit in enumerate(hits, start=1):
        assert hit["rank"] == rank


def test_bm25_empty_query_returns_empty(mini_corpus: Path):
    """Verify empty or whitespace query returns no documents."""
    retriever = BM25Retriever.from_jsonl(mini_corpus)
    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []


def test_augment_knowledge_qa_prompt(mini_corpus: Path):
    """Verify prompt formatting includes retrieved context blocks."""
    retriever = BM25Retriever.from_jsonl(mini_corpus)
    item = {
        "id": "kqa_001",
        "question": "What theory did Albert Einstein develop?",
        "target": "theory of relativity",
    }
    aug_prompt, hits = retriever.augment_knowledge_qa_prompt(item, top_k=2)

    assert len(hits) == 2
    assert hits[0]["title"] == "Albert Einstein"
    assert "Context:\n" in aug_prompt
    assert "[1] Albert Einstein:" in aug_prompt
    assert "Question: What theory did Albert Einstein develop?" in aug_prompt
    assert aug_prompt.endswith("Answer:")


def test_real_corpus_snapshot_loads():
    """Verify the real 6k Wikipedia abstract corpus loads cleanly if present."""
    corpus_path = Path("data/wikipedia_abstracts_5k.jsonl")
    if not corpus_path.exists():
        pytest.skip("data/wikipedia_abstracts_5k.jsonl not present")

    retriever = BM25Retriever.from_jsonl(corpus_path)
    assert len(retriever.docs) == 6000
    assert retriever.is_indexed

    # Test sample query
    hits = retriever.retrieve("When was Bartolomeo Ammannati born?", top_k=3)
    assert len(hits) == 3
    assert hits[0]["title"] == "Bartolomeo Ammannati"
