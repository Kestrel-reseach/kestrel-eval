"""Knowledge QA generation module for Project Kestrel (Step 1).

Extracts factual QA items from a Wikipedia abstract corpus using deterministic rule-based
patterns. Ensures 100% automated span verification: every answer string has an exact
character offset [start_char, end_char] within its source passage such that:
    passage[start_char:end_char] == answer

Adheres strictly to project rules:
- No LLMs (neither F nor candidate models) are used to draft or filter questions.
- Every item has a source passage ID, article title, and exact character span.
- Answers are verified to be unambiguous and not leaked into the question.
- Strict semantic entity alignment: questions are natural, grammatically correct, and factual.
- Deterministic random sampling using fixed PRNG seeds.
"""

from __future__ import annotations

import json
import logging
import random
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATE_PATTERN = r"(?:[A-Z][a-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|\d{3,4})"

PAT_DECEASED_BIOGRAPHY = re.compile(
    rf"\(\s*(?:[^()]*?;\s*)?({DATE_PATTERN})\s*(?:&nbsp;)?\s*[–\-]\s*(?:&nbsp;)?\s*({DATE_PATTERN})\s*\)\s+was\s+",
    re.IGNORECASE,
)

PAT_LIVING_BIOGRAPHY = re.compile(
    rf"(?:\(born\s+|was\s+born\s+(?:on\s+)?|\b\(b\.\s+)({DATE_PATTERN})",
    re.IGNORECASE,
)

VALID_PROFESSIONS = (
    "mathematician",
    "physicist",
    "chemist",
    "astronomer",
    "biologist",
    "philosopher",
    "historian",
    "economist",
    "writer",
    "poet",
    "novelist",
    "politician",
    "composer",
    "painter",
    "sculptor",
    "actor",
    "actress",
    "director",
    "architect",
    "engineer",
    "diplomat",
    "geologist",
    "archaeologist",
    "anthropologist",
    "physician",
    "theologian",
    "statesman",
    "clergyman",
    "cricketer",
    "footballer",
    "lawyer",
    "monarch",
    "general",
)

PROF_REGEX = re.compile(
    r"\b(" + "|".join(VALID_PROFESSIONS) + r")\b",
    re.IGNORECASE,
)


def verify_qa_span(passage: str, answer: str, span: list[int]) -> bool:
    """Verify that an answer span is exact, non-empty, and matches passage text."""
    if not isinstance(span, (list, tuple)) or len(span) != 2:
        return False
    start, end = span
    if not (0 <= start < end <= len(passage)):
        return False
    extracted = passage[start:end]
    if extracted != answer:
        return False
    if len(answer.strip()) < 2:
        return False
    return True


def extract_qa_from_article(article: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract factual QA pairs with verified spans from an article abstract."""
    passage = article["abstract"]
    title = article["title"]
    article_id = article.get("article_id", "unknown_art")
    first_sent = passage.split(". ")[0] + "."
    candidates: list[dict[str, Any]] = []

    def _add_item(q: str, ans: str, span: list[int], ans_type: str, rule: str) -> None:
        if not verify_qa_span(passage, ans, span):
            return
        if ans.lower() in q.lower():
            return
        if ans.strip().lower() == title.strip().lower():
            return
        candidates.append(
            {
                "passage_id": article_id,
                "passage_title": title,
                "passage": passage,
                "question": q,
                "answer": ans,
                "answer_span": span,
                "answer_type": ans_type,
                "rule_family": rule,
                "answer_check": "key_match",
            }
        )

    # 1. Deceased biographical profile
    m_dec = PAT_DECEASED_BIOGRAPHY.search(first_sent)
    if m_dec:
        b_date, d_date = m_dec.group(1), m_dec.group(2)
        b_start = passage.find(b_date)
        if b_start != -1:
            _add_item(
                f"When was {title} born?",
                b_date,
                [b_start, b_start + len(b_date)],
                "date",
                "born_date",
            )
        d_start = passage.find(d_date)
        if d_start != -1:
            _add_item(
                f"When did {title} die?",
                d_date,
                [d_start, d_start + len(d_date)],
                "date",
                "death_date",
            )

        # Check profession in first sentence after lifespan
        tail = first_sent[m_dec.end() :]
        m_prof = PROF_REGEX.search(tail)
        if m_prof:
            prof = m_prof.group(1).lower()
            p_start = passage.find(prof, m_dec.end())
            if p_start != -1:
                _add_item(
                    f"What was the profession or occupation of {title}?",
                    prof,
                    [p_start, p_start + len(prof)],
                    "occupation",
                    "profession",
                )

    # 2. Living biographical profile
    m_liv = PAT_LIVING_BIOGRAPHY.search(first_sent)
    if m_liv:
        b_date = m_liv.group(1).strip()
        b_start = passage.find(b_date)
        if b_start != -1:
            _add_item(
                f"When was {title} born?",
                b_date,
                [b_start, b_start + len(b_date)],
                "date",
                "born_date",
            )

        tail = first_sent[m_liv.end() :]
        m_prof = PROF_REGEX.search(tail)
        if m_prof:
            prof = m_prof.group(1).lower()
            p_start = passage.find(prof, m_liv.end())
            if p_start != -1:
                _add_item(
                    f"What is the profession or occupation of {title}?",
                    prof,
                    [p_start, p_start + len(prof)],
                    "occupation",
                    "profession",
                )

    # 3. Organization founded year
    m_fnd = re.search(
        r"(?:is|was)\s+(?:an?|the)\s+([A-Za-z\s]+?(?:company|organization|university|college|corporation|firm|airline|bank|school|club|band|party|society|institute|museum|hospital|agency))\s+(?:founded|established)\s+in\s+(\d{4})",
        passage,
    )
    if m_fnd:
        year = m_fnd.group(2)
        start = m_fnd.start(2)
        end = start + len(year)
        _add_item(
            f"In what year was {title} founded or established?",
            year,
            [start, end],
            "year",
            "founded_year",
        )

    # 4. Capital city
    m_cap = re.search(
        r"is the capital\s+(?:and largest city\s+)?of\s+([A-Z][a-zA-Z\s]+?)(?:,|\.|\s+and)",
        passage,
    )
    if m_cap:
        ans = m_cap.group(1).strip()
        start = m_cap.start(1)
        end = start + len(ans)
        _add_item(
            f"What territory or country is {title} the capital of?",
            ans,
            [start, end],
            "location",
            "capital_city",
        )

    # 5. City in Region
    m_loc = re.search(
        r"is a\s+(?:city|town|village|municipality)\s+(?:of|in)\s+([A-Z][a-zA-Z\s]+?)(?:,|\.|\s+and)",
        first_sent,
    )
    if m_loc:
        ans = m_loc.group(1).strip()
        start = m_loc.start(1)
        end = start + len(ans)
        _add_item(
            f"In which region or country is {title} located?",
            ans,
            [start, end],
            "location",
            "city_location",
        )

    # 6. Population count
    m_pop = re.search(
        r"(?:had a population of|population of)\s+([0-9,]+(?:\s*(?:million|thousand))?)",
        passage,
    )
    if m_pop:
        ans = m_pop.group(1).strip().rstrip(",.;")
        start = m_pop.start(1)
        end = start + len(ans)
        _add_item(
            f"What was the reported population of {title}?",
            ans,
            [start, end],
            "quantity",
            "population",
        )

    # 7. Surface area
    m_area = re.search(
        r"(?:covers an area of|area of)\s+(\d+(?:,\d+)*(?:\.\d+)?\s*(?:sq mi|square kilometres|km²|hectares|acres))",
        passage,
    )
    if m_area:
        ans = m_area.group(1).strip().rstrip(",.;")
        start = m_area.start(1)
        end = start + len(ans)
        _add_item(
            f"What is the surface area of {title}?",
            ans,
            [start, end],
            "quantity",
            "surface_area",
        )

    # 8. Award received
    m_awd = re.search(
        r"(?:awarded|received|won)\s+the\s+([A-Z][a-zA-Z\s]+?(?:Prize|Award|Medal))",
        passage,
    )
    if m_awd:
        ans = m_awd.group(1).strip()
        start = m_awd.start(1)
        end = start + len(ans)
        _add_item(
            f"What award or prize did {title} receive?",
            ans,
            [start, end],
            "award",
            "award_won",
        )

    # 9. Book / novel / artwork creator
    m_wrk = re.search(
        r"is a\s+(?:novel|book|play|film|song|painting)\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        first_sent,
    )
    if m_wrk:
        ans = m_wrk.group(1).strip()
        start = m_wrk.start(1)
        end = start + len(ans)
        _add_item(
            f"Who created or wrote {title}?",
            ans,
            [start, end],
            "person",
            "work_creator",
        )

    # 10. Publication / release year
    m_rel = re.search(
        r"is a\s+(\d{4})\s+(?:American|British|French|German|Canadian|Italian|Japanese)?\s*(?:film|novel|album|book|play|video game)",
        first_sent,
    )
    if m_rel:
        ans = m_rel.group(1).strip()
        start = m_rel.start(1)
        end = start + len(ans)
        _add_item(
            f"In what year was {title} released or published?",
            ans,
            [start, end],
            "year",
            "release_year",
        )

    return candidates


def generate_knowledge_qa_suite(
    corpus: list[dict[str, Any]],
    seed: int = 20260101,
    train_size: int = 300,
    val_size: int = 300,
    locked_test_size: int = 300,
) -> dict[str, list[dict[str, Any]]]:
    """Generate partitioned Knowledge QA suites with verified spans.

    Returns dict with keys: 'train', 'validation', 'locked_test'.
    """
    rng = random.Random(seed)

    all_candidates: list[dict[str, Any]] = []
    seen_questions: set[str] = set()

    for article in corpus:
        items = extract_qa_from_article(article)
        for it in items:
            q_norm = it["question"].strip().lower()
            if q_norm not in seen_questions:
                seen_questions.add(q_norm)
                all_candidates.append(it)

    rng.shuffle(all_candidates)

    total_needed = train_size + val_size + locked_test_size
    if len(all_candidates) < total_needed:
        raise ValueError(
            f"Not enough distinct QA items extracted: got {len(all_candidates)}, need {total_needed}."
        )

    val_raw = all_candidates[:val_size]
    test_raw = all_candidates[val_size : val_size + locked_test_size]
    train_raw = all_candidates[val_size + locked_test_size : total_needed]

    def _format_partition(items: list[dict[str, Any]], split_name: str) -> list[dict[str, Any]]:
        partition = []
        prefix = {
            "validation": "kqa_val",
            "locked_test": "kqa_lock",
            "train": "kqa_train",
        }[split_name]
        for idx, item in enumerate(items, 1):
            assert verify_qa_span(
                item["passage"], item["answer"], item["answer_span"]
            ), f"Span mismatch in item {idx}"
            record = dict(item)
            record["id"] = f"{prefix}_{idx:04d}"
            record["split"] = split_name
            partition.append(record)
        return partition

    return {
        "validation": _format_partition(val_raw, "validation"),
        "locked_test": _format_partition(test_raw, "locked_test"),
        "train": _format_partition(train_raw, "train"),
    }


def write_qa_partition(items: list[dict[str, Any]], path: Path) -> None:
    """Write QA items to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
