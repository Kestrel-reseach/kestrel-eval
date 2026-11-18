"""Official public source registry and license provenance for Project Kestrel.

Every public source must record:
- name: Official dataset name
- version: Exact version or commit used
- url: Official canonical URL (homepage or primary repo)
- license: License string verified from official page (or 'UNVERIFIED')
- license_url: Official license document URL
- verified_on_official_page: True if verified directly from project homepage
- contamination_risk: Assessment of whether items appear in public LLM training sets
- permissible: True if license permits download, modification, and evaluation use
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceMetadata:
    name: str
    group: str
    version: str
    url: str
    license: str
    license_url: str
    verified_on_official_page: bool
    permissible: bool
    contamination_risk: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "group": self.group,
            "version": self.version,
            "url": self.url,
            "license": self.license,
            "license_url": self.license_url,
            "verified_on_official_page": self.verified_on_official_page,
            "permissible": self.permissible,
            "contamination_risk": self.contamination_risk,
            "notes": self.notes,
        }


PUBLIC_SOURCES: dict[str, SourceMetadata] = {
    "gsm8k": SourceMetadata(
        name="GSM8K (Grade School Math 8K)",
        group="math",
        version="1.0",
        url="https://github.com/openai/grade-school-math",
        license="MIT",
        license_url="https://github.com/openai/grade-school-math/blob/master/LICENSE",
        verified_on_official_page=True,
        permissible=True,
        contamination_risk="HIGH (Widely included in web-scraped LLM pretraining data after 2021)",
        notes="8.5k grade school math word problems with numeric answers. Checkable via exact_numeric.",
    ),
    "arc_challenge": SourceMetadata(
        name="AI2 Reasoning Challenge (ARC-Challenge)",
        group="science_mcq",
        version="1.0 (Feb 2018)",
        url="https://allenai.org/data/arc",
        license="CC BY-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
        verified_on_official_page=True,
        permissible=True,
        contamination_risk="HIGH (Present in common pretraining corpora and eval benchmarks)",
        notes="Grade 3-9 science multiple choice questions requiring reasoning. 4 choices (A-D).",
    ),
    "mmlu": SourceMetadata(
        name="MMLU (Measuring Massive Multitask Language Understanding)",
        group="knowledge_mcq",
        version="1.0",
        url="https://github.com/hendrycks/test",
        license="MIT",
        license_url="https://github.com/hendrycks/test/blob/master/LICENSE",
        verified_on_official_page=True,
        permissible=True,
        contamination_risk="HIGH (Standard LLM benchmark since 2020; likely in web corpora)",
        notes="10 representative subjects selected: college_computer_science, college_physics, "
        "college_biology, college_chemistry, elementary_mathematics, high_school_world_history, "
        "high_school_geography, professional_law, clinical_knowledge, econometrics.",
    ),
    "humaneval": SourceMetadata(
        name="HumanEval",
        group="code",
        version="1.0",
        url="https://github.com/openai/human-eval",
        license="MIT",
        license_url="https://github.com/openai/human-eval/blob/master/LICENSE",
        verified_on_official_page=True,
        permissible=True,
        contamination_risk="CRITICAL (Extensively memorized by code LLMs since 2021; small N=164)",
        notes="Dataset too small (164 items) and heavily contaminated. Per instructions, "
        "privately written synthetic tasks are proposed to augment/replace for locked testing.",
    ),
    "mbpp": SourceMetadata(
        name="MBPP (Mostly Basic Python Problems)",
        group="code",
        version="1.0",
        url="https://github.com/google-research/google-research/tree/master/mbpp",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        verified_on_official_page=True,
        permissible=True,
        contamination_risk="HIGH (Frequently scraped and part of code benchmark mixtures)",
        notes="974 Python tasks with assertions. Per instructions, synthetic private code "
        "tasks are recommended for the locked partition to guarantee zero leakage.",
    ),
}


def get_source_metadata(source_key: str) -> SourceMetadata:
    """Return verified metadata for a public source, or raise KeyError."""
    if source_key not in PUBLIC_SOURCES:
        raise KeyError(
            f"Unknown source {source_key!r}. Registered sources: {list(PUBLIC_SOURCES.keys())}"
        )
    return PUBLIC_SOURCES[source_key]
