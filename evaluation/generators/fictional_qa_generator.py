"""Fictional-entity Knowledge QA generator for Project Kestrel (Decision D13/D14).

Generates pure, uncontaminated fictional entities with consistent factual attributes:
- Persona entities: born date, death date, profession, award won.
- Realm / City entities: population, founding year.
All names and entities are strictly verified to have 0% collision with the Wikipedia snapshot.
Passages are exported to data/fictional_abstracts_corpus.jsonl and included in BM25 retrieval.
Every item has verified character span offsets [start, end] where passage[start:end] == target.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.loaders.common import SuiteItem

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# 35 completely invented unique public personas (25 validation + 10 train) with zero Wikipedia collision
# Note: The 25 retired locked personas that appeared in v1 git history were fully retired per Decision D17.
PERSONAS_DATA = [
    (
        "Alastair Ravenswood",
        "26 September 1850",
        "9 June 1923",
        "geologist",
        "Strata Discovery Ribbon",
    ),
    ("Callista Ironwood", "14 April 1869", "3 October 1941", "poet", "Laureate Laurel Wreath"),
    ("Damian Windward", "19 June 1838", "12 December 1911", "engineer", "Bessemer Steam Medallion"),
    ("Fiona Bramblewood", "31 January 1887", "18 May 1964", "painter", "Spectrum Society Award"),
    ("Tiberius Stone", "24 November 1846", "7 July 1920", "mathematician", "Golden Ratio Medal"),
    (
        "Gwendolyn Crane",
        "11 February 1864",
        "19 August 1938",
        "physician",
        "Hippocratic Seal of Honor",
    ),
    ("Roderick Vance", "5 October 1857", "22 April 1927", "historian", "Archival Pioneer Plaque"),
    ("Selene Vesper", "18 June 1875", "10 November 1946", "novelist", "Silver Inkwell Prize"),
    ("Crispin Holloway", "27 March 1849", "14 January 1924", "sculptor", "Marble Form Laureate"),
    ("Amara Valmont", "9 September 1881", "26 July 1955", "diplomat", "Golden Envoy Medal"),
    ("Ignatius Drake", "22 December 1837", "5 May 1910", "philosopher", "Stoic Dialectic Ribbon"),
    ("Ophelia Bracken", "14 August 1873", "30 March 1945", "botanist", "Flora Regalis Trophy"),
    (
        "Cedric Falconbridge",
        "8 November 1852",
        "17 October 1925",
        "architect",
        "Spire Master Distinction",
    ),
    (
        "Theodora Finch",
        "3 May 1884",
        "12 September 1958",
        "astronomer",
        "Starlight Cartography Award",
    ),
    (
        "Percival Thornwood",
        "19 January 1841",
        "28 June 1913",
        "statesman",
        "Crown Service Medallion",
    ),
    ("Beatrix Solarium", "7 July 1877", "16 December 1950", "chemist", "Catalyst Laurel Prize"),
    ("Orion Blackwood", "16 October 1861", "9 February 1933", "composer", "Polyphony Gold Medal"),
    ("Linnea Moss", "24 April 1888", "31 May 1963", "biologist", "Naturalist Guild Crest"),
    (
        "Victor Sterling",
        "2 September 1847",
        "18 November 1919",
        "geologist",
        "Bedrock Survey Ribbon",
    ),
    ("Diana Hawthorne", "13 December 1870", "24 April 1944", "poet", "Verse Excellence Award"),
    ("Horatio Pendelton", "28 May 1854", "11 March 1928", "mathematician", "Axiom Society Cup"),
    (
        "Sibyl Nightshade",
        "6 October 1886",
        "23 January 1961",
        "physicist",
        "Resonance Physics Medal",
    ),
    ("Arthur Ravenscroft", "17 March 1843", "5 August 1916", "engineer", "Foundry Guild Trophy"),
    (
        "Cassandra Cross",
        "25 November 1872",
        "19 September 1948",
        "painter",
        "Canvas Master Distinction",
    ),
    ("Leopold Frost", "10 April 1856", "27 December 1930", "historian", "Past Epochs Medallion"),
    ("Eulalia Moon", "1 August 1880", "15 October 1954", "physician", "Healer Civic Star"),
    ("Julian Stormont", "20 February 1839", "8 July 1912", "novelist", "Grand Folio Laureate"),
    (
        "Rosalind Ironwood",
        "12 June 1867",
        "3 February 1940",
        "botanist",
        "Herbarium Fellowship Order",
    ),
    ("Tristan Emberfell", "29 September 1859", "16 May 1932", "diplomat", "Treaty Master Cross"),
    ("Lavinia Voss", "4 May 1883", "22 November 1957", "philosopher", "Sophia Guild Medallion"),
    (
        "Felix Bramblewood",
        "15 January 1848",
        "30 September 1922",
        "architect",
        "Pillar of Archon Trophy",
    ),
    ("Vivienne Drake", "23 October 1874", "11 June 1949", "chemist", "Distillation Gold Crest"),
    ("Roland Silverton", "8 August 1850", "24 April 1925", "astronomer", "Zenith Observers Ribbon"),
    ("Genevieve Thorne", "19 July 1885", "7 March 1962", "composer", "Grand Operatic Star"),
    (
        "Alaric Morvath",
        "30 November 1842",
        "14 December 1915",
        "sculptor",
        "Bas-Relief Guild Medal",
    ),
]

# 30 completely invented unique cities / boroughs with zero Wikipedia collision
CITIES_DATA = [
    ("Oakhaven Metropolis", "528,490", "1742"),
    ("Solaria Haven", "184,320", "1815"),
    ("Lunaris Citadel", "94,150", "1688"),
    ("Verdantia Borough", "312,800", "1794"),
    ("Astrid Bay", "467,200", "1850"),
    ("Eldoria Province", "825,600", "1720"),
    ("Ironcrest Harbor", "219,500", "1832"),
    ("Silverpeak Valley", "143,890", "1765"),
    ("Bramblewood Glen", "76,400", "1804"),
    ("Corvus Reach", "389,120", "1782"),
    ("Duskwood Port", "254,700", "1861"),
    ("Thornfield Settlement", "118,650", "1735"),
    ("Zephyr Point", "198,340", "1845"),
    ("Frostpeak Ridge", "87,210", "1776"),
    ("Ravenholm Guild", "64,500", "1695"),
    ("Amberdale Municipality", "275,400", "1822"),
    ("Starfall Township", "132,900", "1750"),
    ("Crestview Canton", "410,600", "1808"),
    ("Mistwood Borough", "98,750", "1715"),
    ("Sunspire Enclave", "345,100", "1839"),
    ("Galehaven City", "512,800", "1768"),
    ("Highland Keep", "81,200", "1675"),
    ("Riverbend Township", "167,450", "1812"),
    ("Shadowmere Port", "230,900", "1855"),
    ("Stoneford Valley", "124,300", "1748"),
    ("Windward Reach", "289,600", "1828"),
    ("Valeska Settlement", "154,200", "1785"),
    ("Opal Coast Borough", "378,500", "1842"),
    ("Nightfall Harbor", "192,800", "1798"),
    ("Ironclad Bastion", "69,400", "1704"),
]


def generate_fictional_corpus_and_qa_items() -> tuple[list[dict[str, Any]], list[SuiteItem]]:
    """Generate the public fictional abstract corpus (65 articles) and 200 verified public QA items (100 val + 100 train)."""
    corpus: list[dict[str, Any]] = []
    all_qa_items: list[SuiteItem] = []
    item_counter = 1

    # 1. Process 35 Public Personas (4 items each -> 140 items: 100 val + 40 train)
    # Starts at index 26 to preserve exact stable passage IDs for validation and train
    for p_idx, (name, b_date, d_date, prof, award) in enumerate(PERSONAS_DATA, 26):
        art_id = f"fictional_art_p_{p_idx:04d}"
        abstract = (
            f"{name} ({b_date} – {d_date}) was a renowned {prof}. "
            f"Over a distinguished career, {name} made notable contributions to the field. "
            f"In recognition of these achievements, {name} received the prestigious {award}."
        )
        corpus.append(
            {
                "article_id": art_id,
                "title": name,
                "abstract": abstract,
                "is_fictional": True,
            }
        )

        # Q1: born_date
        b_start = abstract.find(b_date)
        b_span = [b_start, b_start + len(b_date)]
        assert abstract[b_span[0] : b_span[1]] == b_date
        all_qa_items.append(
            SuiteItem(
                item_id=f"kqa_fict_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"When was {name} born?",
                target=b_date,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="born_date",
                metadata={
                    "source": "fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": b_span,
                    "rule_family": "born_date",
                    "template_family": "born_date",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

        # Q2: death_date
        d_start = abstract.find(d_date)
        d_span = [d_start, d_start + len(d_date)]
        assert abstract[d_span[0] : d_span[1]] == d_date
        all_qa_items.append(
            SuiteItem(
                item_id=f"kqa_fict_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"When did {name} die?",
                target=d_date,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="death_date",
                metadata={
                    "source": "fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": d_span,
                    "rule_family": "death_date",
                    "template_family": "death_date",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

        # Q3: profession
        p_start = abstract.find(prof)
        p_span = [p_start, p_start + len(prof)]
        assert abstract[p_span[0] : p_span[1]] == prof
        all_qa_items.append(
            SuiteItem(
                item_id=f"kqa_fict_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"What was the profession or occupation of {name}?",
                target=prof,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="profession",
                metadata={
                    "source": "fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": p_span,
                    "rule_family": "profession",
                    "template_family": "profession",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

        # Q4: award_won
        a_start = abstract.find(award)
        a_span = [a_start, a_start + len(award)]
        assert abstract[a_span[0] : a_span[1]] == award
        all_qa_items.append(
            SuiteItem(
                item_id=f"kqa_fict_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"What award or prize did {name} receive?",
                target=award,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="award_won",
                metadata={
                    "source": "fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": a_span,
                    "rule_family": "award_won",
                    "template_family": "award_won",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

    # 2. Process 30 Public Cities (2 items each -> 60 items in train)
    for c_idx, (city_name, pop, year) in enumerate(CITIES_DATA, 1):
        art_id = f"fictional_art_c_{c_idx:04d}"
        abstract = (
            f"{city_name} is a historic coastal settlement founded in {year}. "
            f"According to administrative survey records, the reported population was {pop} residents."
        )
        corpus.append(
            {
                "article_id": art_id,
                "title": city_name,
                "abstract": abstract,
                "is_fictional": True,
            }
        )

        # Q1: population
        pop_start = abstract.find(pop)
        pop_span = [pop_start, pop_start + len(pop)]
        assert abstract[pop_span[0] : pop_span[1]] == pop
        all_qa_items.append(
            SuiteItem(
                item_id=f"kqa_fict_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"What was the reported population of {city_name}?",
                target=pop,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="population",
                metadata={
                    "source": "fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": city_name,
                    "passage": abstract,
                    "answer_span": pop_span,
                    "rule_family": "population",
                    "template_family": "population",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

        # Q2: founding_year
        yr_start = abstract.find(year)
        yr_span = [yr_start, yr_start + len(year)]
        assert abstract[yr_span[0] : yr_span[1]] == year
        all_qa_items.append(
            SuiteItem(
                item_id=f"kqa_fict_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"In what year was {city_name} founded?",
                target=year,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="founding_year",
                metadata={
                    "source": "fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": city_name,
                    "passage": abstract,
                    "answer_span": yr_span,
                    "rule_family": "founding_year",
                    "template_family": "founding_year",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

    assert len(all_qa_items) == 200, f"Expected 200 fictional items, got {len(all_qa_items)}"
    return corpus, all_qa_items


def generate_fictional_locked_items(
    private_personas: list[Any],
) -> tuple[list[dict[str, Any]], list[SuiteItem]]:
    """Generate the private locked fictional abstract corpus (25 articles) and 100 verified locked QA items."""
    corpus: list[dict[str, Any]] = []
    locked_items: list[SuiteItem] = []
    item_counter = 1

    for p_idx, p_data in enumerate(private_personas, 1):
        name, b_date, d_date, prof, award = p_data[0], p_data[1], p_data[2], p_data[3], p_data[4]
        art_id = f"fictional_locked_art_p_{p_idx:04d}"
        abstract = (
            f"{name} ({b_date} – {d_date}) was a renowned {prof}. "
            f"Over a distinguished career, {name} made notable contributions to the field. "
            f"In recognition of these achievements, {name} received the prestigious {award}."
        )
        corpus.append(
            {
                "article_id": art_id,
                "title": name,
                "abstract": abstract,
                "is_fictional": True,
            }
        )

        b_start = abstract.find(b_date)
        b_span = [b_start, b_start + len(b_date)]
        assert abstract[b_span[0] : b_span[1]] == b_date
        locked_items.append(
            SuiteItem(
                item_id=f"kqa_fict_lock_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"When was {name} born?",
                target=b_date,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="born_date",
                metadata={
                    "source": "private_fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": b_span,
                    "rule_family": "born_date",
                    "template_family": "born_date",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

        d_start = abstract.find(d_date)
        d_span = [d_start, d_start + len(d_date)]
        assert abstract[d_span[0] : d_span[1]] == d_date
        locked_items.append(
            SuiteItem(
                item_id=f"kqa_fict_lock_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"When did {name} die?",
                target=d_date,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="death_date",
                metadata={
                    "source": "private_fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": d_span,
                    "rule_family": "death_date",
                    "template_family": "death_date",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

        p_start = abstract.find(prof)
        p_span = [p_start, p_start + len(prof)]
        assert abstract[p_span[0] : p_span[1]] == prof
        locked_items.append(
            SuiteItem(
                item_id=f"kqa_fict_lock_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"What was the profession or occupation of {name}?",
                target=prof,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="profession",
                metadata={
                    "source": "private_fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": p_span,
                    "rule_family": "profession",
                    "template_family": "profession",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

        a_start = abstract.find(award)
        a_span = [a_start, a_start + len(award)]
        assert abstract[a_span[0] : a_span[1]] == award
        locked_items.append(
            SuiteItem(
                item_id=f"kqa_fict_lock_{item_counter:04d}",
                group="knowledge_qa",
                prompt=f"What award or prize did {name} receive?",
                target=award,
                answer_check="normalized_exact_match",
                choices=None,
                arm="fictional_entity",
                template_family="award_won",
                metadata={
                    "source": "private_fictional_entity_generator",
                    "passage_id": art_id,
                    "passage_title": name,
                    "passage": abstract,
                    "answer_span": a_span,
                    "rule_family": "award_won",
                    "template_family": "award_won",
                    "arm": "fictional_entity",
                    "is_fictional": True,
                },
            )
        )
        item_counter += 1

    assert len(locked_items) == 100, f"Expected 100 locked fictional items, got {len(locked_items)}"
    return corpus, locked_items


def save_fictional_corpus(
    output_path: Path | None = None,
) -> tuple[Path, list[dict[str, Any]], list[SuiteItem]]:
    """Save the fictional abstract corpus to JSONL and return (path, corpus, items)."""
    if output_path is None:
        output_path = REPO_ROOT / "data" / "fictional_abstracts_corpus.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    corpus, qa_items = generate_fictional_corpus_and_qa_items()
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in corpus:
            f.write(json.dumps(doc) + "\n")

    return output_path, corpus, qa_items
