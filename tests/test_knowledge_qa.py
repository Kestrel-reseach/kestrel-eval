"""Unit tests for Knowledge QA extractor, span verification, and generator (PR 3)."""

from __future__ import annotations

from evaluation.generators.knowledge_qa_generator import (
    extract_qa_from_article,
    generate_knowledge_qa_suite,
    verify_qa_span,
)
from evaluation.generators.wiki_extractor import clean_wikitext


def test_clean_wikitext_strips_markup() -> None:
    raw = (
        "{{Short description|Ancient civilization}}\n"
        "{{Infobox country|name=Sumer}}\n"
        "'''Sumer''' was the earliest known [[civilization]] in the historical region of southern [[Mesopotamia]].\n"
        '<ref name="hist">History of Sumer</ref><!-- editorial comment -->\n'
        "It was founded in 4500 BC.\n\n"
        "== History ==\n"
        "More details here..."
    )
    cleaned = clean_wikitext(raw)
    assert "Infobox" not in cleaned
    assert "<!--" not in cleaned
    assert "<ref" not in cleaned
    assert "== History ==" not in cleaned
    assert "'''" not in cleaned
    assert (
        "Sumer was the earliest known civilization in the historical region of southern Mesopotamia."
        in cleaned
    )


def test_verify_qa_span_positive() -> None:
    passage = "Ada Lovelace (1815–1852) was an English mathematician and writer."
    answer = "1852"
    span = [passage.index(answer), passage.index(answer) + len(answer)]
    assert verify_qa_span(passage, answer, span) is True


def test_verify_qa_span_negative_mismatch() -> None:
    passage = "Alan Turing was born on 23 June 1912."
    answer = "1912"
    wrong_span = [0, 4]  # Points to 'Alan'
    assert verify_qa_span(passage, answer, wrong_span) is False


def test_verify_qa_span_negative_out_of_bounds() -> None:
    passage = "Short text."
    answer = "text"
    assert verify_qa_span(passage, answer, [6, 100]) is False
    assert verify_qa_span(passage, answer, [-1, 4]) is False


def test_extract_qa_from_article_span_integrity() -> None:
    article = {
        "article_id": "wiki_art_00001",
        "title": "Marie Curie",
        "abstract": (
            "Marie Curie (1867–1934) was a Polish and naturalized-French physicist and chemist. "
            "She was awarded the Nobel Prize in Physics in 1903. "
            "She was born on 7 November 1867 in Warsaw."
        ),
    }
    items = extract_qa_from_article(article)
    assert len(items) >= 2
    for item in items:
        span = item["answer_span"]
        passage = item["passage"]
        ans = item["answer"]
        assert passage[span[0] : span[1]] == ans
        assert ans.lower() not in item["question"].lower()
        assert item["passage_id"] == "wiki_art_00001"
        assert item["passage_title"] == "Marie Curie"


def test_generate_knowledge_qa_suite_determinism() -> None:
    corpus = [
        {
            "article_id": f"wiki_art_{i:04d}",
            "title": f"Entity {i}",
            "abstract": (
                f"Entity {i} (1900–198{i % 10}) was a renowned scholar. "
                f"The organization was founded in 195{i % 10}. "
                f"It was located in Oxford and was awarded the Copley Medal."
            ),
        }
        for i in range(1, 40)
    ]
    suite1 = generate_knowledge_qa_suite(
        corpus, seed=42, train_size=5, val_size=5, locked_test_size=5
    )
    suite2 = generate_knowledge_qa_suite(
        corpus, seed=42, train_size=5, val_size=5, locked_test_size=5
    )

    for split in ("train", "validation", "locked_test"):
        assert len(suite1[split]) == 5
        for it1, it2 in zip(suite1[split], suite2[split]):
            assert it1["id"] == it2["id"]
            assert it1["question"] == it2["question"]
            assert it1["answer"] == it2["answer"]
            assert it1["answer_span"] == it2["answer_span"]


def test_generate_knowledge_qa_suite_distinct_questions() -> None:
    corpus = [
        {
            "article_id": f"wiki_art_{i:04d}",
            "title": f"Philosopher {i}",
            "abstract": (
                f"Philosopher {i} was born on 12 May 18{i % 90 + 10}. "
                f"He died in 19{i % 80 + 10}. "
                f"He was located in Cambridge."
            ),
        }
        for i in range(1, 30)
    ]
    suite = generate_knowledge_qa_suite(
        corpus, seed=2026, train_size=5, val_size=5, locked_test_size=5
    )
    all_questions = [
        it["question"] for s in ("train", "validation", "locked_test") for it in suite[s]
    ]
    assert len(all_questions) == len(set(all_questions))
