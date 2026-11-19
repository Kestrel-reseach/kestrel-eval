"""Suite builder, hasher, and partition manager for Project Kestrel (Step 1).

Implements:
1. Generation and stratification of all 6 groups across train, validation, and locked-test
   per Decision D1 (200/200/300/100/300/100 items per partition, 1200 per partition, 3600 total).
2. Deterministic hashing: SHA-256 per partition file and root hash across locked-test files.
3. Strict out-of-repo routing for locked-test data (stored in KESTREL_PRIVATE_DIR; only hashes committed).
4. Automated leakage verification prior to writing: 100% zero ID overlap and zero duplicate prompts.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

from evaluation.generators.code_generator import generate_code_suite
from evaluation.generators.knowledge_mcq_generator import generate_knowledge_mcq_suite
from evaluation.generators.knowledge_qa_generator import generate_knowledge_qa_suite
from evaluation.generators.math_generator import generate_math_suite
from evaluation.generators.memory_probe_generator import generate_memory_probe_suite
from evaluation.generators.science_mcq_generator import generate_science_mcq_suite
from evaluation.generators.wiki_extractor import extract_abstract_corpus
from evaluation.leakage import (
    check_answer_leakage,
    check_exact_prompt_duplicates,
    check_no_id_overlap,
)

logger = logging.getLogger(__name__)

GROUPS = (
    "math",
    "science_mcq",
    "knowledge_mcq",
    "code",
    "knowledge_qa",
    "memory_probe",
)

GROUP_SIZES = {
    "math": 200,
    "science_mcq": 200,
    "knowledge_mcq": 300,
    "code": 100,
    "knowledge_qa": 300,
    "memory_probe": 150,  # expanded per D16 (100 stale + 50 static items)
}


def compute_sha256(data: bytes | str) -> str:
    """Compute SHA-256 hex digest of bytes or string."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file on disk."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_root_hash(partition_hashes: dict[str, str]) -> str:
    """Compute root hash as SHA-256 over sorted group hashes."""
    sorted_items = sorted(partition_hashes.items())
    payload = "\n".join(f"{k}:{v}" for k, v in sorted_items)
    return compute_sha256(payload)


def get_private_dir(create: bool = False) -> Path:
    """Return destination directory for locked-test partitions.

    Must reside outside git repository per project rules.
    Reads KESTREL_PRIVATE_DIR or defaults to workspace sibling kestrel_private.
    """
    env_dir = os.environ.get("KESTREL_PRIVATE_DIR")
    if env_dir:
        dest = Path(env_dir).resolve()
    else:
        repo_root = Path(__file__).resolve().parent.parent
        dest = (repo_root.parent / "kestrel_private").resolve()
    if create:
        try:
            dest.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return dest


def _reprefix_items(items: Sequence[Any], prefix: str, split: str) -> list[dict[str, Any]]:
    """Format items with canonical partition ID prefix and split field."""
    formatted = []
    for idx, raw in enumerate(items, 1):
        it = dict(raw)
        it["id"] = f"{prefix}_{idx:04d}"
        it["split"] = split
        formatted.append(it)
    return formatted


def build_suite_partitions(
    base_seed: int = 20260101,
    dump_path: Path | None = None,
    abstracts_corpus_path: Path | None = None,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Build all 6 groups across train, validation, and locked-test partitions.

    Returns:
      {
        'validation': {'math': [...], 'science_mcq': [...], ...},
        'locked_test': {'math': [...], ...},
        'train': {'math': [...], ...},
      }
    """
    logger.info("Building evaluation suite (Decision D1)...")
    global_seen_prompts: set[str] = set()

    # 1. Math (200 / 200 / 200)
    math_val = _reprefix_items(
        generate_math_suite(
            n_items=GROUP_SIZES["math"], seed=base_seed + 1, seen_prompts=global_seen_prompts
        ),
        prefix="math_val",
        split="validation",
    )
    math_lock = _reprefix_items(
        generate_math_suite(
            n_items=GROUP_SIZES["math"], seed=base_seed + 2, seen_prompts=global_seen_prompts
        ),
        prefix="math_lock",
        split="locked_test",
    )
    math_train = _reprefix_items(
        generate_math_suite(
            n_items=GROUP_SIZES["math"], seed=base_seed + 3, seen_prompts=global_seen_prompts
        ),
        prefix="math_train",
        split="train",
    )

    # 2. Science MCQ (200 / 200 / 200)
    sci_val = generate_science_mcq_suite(
        count=GROUP_SIZES["science_mcq"],
        seed=base_seed + 10,
        prefix="sci_val",
        split="validation",
        seen_prompts=global_seen_prompts,
    )
    sci_lock = generate_science_mcq_suite(
        count=GROUP_SIZES["science_mcq"],
        seed=base_seed + 11,
        prefix="sci_lock",
        split="locked_test",
        seen_prompts=global_seen_prompts,
    )
    sci_train = generate_science_mcq_suite(
        count=GROUP_SIZES["science_mcq"],
        seed=base_seed + 12,
        prefix="sci_train",
        split="train",
        seen_prompts=global_seen_prompts,
    )

    # 3. Knowledge MCQ (300 / 300 / 300; 30 items x 10 subjects)
    know_val = generate_knowledge_mcq_suite(
        items_per_subject=30,
        seed=base_seed + 20,
        prefix="know_val",
        split="validation",
        seen_prompts=global_seen_prompts,
    )
    know_lock = generate_knowledge_mcq_suite(
        items_per_subject=30,
        seed=base_seed + 21,
        prefix="know_lock",
        split="locked_test",
        seen_prompts=global_seen_prompts,
    )
    know_train = generate_knowledge_mcq_suite(
        items_per_subject=30,
        seed=base_seed + 22,
        prefix="know_train",
        split="train",
        seen_prompts=global_seen_prompts,
    )

    # 4. Code (100 / 100 / 100)
    code_val = _reprefix_items(
        generate_code_suite(
            n_items=GROUP_SIZES["code"], seed=base_seed + 30, seen_prompts=global_seen_prompts
        ),
        prefix="code_val",
        split="validation",
    )
    code_lock = _reprefix_items(
        generate_code_suite(
            n_items=GROUP_SIZES["code"], seed=base_seed + 31, seen_prompts=global_seen_prompts
        ),
        prefix="code_lock",
        split="locked_test",
    )
    code_train = _reprefix_items(
        generate_code_suite(
            n_items=GROUP_SIZES["code"], seed=base_seed + 32, seen_prompts=global_seen_prompts
        ),
        prefix="code_train",
        split="train",
    )

    # 5. Knowledge QA from Wikipedia (300 / 300 / 300)
    corpus: list[dict[str, Any]] = []
    if abstracts_corpus_path and abstracts_corpus_path.exists():
        with open(abstracts_corpus_path, encoding="utf-8") as f:
            for line in f:
                corpus.append(json.loads(line))
    elif dump_path and dump_path.exists():
        corpus = extract_abstract_corpus(dump_path, target_count=6000)
    else:
        default_p = Path("data/wikipedia_abstracts_5k.jsonl")
        if default_p.exists():
            with open(default_p, encoding="utf-8") as f:
                for line in f:
                    corpus.append(json.loads(line))
        else:
            raise FileNotFoundError(
                "Wikipedia abstracts corpus not found. Run extract_abstract_corpus first."
            )

    kqa_partitions = generate_knowledge_qa_suite(
        corpus=corpus,
        seed=base_seed + 40,
        train_size=GROUP_SIZES["knowledge_qa"],
        val_size=GROUP_SIZES["knowledge_qa"],
        locked_test_size=GROUP_SIZES["knowledge_qa"],
    )

    # 6. Memory probe (100 / 100 / 100, 30 stale-fact each)
    mem_val = _reprefix_items(
        generate_memory_probe_suite(
            n_items=GROUP_SIZES["memory_probe"],
            stale_fact_count=30,
            seed=base_seed + 50,
            seen_prompts=global_seen_prompts,
        ),
        prefix="mem_val",
        split="validation",
    )
    mem_lock = _reprefix_items(
        generate_memory_probe_suite(
            n_items=GROUP_SIZES["memory_probe"],
            stale_fact_count=30,
            seed=base_seed + 51,
            seen_prompts=global_seen_prompts,
        ),
        prefix="mem_lock",
        split="locked_test",
    )
    mem_train = _reprefix_items(
        generate_memory_probe_suite(
            n_items=GROUP_SIZES["memory_probe"],
            stale_fact_count=30,
            seed=base_seed + 52,
            seen_prompts=global_seen_prompts,
        ),
        prefix="mem_train",
        split="train",
    )

    partitions: dict[str, dict[str, list[dict[str, Any]]]] = {
        "validation": {
            "math": math_val,
            "science_mcq": sci_val,
            "knowledge_mcq": know_val,
            "code": code_val,
            "knowledge_qa": kqa_partitions["validation"],
            "memory_probe": mem_val,
        },
        "locked_test": {
            "math": math_lock,
            "science_mcq": sci_lock,
            "knowledge_mcq": know_lock,
            "code": code_lock,
            "knowledge_qa": kqa_partitions["locked_test"],
            "memory_probe": mem_lock,
        },
        "train": {
            "math": math_train,
            "science_mcq": sci_train,
            "knowledge_mcq": know_train,
            "code": code_train,
            "knowledge_qa": kqa_partitions["train"],
            "memory_probe": mem_train,
        },
    }

    # Flatten for leakage check
    flat_partitions = {
        split_name: [it for grp in groups.values() for it in grp]
        for split_name, groups in partitions.items()
    }

    check_no_id_overlap(flat_partitions)
    exact_dups = check_exact_prompt_duplicates(flat_partitions)
    if exact_dups:
        raise ValueError(
            f"Partition leakage violation: found {len(exact_dups)} duplicate prompts across partitions: {exact_dups[:3]}"
        )

    for s_name, itms in flat_partitions.items():
        ans_leaks = check_answer_leakage(itms)
        if ans_leaks:
            logger.warning(
                "Found %d potential answer leaks in %s: %s",
                len(ans_leaks),
                s_name,
                ans_leaks[:3],
            )

    return partitions


def write_suite_files(
    partitions: dict[str, dict[str, list[dict[str, Any]]]],
    repo_root: Path,
) -> dict[str, Any]:
    """Write validation & train to repo, and locked_test to KESTREL_PRIVATE_DIR.

    Returns dict with file hashes and root hash.
    """
    private_dir = get_private_dir(create=True)
    hashes: dict[str, dict[str, str]] = {
        "validation": {},
        "locked_test": {},
        "train": {},
    }

    for split_name, groups in partitions.items():
        if split_name == "locked_test":
            split_dir = private_dir / "locked_test"
        else:
            split_dir = repo_root / "suite" / split_name
        split_dir.mkdir(parents=True, exist_ok=True)

        for group_name, items in groups.items():
            file_path = split_dir / f"{group_name}.jsonl"
            with open(file_path, "w", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")
            h = compute_file_sha256(file_path)
            hashes[split_name][group_name] = h

    root_hash = compute_root_hash(hashes["locked_test"])

    return {
        "locked_test_hashes": hashes["locked_test"],
        "validation_hashes": hashes["validation"],
        "train_hashes": hashes["train"],
        "root_hash": root_hash,
        "private_dir": str(private_dir),
    }


def load_suite_partition(
    split: str = "validation",
    group: str | None = None,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Load items from a suite partition for evaluation.

    Parameters:
      split: 'validation', 'train', or 'locked_test'.
      group: Optional group name ('math', 'science_mcq', 'knowledge_mcq',
             'code', 'knowledge_qa', 'memory_probe'). If None, loads all 6 groups.
      repo_root: Optional repository root path.

    Returns:
      List of item dicts with both 'id' and 'item_id' normalized.

    Raises:
      PermissionError: If split == 'locked_test' and KESTREL_ALLOW_LOCKED_TEST != '1'.
      ValueError: If split or group is unrecognized.
      FileNotFoundError: If partition files are not found.
    """
    if split == "locked_test":
        if os.environ.get("KESTREL_ALLOW_LOCKED_TEST") != "1":
            raise PermissionError(
                "Access to locked-test partition is forbidden until Step 10 "
                "(KESTREL_ALLOW_LOCKED_TEST != '1'). Use split='validation' for evaluation and development."
            )
        base_dir = get_private_dir() / "locked_test"
    elif split in ("validation", "train"):
        if repo_root is None:
            repo_root = Path(__file__).resolve().parent.parent
        base_dir = repo_root / "suite" / split
    else:
        raise ValueError(
            f"Unknown split: {split!r}. Must be 'validation', 'train', or 'locked_test'."
        )

    if group is not None:
        if group not in GROUPS:
            raise ValueError(f"Unknown group: {group!r}. Must be one of {GROUPS}")
        target_groups = [group]
    else:
        target_groups = list(GROUPS)

    items: list[dict[str, Any]] = []
    for grp in target_groups:
        file_path = base_dir / f"{grp}.jsonl"
        if not file_path.exists():
            raise FileNotFoundError(f"Partition file not found: {file_path}")
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    it = json.loads(line)
                    # Normalize both item_id and id
                    if "item_id" not in it and "id" in it:
                        it["item_id"] = it["id"]
                    elif "id" not in it and "item_id" in it:
                        it["id"] = it["item_id"]
                    items.append(it)
    return items
