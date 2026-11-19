"""Verify whether 50 random items from suite v1 science_mcq and knowledge_mcq
match the real downloaded ARC-Challenge and MMLU datasets (verbatim normalized text & 5-gram overlap).
"""

from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def get_ngrams(tokens: list[str], n: int = 5) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def main() -> None:
    rng = random.Random(20260104)

    # 1. Load real ARC-Challenge questions
    print("Loading real ARC-Challenge questions...")
    real_arc_questions = []
    arc_dir = RAW_DIR / "ARC-V1-Feb2018-2" / "ARC-Challenge"
    for sp in ("Train", "Dev", "Test"):
        fpath = arc_dir / f"ARC-Challenge-{sp}.jsonl"
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    stem = data.get("question", {}).get("stem", "")
                    if stem:
                        real_arc_questions.append(normalize_text(stem))

    print(f"Loaded {len(real_arc_questions)} real ARC-Challenge stems.")

    # 2. Load real MMLU questions (all subjects)
    print("Loading real MMLU questions...")
    real_mmlu_questions = []
    mmlu_dir = RAW_DIR / "mmlu_data"
    for sp in ("dev", "val", "test"):
        sp_dir = mmlu_dir / sp
        for csv_f in sp_dir.glob("*.csv"):
            with open(csv_f, encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        real_mmlu_questions.append(normalize_text(row[0]))

    print(f"Loaded {len(real_mmlu_questions)} real MMLU questions.")

    real_arc_set = set(real_arc_questions)
    real_mmlu_set = set(real_mmlu_questions)

    # Real ARC and MMLU 5-grams
    real_arc_5grams = set()
    for q in real_arc_questions:
        real_arc_5grams.update(get_ngrams(q.split(), n=5))

    real_mmlu_5grams = set()
    for q in real_mmlu_questions:
        real_mmlu_5grams.update(get_ngrams(q.split(), n=5))

    # 3. Check 50 random suite v1 science_mcq validation items
    with open(REPO_ROOT / "suite" / "validation" / "science_mcq.jsonl", encoding="utf-8") as f:
        v1_sci_items = [json.loads(line) for line in f if line.strip()]

    sample_sci = rng.sample(v1_sci_items, 50)
    sci_exact_matches = 0
    sci_ngram_matches = 0

    for it in sample_sci:
        # Extract stem before Choices: or [A-D])
        prompt = it.get("prompt", "")
        m = re.search(r"^(.*?)(?:\n\s*[A-D]\)|\n\nChoices:)", prompt, re.DOTALL)
        stem = m.group(1).strip() if m else prompt
        norm_stem = normalize_text(stem)

        if norm_stem in real_arc_set:
            sci_exact_matches += 1

        tokens = norm_stem.split()
        item_5grams = get_ngrams(tokens, n=5)
        if item_5grams and (item_5grams & real_arc_5grams):
            sci_ngram_matches += 1

    # 4. Check 50 random suite v1 knowledge_mcq validation items
    with open(REPO_ROOT / "suite" / "validation" / "knowledge_mcq.jsonl", encoding="utf-8") as f:
        v1_know_items = [json.loads(line) for line in f if line.strip()]

    sample_know = rng.sample(v1_know_items, 50)
    know_exact_matches = 0
    know_ngram_matches = 0

    for it in sample_know:
        prompt = it.get("prompt", "")
        m = re.search(r"^(.*?)(?:\n\s*[A-D]\)|\n\nChoices:)", prompt, re.DOTALL)
        stem = m.group(1).strip() if m else prompt
        norm_stem = normalize_text(stem)

        if norm_stem in real_mmlu_set:
            know_exact_matches += 1

        tokens = norm_stem.split()
        item_5grams = get_ngrams(tokens, n=5)
        if item_5grams and (item_5grams & real_mmlu_5grams):
            know_ngram_matches += 1

    results = {
        "science_mcq": {
            "sample_size": 50,
            "real_arc_total_stems": len(real_arc_questions),
            "verbatim_exact_matches": sci_exact_matches,
            "verbatim_exact_match_rate": f"{sci_exact_matches / 50 * 100:.1f}%",
            "five_gram_overlap_matches": sci_ngram_matches,
            "five_gram_overlap_match_rate": f"{sci_ngram_matches / 50 * 100:.1f}%",
        },
        "knowledge_mcq": {
            "sample_size": 50,
            "real_mmlu_total_questions": len(real_mmlu_questions),
            "verbatim_exact_matches": know_exact_matches,
            "verbatim_exact_match_rate": f"{know_exact_matches / 50 * 100:.1f}%",
            "five_gram_overlap_matches": know_ngram_matches,
            "five_gram_overlap_match_rate": f"{know_ngram_matches / 50 * 100:.1f}%",
        },
    }

    out_file = REPO_ROOT / "reports" / "step2" / "public_benchmark_match_verification.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n=== MATCH VERIFICATION RESULTS (EMERGING FROM REAL DOWNLOADED BENCHMARKS) ===")
    print(f"Science MCQ (n=50) vs Real ARC-Challenge ({len(real_arc_questions)} stems):")
    print(
        f"  Exact Normalized Matches: {sci_exact_matches}/50 ({results['science_mcq']['verbatim_exact_match_rate']})"
    )
    print(
        f"  5-Gram Overlap Matches: {sci_ngram_matches}/50 ({results['science_mcq']['five_gram_overlap_match_rate']})"
    )
    print(f"Knowledge MCQ (n=50) vs Real MMLU ({len(real_mmlu_questions)} questions):")
    print(
        f"  Exact Normalized Matches: {know_exact_matches}/50 ({results['knowledge_mcq']['verbatim_exact_match_rate']})"
    )
    print(
        f"  5-Gram Overlap Matches: {know_ngram_matches}/50 ({results['knowledge_mcq']['five_gram_overlap_match_rate']})"
    )
    print(f"Saved results to {out_file}")


if __name__ == "__main__":
    main()
