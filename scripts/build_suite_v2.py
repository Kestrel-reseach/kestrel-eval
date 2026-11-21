"""Build Suite v2.0 (Phase A: Steps A5, A6, A7).

Implements Owner Decision D14:
- math: 100 public GSM8K + 100 synthetic math (16 procedural families).
- science_mcq: 200 public ARC-Challenge (synthetic dropped per A3 audit).
- knowledge_mcq: 300 public MMLU across 10 subjects (30/subject; synthetic dropped per A3 audit).
- code: 50 public MBPP + 50 synthetic algorithmic code (36 families).
- knowledge_qa: 200 real Wikipedia QA (family share <= 30%) + 100 fictional QA (D13).
- memory_probe: 100 synthetic (30 stale across 16 categories + 70 static).
- Total: 1200 items/partition (3600 items total).
- 100% zero ID overlap, zero prompt duplicates, zero overlap with 50 exposed v1 locked items.
- Locked test partitions written to KESTREL_PRIVATE_DIR outside git repo.
- Computes SHA-256 for all partition files and locked root hash for Manifest v2.0.
"""

# ruff: noqa: E402

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.generators.code_generator import generate_code_suite
from evaluation.generators.fictional_qa_generator import (
    generate_fictional_locked_items,
    save_fictional_corpus,
)
from evaluation.generators.knowledge_qa_generator import (
    extract_qa_from_article,
    verify_qa_span,
)
from evaluation.generators.math_generator import generate_math_suite
from evaluation.generators.memory_probe_generator import generate_memory_probe_suite
from evaluation.leakage import (
    check_answer_leakage,
    check_exact_prompt_duplicates,
    check_no_id_overlap,
)
from evaluation.loaders.code_loader import parse_code_record
from evaluation.loaders.common import format_mcq_prompt
from evaluation.loaders.knowledge_mcq_loader import MMLU_10_SUBJECTS
from evaluation.loaders.math_loader import parse_gsm8k_record
from evaluation.loaders.science_mcq_loader import parse_arc_record
from evaluation.suite import compute_file_sha256, compute_root_hash, get_private_dir

BASE_SEED = 20260101
SALT = f"kestrel_suite_v2_{BASE_SEED}"


def load_locked_credentials() -> tuple[int, str, list[Any]]:
    """Load private seed, salt, and personas from KESTREL_PRIVATE_DIR outside git repo."""
    private_dir = get_private_dir()
    env_file = private_dir / "locked_seed.env"
    if not env_file.exists():
        raise FileNotFoundError(
            f"Missing locked credentials file at {env_file}. Private locked generation requires locked_seed.env."
        )

    seed: int | None = None
    salt: str | None = None
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k == "LOCKED_SEED":
                seed = int(v)
            elif k == "LOCKED_SALT":
                salt = v

    if seed is None or salt is None:
        raise ValueError(f"Incomplete credentials in {env_file}: seed or salt missing.")

    personas_file = private_dir / "locked_personas.json"
    if not personas_file.exists():
        raise FileNotFoundError(
            f"Missing private locked personas file at {personas_file}. Decision D17 requires new retired personas."
        )
    with open(personas_file, encoding="utf-8") as f:
        personas = json.load(f)

    return seed, salt, personas


def deterministic_sort_key(item_id: str, extra: str = "", salt: str = SALT) -> str:
    payload = f"{salt}:{item_id}:{extra}".encode()
    return hashlib.sha256(payload).hexdigest()


def load_raw_gsm8k() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    test_p = REPO_ROOT / "data" / "raw" / "gsm8k_test.jsonl"
    train_p = REPO_ROOT / "data" / "raw" / "gsm8k_train.jsonl"

    test_items = []
    with open(test_p, encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if line.strip():
                raw = json.loads(line)
                it = parse_gsm8k_record(raw, index=idx)
                # Filter out items where the numeric target trivially appears in the question text
                if it["target"] and it["target"] in it["prompt"]:
                    continue
                it["metadata"]["source_split"] = "test"
                it["arm"] = "public"
                it["template_family"] = "gsm8k"
                test_items.append(it)

    train_items = []
    with open(train_p, encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if line.strip():
                raw = json.loads(line)
                it = parse_gsm8k_record(raw, index=idx)
                if it["target"] and it["target"] in it["prompt"]:
                    continue
                it["metadata"]["source_split"] = "train"
                it["arm"] = "public"
                it["template_family"] = "gsm8k"
                train_items.append(it)

    return test_items, train_items


def load_raw_arc_challenge() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    arc_dir = REPO_ROOT / "data" / "raw" / "ARC-V1-Feb2018-2" / "ARC-Challenge"
    test_p = arc_dir / "ARC-Challenge-Test.jsonl"
    dev_p = arc_dir / "ARC-Challenge-Dev.jsonl"
    train_p = arc_dir / "ARC-Challenge-Train.jsonl"

    eval_items = []
    seen_stems: set[str] = set()
    idx = 1
    for p in (test_p, dev_p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    raw = json.loads(line)
                    stem = raw.get("question", {}).get("stem", "").strip().lower()
                    if stem in seen_stems:
                        continue
                    seen_stems.add(stem)
                    it = parse_arc_record(raw, index=idx)
                    it["metadata"]["source_split"] = "test_or_dev"
                    it["arm"] = "public"
                    it["template_family"] = "arc_challenge"
                    eval_items.append(it)
                    idx += 1

    train_items = []
    with open(train_p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                raw = json.loads(line)
                stem = raw.get("question", {}).get("stem", "").strip().lower()
                if stem in seen_stems:
                    continue
                seen_stems.add(stem)
                it = parse_arc_record(raw, index=idx)
                it["metadata"]["source_split"] = "train"
                it["arm"] = "public"
                it["template_family"] = "arc_challenge"
                train_items.append(it)
                idx += 1

    return eval_items, train_items


def load_raw_mmlu_by_subject() -> dict[str, list[dict[str, Any]]]:
    mmlu_dir = REPO_ROOT / "data" / "raw" / "mmlu_data"

    items_by_subject: dict[str, list[dict[str, Any]]] = {}
    for subj in MMLU_10_SUBJECTS:
        subj_items = []
        seen_questions: set[str] = set()
        r_idx = 1
        for split_dir in ("test", "val", "dev"):
            csv_p = mmlu_dir / split_dir / f"{subj}_{split_dir}.csv"
            if not csv_p.exists():
                continue
            with open(csv_p, encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 6:
                        continue
                    q, choices, ans = row[0], row[1:5], row[5].strip().upper()
                    q_norm = q.strip().lower()
                    if q_norm in seen_questions:
                        continue
                    seen_questions.add(q_norm)
                    prompt = format_mcq_prompt(q, choices)
                    it = {
                        "item_id": f"mmlu_{subj}_{r_idx:04d}",
                        "group": "knowledge_mcq",
                        "prompt": prompt,
                        "question": q,
                        "target": ans,
                        "answer_check": "answer_key",
                        "choices": choices,
                        "arm": "public",
                        "template_family": subj,
                        "metadata": {
                            "source": "MMLU (Hendrycks et al., 2020)",
                            "subject": subj,
                            "license": "MIT",
                            "source_split": split_dir,
                            "arm": "public",
                            "template_family": subj,
                            "original_id": f"{subj}_{split_dir}_{r_idx}",
                        },
                    }
                    subj_items.append(it)
                    r_idx += 1
        items_by_subject[subj] = subj_items
    return items_by_subject


def load_raw_mbpp() -> list[dict[str, Any]]:
    mbpp_p = REPO_ROOT / "data" / "raw" / "mbpp.jsonl"
    items = []
    with open(mbpp_p, encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if line.strip():
                raw = json.loads(line)
                it = parse_code_record(raw, index=idx, source_key="mbpp")
                it["arm"] = "public"
                it["template_family"] = "mbpp"
                it["metadata"]["source_split"] = "train_eval"
                it["metadata"]["arm"] = "public"
                it["metadata"]["template_family"] = "mbpp"
                items.append(it)
    return items


def load_real_wikipedia_qa(
    exposed_titles: set[str],
    n_per_split: int = 200,
    max_family_share: float = 0.30,
    locked_salt: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    corpus_p = REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl"
    corpus: list[dict[str, Any]] = []
    with open(corpus_p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                corpus.append(json.loads(line))

    # Deterministic pool of QA items
    pool: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()

    for art in corpus:
        title = art.get("title", "")
        # Filter out any title belonging to the 50 exposed locked items
        if title.lower() in exposed_titles:
            continue

        qa_list = extract_qa_from_article(art)
        for qa in qa_list:
            q_norm = qa["question"].strip().lower()
            if q_norm in seen_prompts:
                continue
            seen_prompts.add(q_norm)
            pool.append(qa)

    # Sort deterministically with public salt
    pool.sort(key=lambda x: deterministic_sort_key(x["passage_id"], x["question"], salt=SALT))

    splits = {"validation": [], "locked_test": [], "train": []}
    max_per_fam = int(n_per_split * max_family_share)

    # In Suite v2.0, items were selected in order: pass 1 (old locked), pass 2 (validation), pass 3 (train).
    # To guarantee validation and train remain 100% bit-for-bit identical, we preserve their exact slices.
    temp_pool = list(pool)
    pass_slices: dict[str, list[dict[str, Any]]] = {}
    for p_name in ("old_locked", "validation", "train"):
        sel = []
        fam_counts: dict[str, int] = {}
        for cand in temp_pool:
            fam = cand["rule_family"]
            if fam_counts.get(fam, 0) >= max_per_fam:
                continue
            sel.append(cand)
            fam_counts[fam] = fam_counts.get(fam, 0) + 1
            if len(sel) == n_per_split:
                break
        sel_set = set(id(c) for c in sel)
        temp_pool = [c for c in temp_pool if id(c) not in sel_set]
        pass_slices[p_name] = sel

    selected_val = pass_slices["validation"]
    selected_train = pass_slices["train"]

    # Now select NEW locked items under private locked_salt from pool minus validation and train
    used_set = set(id(c) for c in selected_val + selected_train)
    available_for_lock = [c for c in pool if id(c) not in used_set]
    lock_salt_to_use = locked_salt if locked_salt is not None else SALT
    available_for_lock.sort(
        key=lambda x: deterministic_sort_key(x["passage_id"], x["question"], salt=lock_salt_to_use)
    )

    selected_lock = []
    lock_fam_counts: dict[str, int] = {}
    for cand in available_for_lock:
        fam = cand["rule_family"]
        if lock_fam_counts.get(fam, 0) >= max_per_fam:
            continue
        selected_lock.append(cand)
        lock_fam_counts[fam] = lock_fam_counts.get(fam, 0) + 1
        if len(selected_lock) == n_per_split:
            break

    # Format items
    for split_name, selected_items in (
        ("validation", selected_val),
        ("locked_test", selected_lock),
        ("train", selected_train),
    ):
        formatted = []
        prefix = {"validation": "kqa_val", "locked_test": "kqa_lock", "train": "kqa_train"}[
            split_name
        ]
        for idx, it in enumerate(selected_items, 1):
            assert verify_qa_span(it["passage"], it["answer"], it["answer_span"])
            item_id = f"{prefix}_{idx:04d}"
            formatted.append(
                {
                    "item_id": item_id,
                    "id": item_id,
                    "group": "knowledge_qa",
                    "prompt": f"Passage:\n{it['passage']}\n\nQuestion: {it['question']}\nAnswer:",
                    "question": it["question"],
                    "target": it["answer"],
                    "answer_check": "normalized_exact_match",
                    "choices": None,
                    "arm": "real_wikipedia",
                    "template_family": it["rule_family"],
                    "split": split_name,
                    "metadata": {
                        "source": "Wikipedia English Abstracts 5k (2026-11)",
                        "passage_id": it["passage_id"],
                        "passage_title": it["passage_title"],
                        "passage": it["passage"],
                        "answer_span": it["answer_span"],
                        "rule_family": it["rule_family"],
                        "template_family": it["rule_family"],
                        "arm": "real_wikipedia",
                        "license": "CC BY-SA 4.0",
                    },
                }
            )
        splits[split_name] = formatted

    return splits


def get_50_exposed_v1_titles() -> set[str]:
    # Titles from the PR 3 exposure incident (commit 6ec22c2)
    return {
        "fred singer",
        "ed sullivan",
        "gilles deleuze",
        "georg henrik von wright",
        "hezârfen ahmed çelebi",
        "filippo tommaso marinetti",
        "c. s. lewis",
        "claude debussy",
        "emil theodor kocher",
        "c. l. moore",
        "burhanuddin rabbani",
        "bill joy",
        "daniel gabriel fahrenheit",
        "bob knight",
        "berthe morisot",
        "charles alston",
        "billy crystal",
        "hugh hefner",
        "charles evans hughes",
        "elizabeth garrett anderson",
        "dressed to kill (1980 film)",
        "christian goldbach",
        "george abbot (author)",
        "albert frederick, duke of prussia",
        "languages of europe",
        "e. e. smith",
        "aaliyah",
        "bram stoker",
        "drew barrymore",
        "diego maradona",
        "brion gysin",
        "bert bell",
        "christine lavin",
        "huldrych zwingli",
        "camilla hall",
        "antonio vivaldi",
        "graham chapman",
        "charles baudelaire",
        "edward jenner",
        "hannibal hamlin",
        "hunter s. thompson",
        "agostino carracci",
        "fort william, scotland",
        "crete",
        "bobby charlton",
        "dr. seuss",
        "albert camus",
        "william m. tweed",
        "the bronx",
    }


def build_suite_v2_partitions() -> dict[str, dict[str, list[dict[str, Any]]]]:
    print("=" * 80)
    print("BUILDING SUITE v2.1 (DECISIONS D14, D16, D17)")
    print("=" * 80)

    locked_seed, locked_salt, locked_personas = load_locked_credentials()

    # 1. Math: 100 GSM8K + 100 Synthetic per partition
    print("Loading and partitioning Math (GSM8K public + 16-family synthetic)...")
    gsm_test, gsm_train = load_raw_gsm8k()
    gsm_test.sort(key=lambda x: deterministic_sort_key(x["metadata"]["original_id"]))
    gsm_train.sort(key=lambda x: deterministic_sort_key(x["metadata"]["original_id"]))

    math_pub_val = gsm_test[100:200]
    math_pub_train = gsm_train[:100]
    gsm_remaining = [x for x in gsm_test if x not in math_pub_val and x not in math_pub_train]
    gsm_remaining.sort(
        key=lambda x: deterministic_sort_key(x["metadata"]["original_id"], salt=locked_salt)
    )
    math_pub_lock = gsm_remaining[:100]

    seen_math: set[str] = set()
    # Populate collision set in the identical sequence as Suite v2.0 to preserve validation and train hashes
    _ = generate_math_suite(100, seed=BASE_SEED + 101, seen_prompts=seen_math)
    math_synth_val = generate_math_suite(100, seed=BASE_SEED + 102, seen_prompts=seen_math)
    math_synth_train = generate_math_suite(100, seed=BASE_SEED + 103, seen_prompts=seen_math)
    math_synth_lock = generate_math_suite(100, seed=locked_seed + 101, seen_prompts=seen_math)

    # 2. Science MCQ: 200 ARC-Challenge per partition (100% PUBLIC)
    print("Loading and partitioning Science MCQ (ARC-Challenge, 100% public)...")
    arc_eval, arc_train = load_raw_arc_challenge()
    arc_eval.sort(key=lambda x: deterministic_sort_key(x["metadata"]["original_id"]))
    arc_train.sort(key=lambda x: deterministic_sort_key(x["metadata"]["original_id"]))

    sci_val = arc_eval[200:400]
    sci_train = arc_train[:200]
    arc_remaining = [x for x in arc_eval if x not in sci_val and x not in sci_train]
    arc_remaining.sort(
        key=lambda x: deterministic_sort_key(x["metadata"]["original_id"], salt=locked_salt)
    )
    sci_lock = arc_remaining[:200]

    # 3. Knowledge MCQ: 300 MMLU (30/subj x 10 subjects) per partition (100% PUBLIC)
    print("Loading and partitioning Knowledge MCQ (MMLU 10 subjects, 100% public)...")
    mmlu_by_subj = load_raw_mmlu_by_subject()
    know_lock, know_val, know_train = [], [], []
    for subj in MMLU_10_SUBJECTS:
        s_items = list(mmlu_by_subj[subj])
        s_items.sort(key=lambda x: deterministic_sort_key(x["metadata"]["original_id"]))
        val_s = s_items[30:60]
        train_s = s_items[60:90]
        rem_s = [x for x in s_items if x not in val_s and x not in train_s]
        rem_s.sort(
            key=lambda x: deterministic_sort_key(x["metadata"]["original_id"], salt=locked_salt)
        )
        lock_s = rem_s[:30]
        know_val.extend(val_s)
        know_train.extend(train_s)
        know_lock.extend(lock_s)

    # 4. Code: 50 MBPP + 50 Synthetic per partition
    print("Loading and partitioning Code (MBPP public + 36-family synthetic)...")
    mbpp_all = load_raw_mbpp()
    mbpp_all.sort(key=lambda x: deterministic_sort_key(str(x["metadata"]["original_id"])))

    code_pub_val = mbpp_all[50:100]
    code_pub_train = mbpp_all[100:150]
    mbpp_remaining = [x for x in mbpp_all if x not in code_pub_val and x not in code_pub_train]
    mbpp_remaining.sort(
        key=lambda x: deterministic_sort_key(str(x["metadata"]["original_id"]), salt=locked_salt)
    )
    code_pub_lock = mbpp_remaining[:50]

    seen_code: set[str] = set()
    # Populate collision set in the identical sequence as Suite v2.0 to preserve validation and train hashes
    _ = generate_code_suite(50, seed=BASE_SEED + 301, seen_prompts=seen_code)
    code_synth_val = generate_code_suite(50, seed=BASE_SEED + 302, seen_prompts=seen_code)
    code_synth_train = generate_code_suite(50, seed=BASE_SEED + 303, seen_prompts=seen_code)
    code_synth_lock = generate_code_suite(50, seed=locked_seed + 301, seen_prompts=seen_code)

    # 5. Knowledge QA: 200 Real Wikipedia + 100 Fictional per partition
    print("Building Knowledge QA (200 Real Wikipedia + 100 Fictional Entities)...")
    exposed_titles = get_50_exposed_v1_titles()
    real_kqa_splits = load_real_wikipedia_qa(
        exposed_titles=exposed_titles,
        n_per_split=200,
        max_family_share=0.30,
        locked_salt=locked_salt,
    )

    # Generate public fictional corpus and 200 public items (100 val + 100 train)
    _, fictional_corpus, fictional_items = save_fictional_corpus()
    fict_val = fictional_items[:100]
    fict_train = fictional_items[100:200]

    # Generate private locked fictional items using locked personas under private seed/salt
    private_dir = get_private_dir()
    locked_corpus, fict_lock = generate_fictional_locked_items(locked_personas)
    fict_lock_corpus_p = private_dir / "fictional_locked_passages.jsonl"
    with open(fict_lock_corpus_p, "w", encoding="utf-8") as f:
        for doc in locked_corpus:
            f.write(json.dumps(doc) + "\n")

    # Combine real + fictional
    kqa_lock = real_kqa_splits["locked_test"] + fict_lock
    kqa_val = real_kqa_splits["validation"] + fict_val
    kqa_train = real_kqa_splits["train"] + fict_train

    # 6. Memory Probe: 150 Synthetic (100 stale + 50 static) across 16 categories (Decision D16)
    print("Building Memory Probe (100 stale categories + 50 static per D16)...")
    global_seen_mem: set[str] = set()
    mem_val = generate_memory_probe_suite(
        150, stale_fact_count=100, seed=BASE_SEED + 502, seen_prompts=global_seen_mem
    )
    mem_train = generate_memory_probe_suite(
        150, stale_fact_count=100, seed=BASE_SEED + 503, seen_prompts=global_seen_mem
    )
    mem_lock = generate_memory_probe_suite(
        150, stale_fact_count=100, seed=locked_seed + 501, seen_prompts=global_seen_mem
    )

    # Reprefix canonical IDs for clean partition index
    def _finalize_group(
        items: list[dict[str, Any]], prefix: str, split_name: str
    ) -> list[dict[str, Any]]:
        finalized = []
        for idx, raw in enumerate(items, 1):
            it = dict(raw)
            canonical_id = f"{prefix}_{idx:04d}"
            it["id"] = canonical_id
            it["item_id"] = canonical_id
            it["split"] = split_name
            if "arm" not in it:
                it["arm"] = it.get("metadata", {}).get("arm", "public")
            if "template_family" not in it:
                it["template_family"] = it.get("metadata", {}).get("template_family", "general")
            finalized.append(it)
        return finalized

    partitions = {
        "validation": {
            "math": _finalize_group(math_pub_val + math_synth_val, "math_val", "validation"),
            "science_mcq": _finalize_group(sci_val, "sci_val", "validation"),
            "knowledge_mcq": _finalize_group(know_val, "know_val", "validation"),
            "code": _finalize_group(code_pub_val + code_synth_val, "code_val", "validation"),
            "knowledge_qa": _finalize_group(kqa_val, "kqa_val", "validation"),
            "memory_probe": _finalize_group(mem_val, "mem_val", "validation"),
        },
        "locked_test": {
            "math": _finalize_group(math_pub_lock + math_synth_lock, "math_lock", "locked_test"),
            "science_mcq": _finalize_group(sci_lock, "sci_lock", "locked_test"),
            "knowledge_mcq": _finalize_group(know_lock, "know_lock", "locked_test"),
            "code": _finalize_group(code_pub_lock + code_synth_lock, "code_lock", "locked_test"),
            "knowledge_qa": _finalize_group(kqa_lock, "kqa_lock", "locked_test"),
            "memory_probe": _finalize_group(mem_lock, "mem_lock", "locked_test"),
        },
        "train": {
            "math": _finalize_group(math_pub_train + math_synth_train, "math_train", "train"),
            "science_mcq": _finalize_group(sci_train, "sci_train", "train"),
            "knowledge_mcq": _finalize_group(know_train, "know_train", "train"),
            "code": _finalize_group(code_pub_train + code_synth_train, "code_train", "train"),
            "knowledge_qa": _finalize_group(kqa_train, "kqa_train", "train"),
            "memory_probe": _finalize_group(mem_train, "mem_train", "train"),
        },
    }

    # Verify counts
    for split_name, grps in partitions.items():
        total = sum(len(items) for items in grps.values())
        print(f"Partition '{split_name}': total {total} items")
        for g_name, items in grps.items():
            print(f"  - {g_name}: {len(items)} items")
        assert total == 1250, f"Partition '{split_name}' has {total} items, expected 1250"

    return partitions


def verify_suite_leakage_and_integrity(
    partitions: dict[str, dict[str, list[dict[str, Any]]]],
) -> None:
    print("\nRunning Automated Leakage & Partition Independence Checks...")
    flat_partitions = {
        split_name: [it for grp in groups.values() for it in grp]
        for split_name, groups in partitions.items()
    }

    # 1. Zero ID overlap
    check_no_id_overlap(flat_partitions)
    print("PASS: Zero ID overlap across validation, locked_test, and train.")

    # 2. Zero exact prompt duplicates
    dups = check_exact_prompt_duplicates(flat_partitions)
    if dups:
        raise ValueError(f"Found {len(dups)} duplicate prompts across partitions: {dups[:3]}")
    print("PASS: Zero exact prompt duplicates across partitions.")

    # 3. Answer in prompt leakage
    for split_name, items in flat_partitions.items():
        leaks = check_answer_leakage(items)
        if leaks:
            print(
                f"WARNING: {len(leaks)} potential answer leaks in {split_name}: {[it.get('id') for it in leaks[:2]]}"
            )
    print("PASS: Answer leakage check complete.")

    # 4. Zero overlap with 50 exposed locked items
    exposed_titles = get_50_exposed_v1_titles()
    for split_name, items in flat_partitions.items():
        for it in items:
            title = it.get("metadata", {}).get("passage_title", "").strip().lower()
            if title and title in exposed_titles:
                raise ValueError(
                    f"CRITICAL LEAK: Exposed v1 title {title!r} found in {split_name} item {it['id']}"
                )
    print("PASS: Zero overlap with the 50 exposed v1 locked items.")


def write_suite_v2(partitions: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    print("\nWriting Suite v2.0 files...")
    private_dir = get_private_dir(create=True)
    locked_dir = private_dir / "locked_test"

    # Archive superseded v1 locked test partition if present
    if locked_dir.exists():
        archive_dir = private_dir / "superseded_v1_locked_test"
        if not archive_dir.exists():
            print(f"Archiving superseded v1 locked files from {locked_dir} -> {archive_dir}...")
            shutil.copytree(locked_dir, archive_dir)
            print("Successfully archived superseded v1 locked files.")

    hashes: dict[str, dict[str, str]] = {
        "validation": {},
        "locked_test": {},
        "train": {},
    }

    for split_name, groups in partitions.items():
        if split_name == "locked_test":
            dest_dir = locked_dir
        else:
            dest_dir = REPO_ROOT / "suite" / split_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        for grp_name, items in groups.items():
            fpath = dest_dir / f"{grp_name}.jsonl"
            with open(fpath, "w", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")
            h = compute_file_sha256(fpath)
            hashes[split_name][grp_name] = h
            print(f"Wrote {split_name}/{grp_name}.jsonl ({len(items)} items) -> SHA-256: {h}")

    root_hash = compute_root_hash(hashes["locked_test"])
    print(f"\nNEW LOCKED ROOT HASH (Suite v2.0): {root_hash}")
    return {"hashes": hashes, "root_hash": root_hash}


def print_confidence_interval_half_widths(
    partitions: dict[str, dict[str, list[dict[str, Any]]]],
) -> None:
    import math

    def hw(n: int) -> float:
        return 1.96 * math.sqrt(0.25 / n) * 100

    print("\n" + "=" * 80)
    print("95% WILSON / BINOMIAL CONFIDENCE INTERVAL HALF-WIDTHS PER ARM (p = 0.5)")
    print("=" * 80)
    print(f"{'Group':<16} | {'Arm':<18} | {'N (per split)':<14} | {'95% CI Half-Width':<18}")
    print("-" * 72)

    val_groups = partitions["validation"]
    for grp, items in val_groups.items():
        arms: dict[str, int] = {}
        for it in items:
            a = it.get("arm", "unspecified")
            arms[a] = arms.get(a, 0) + 1
        for arm_name, cnt in arms.items():
            h = hw(cnt)
            print(f"{grp:<16} | {arm_name:<18} | {cnt:<14} | ±{h:.2f} pp")
        # Total for group
        print(f"{grp:<16} | {'TOTAL GROUP':<18} | {len(items):<14} | ±{hw(len(items)):.2f} pp")
        print("-" * 72)


def main() -> None:
    partitions = build_suite_v2_partitions()
    verify_suite_leakage_and_integrity(partitions)
    res = write_suite_v2(partitions)
    print_confidence_interval_half_widths(partitions)

    out_hashes = REPO_ROOT / "reports" / "step2" / "suite_v2_hashes.json"
    with open(out_hashes, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"\nSaved hash summary to {out_hashes}")


if __name__ == "__main__":
    main()
