"""Wikipedia abstract extraction module for Project Kestrel (Step 1).

Extracts clean lead abstracts from official English Wikipedia XML dumps (.xml.bz2).
Handles wikitext stripping, template removal, reference removal, and sentence boundary
alignment to produce clean factual passage corpora for Knowledge QA evaluation.
"""

from __future__ import annotations

import bz2
import json
import logging
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def clean_wikitext(text: str) -> str:
    """Clean Wikipedia wikitext to produce a clean plain-text abstract.

    Strips:
    - HTML/XML comments (<!-- ... -->)
    - Reference tags (<ref>...</ref> and <ref ... />)
    - Other HTML tags
    - Wikitables ({| ... |})
    - Templates ({{ ... }})
    - Media/File links ([[File:...]], [[Image:...]])
    - Internal wikilinks ([[Target|Anchor]] -> Anchor, [[Target]] -> Target)
    - External links ([http... text] -> text)
    - Bold and italic markup (''', '')
    - Bulleted lists and section headers
    """
    if not text:
        return ""

    # Cut off at first section header if present (lead section only)
    sections = re.split(r"\n==+\s*[^=]+==+", text, maxsplit=1)
    lead = sections[0]

    # Remove comments
    lead = re.sub(r"<!--.*?-->", "", lead, flags=re.DOTALL)

    # Remove ref tags and other tags
    lead = re.sub(r"<ref[^>]*>.*?</ref>", "", lead, flags=re.DOTALL)
    lead = re.sub(r"<ref[^>]*/>", "", lead)
    lead = re.sub(r"<[^>]+>", "", lead)

    # Remove wikitables {| ... |}
    lead = re.sub(r"\{\|.*?\|\}", "", lead, flags=re.DOTALL)

    # Iteratively strip templates {{ ... }} to handle nested structures
    for _ in range(6):
        lead = re.sub(r"\{\{[^{}]*\}\}", "", lead, flags=re.DOTALL)

    # Remove File: and Image: links
    lead = re.sub(r"\[\[(?:File|Image):[^\]]+\]\]", "", lead, flags=re.IGNORECASE)

    # Convert [[Target|Anchor]] -> Anchor and [[Target]] -> Target
    lead = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", lead)

    # Convert [http... Anchor] -> Anchor and bare URLs to empty
    lead = re.sub(r"\[https?://[^\s\]]+\s+([^\]]+)\]", r"\1", lead)
    lead = re.sub(r"\[https?://[^\s\]]+\]", "", lead)

    # Remove bold/italic quotes (''' or '')
    lead = re.sub(r"'{2,5}", "", lead)

    # Strip bullet / list lines
    lines = [
        line.strip()
        for line in lead.split("\n")
        if line.strip() and not line.strip().startswith(("*", "#", ";", ":", "|"))
    ]
    cleaned = " ".join(lines)

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Ensure abstract ends at a valid sentence boundary
    if cleaned and not cleaned.endswith((".", "!", "?")):
        # Truncate at last sentence boundary if available
        last_period = max(cleaned.rfind(". "), cleaned.rfind("! "), cleaned.rfind("? "))
        if last_period > 100:
            cleaned = cleaned[: last_period + 1].strip()

    return cleaned


def iter_wikipedia_articles(dump_path: Path) -> Iterator[dict[str, Any]]:
    """Stream articles from an English Wikipedia XML dump (.xml.bz2).

    Yields dicts with:
      page_id: int
      title: str
      raw_text: str
    """
    with bz2.open(dump_path, "rb") as f:
        # iterparse stream to keep memory O(1)
        context = ET.iterparse(f, events=("end",))
        for _, elem in context:
            if elem.tag.endswith("page"):
                ns = elem.find("{*}ns")
                redirect = elem.find("{*}redirect")
                title_elem = elem.find("{*}title")
                id_elem = elem.find("{*}id")
                text_elem = elem.find(".//{*}text")

                # Namespace 0 is encyclopedia articles; skip redirects & meta
                if (
                    ns is not None
                    and ns.text == "0"
                    and redirect is None
                    and title_elem is not None
                    and title_elem.text
                    and text_elem is not None
                    and text_elem.text
                ):
                    title = title_elem.text.strip()
                    raw_text = text_elem.text

                    # Skip disambiguation, list pages, and redirect wikitext
                    is_disambig = (
                        "{{disambiguation" in raw_text.lower() or "{{disambig" in raw_text.lower()
                    )
                    is_list = title.startswith("List of ") or "disambiguation" in title.lower()
                    is_redirect_text = raw_text.strip().upper().startswith("#REDIRECT")

                    if not (is_disambig or is_list or is_redirect_text):
                        yield {
                            "page_id": int(id_elem.text)
                            if id_elem is not None and id_elem.text
                            else 0,
                            "title": title,
                            "raw_text": raw_text,
                        }
                elem.clear()


def extract_abstract_corpus(
    dump_path: Path,
    output_path: Path | None = None,
    target_count: int = 5000,
    min_chars: int = 180,
    max_chars: int = 1500,
) -> list[dict[str, Any]]:
    """Extract target_count clean article abstracts from a Wikipedia dump.

    Each item has:
      article_id: str (e.g. 'wiki_art_00001')
      page_id: int
      title: str
      abstract: str
      char_count: int
      word_count: int
    """
    corpus: list[dict[str, Any]] = []

    for article in iter_wikipedia_articles(dump_path):
        cleaned = clean_wikitext(article["raw_text"])
        if len(cleaned) < min_chars:
            continue

        # Truncate overly long abstracts to max_chars at a sentence boundary
        if len(cleaned) > max_chars:
            cutoff = cleaned[:max_chars].rfind(". ")
            if cutoff > min_chars:
                cleaned = cleaned[: cutoff + 1].strip()
            else:
                cleaned = cleaned[:max_chars].strip()

        article_id = f"wiki_art_{len(corpus) + 1:05d}"
        item = {
            "article_id": article_id,
            "page_id": article["page_id"],
            "title": article["title"],
            "abstract": cleaned,
            "char_count": len(cleaned),
            "word_count": len(cleaned.split()),
        }
        corpus.append(item)

        if len(corpus) >= target_count:
            break

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for item in corpus:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return corpus
