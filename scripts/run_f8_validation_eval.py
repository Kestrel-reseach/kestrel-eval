"""F8: Large-Scale Validation Evaluation on Qwen2.5-0.5B-Instruct.

Covers:
- F8c: All 200 science_mcq and 300 knowledge_mcq items (unshuffled + 3-permutation shuffled).
- F8d: All 300 knowledge_qa items with BM25 top-3 context, cap 32, evaluated on:
       (1) Normalized exact match (dates, numbers, articles, passage aliases)
       (2) Token F1
       (3) Short non-list containment
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, ".")
from evaluation.extractors import extract_mcq_answer  # noqa: E402
from evaluation.prompts import (  # noqa: E402
    extract_question_text,
    format_prompt_for_model,
)
from evaluation.retrieval import BM25Retriever  # noqa: E402
from evaluation.suite import load_suite_partition  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def wilson_score_interval(
    correct: int, total: int, confidence: float = 0.95
) -> tuple[float, float]:
    """Compute Wilson score 95% confidence interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95% confidence
    p = correct / total
    denom = 1.0 + (z**2) / total
    centre = (p + (z**2) / (2 * total)) / denom
    half = (z * math.sqrt((p * (1 - p) + (z**2) / (4 * total)) / total)) / denom
    return (round(max(0.0, centre - half) * 100, 2), round(min(1.0, centre + half) * 100, 2))


def normalize_answer(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(?:the|a|an)\s+", "", s)
    s = re.sub(r"[.,;:'\"!?]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_number(s: str) -> str:
    return re.sub(r"(?<=\d),(?=\d)", "", s)


def try_parse_date(s: str) -> Any | None:
    s = normalize_answer(s)
    fmts = (
        "%d %B %Y",
        "%B %d %Y",
        "%B %d, %Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%b %d %Y",
        "%b %d, %Y",
        "%Y",
    )
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def extract_aliases_from_passage(passage: str, target: str) -> set[str]:
    """Extract plausible aliases / synonyms for target entity from passage."""
    aliases = {normalize_answer(target)}
    # If target is date
    dt = try_parse_date(target)
    if dt:
        aliases.add(str(dt.year))
        aliases.add(dt.strftime("%d %B %Y").lower())
        aliases.add(dt.strftime("%B %d, %Y").lower())

    # Check for compound professions like 'architect and sculptor'
    norm_p = passage.lower()
    norm_t = target.lower()
    for m in re.finditer(rf"\b{re.escape(norm_t)}\s+and\s+(\w+)\b", norm_p):
        aliases.add(m.group(1).lower())
    for m in re.finditer(rf"\b(\w+)\s+and\s+{re.escape(norm_t)}\b", norm_p):
        aliases.add(m.group(1).lower())

    return aliases


def score_exact_match_qa(pred: str, target: str, passage: str = "") -> bool:
    np = normalize_number(normalize_answer(pred))
    nt = normalize_number(normalize_answer(target))
    if np == nt:
        return True

    aliases = extract_aliases_from_passage(passage, target)
    if np in aliases:
        return True

    dp = try_parse_date(pred)
    dt = try_parse_date(target)
    if dp and dt and dp == dt:
        return True

    return False


def score_token_f1_qa(pred: str, target: str) -> float:
    np = normalize_answer(normalize_number(pred))
    nt = normalize_answer(normalize_number(target))
    pred_tokens = re.findall(r"\w+", np)
    gold_tokens = re.findall(r"\w+", nt)
    if not pred_tokens or not gold_tokens:
        return 1.0 if pred_tokens == gold_tokens else 0.0
    common = set(pred_tokens) & set(gold_tokens)
    num_same = sum(min(pred_tokens.count(w), gold_tokens.count(w)) for w in common)
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return (2 * precision * recall) / (precision + recall)


def score_containment_qa(pred: str, target: str) -> bool:
    np = normalize_number(normalize_answer(pred))
    nt = normalize_number(normalize_answer(target))
    words = np.split()
    # ONLY when extracted answer is short (<= 8 words)
    if len(words) > 8:
        return False
    # NOT a list (no commas/semicolons and no 'and' unless target has it)
    if ("," in pred or ";" in pred or " and " in pred) and (
        "," not in target and " and " not in target
    ):
        return False
    return nt in np


def shuffle_mcq_item(item: dict[str, Any], seed: int) -> dict[str, Any]:
    """Create a new item with shuffled choices A, B, C, D."""
    rng = random.Random(seed)
    choices = list(item.get("choices", []))
    old_target = item.get("target")

    # Map labels to indices
    label_to_idx = {"A": 0, "B": 1, "C": 2, "D": 3}
    idx_to_label = {0: "A", 1: "B", 2: "C", 3: "D"}
    correct_idx = label_to_idx.get(old_target, 0)

    indices = list(range(len(choices)))
    rng.shuffle(indices)

    new_choices = [choices[i] for i in indices]
    new_correct_idx = indices.index(correct_idx)
    new_target = idx_to_label[new_correct_idx]

    stem = item.get("stem") or item.get("question")
    if not stem:
        prompt = item.get("prompt", "")
        # Extract stem before Question: or Choices:
        m = re.search(r"^(.*?)(?:\n\s*[A-D]\)|\n\nChoices:)", prompt, re.DOTALL)
        stem = m.group(1).strip() if m else prompt

    # Build new prompt
    choice_lines = [f"{idx_to_label[i]}) {text}" for i, text in enumerate(new_choices)]
    new_prompt = f"{stem}\n\n" + "\n".join(choice_lines)

    shuffled = dict(item)
    shuffled["choices"] = new_choices
    shuffled["target"] = new_target
    shuffled["prompt"] = new_prompt
    return shuffled


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    print(f"Loading tokenizer and model {model_name} on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map=device,
        local_files_only=True,
    )
    model.eval()

    # Load validation and train partitions
    val_items = load_suite_partition("validation")
    train_items = load_suite_partition("train")

    sci_val = [it for it in val_items if it.get("group") == "science_mcq"]
    sci_train = [it for it in train_items if it.get("group") == "science_mcq"]

    know_val = [it for it in val_items if it.get("group") == "knowledge_mcq"]
    know_train = [it for it in train_items if it.get("group") == "knowledge_mcq"]

    kqa_val = [it for it in val_items if it.get("group") == "knowledge_qa"]

    print(
        f"Loaded {len(sci_val)} science_mcq, {len(know_val)} knowledge_mcq, {len(kqa_val)} knowledge_qa items."
    )

    # ==============================================================================
    # F8c: MCQ SANITY AT SCALE
    # ==============================================================================
    print("\n" + "=" * 80)
    print("F8c: MCQ EVALUATION ON ALL VALIDATION ITEMS")
    print("=" * 80)

    def run_mcq_batch(items: list[dict[str, Any]], desc: str) -> dict[str, Any]:
        correct_count = 0
        pred_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "None": 0}
        key_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
        records = []
        truncated_count = 0
        extractable_count = 0

        for _idx, it in enumerate(items):
            prompt_str, prompt_hash, prefill = format_prompt_for_model(it, tokenizer=tokenizer)
            inputs = tokenizer(prompt_str, return_tensors="pt").to(device)
            target = it["target"]
            key_dist[target] = key_dist.get(target, 0) + 1

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=8,
                    do_sample=False,
                    eos_token_id=[tokenizer.eos_token_id, 198, 271],
                )
            gen_tokens = outputs[0][inputs["input_ids"].shape[1] :]
            token_count = len(gen_tokens)
            if token_count >= 8:
                truncated_count += 1
            raw_out = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

            extracted = extract_mcq_answer(raw_out)
            if extracted is not None:
                extractable_count += 1
                pred_dist[extracted] = pred_dist.get(extracted, 0) + 1
            else:
                pred_dist["None"] += 1

            is_correct = extracted == target
            if is_correct:
                correct_count += 1

            records.append(
                {
                    "item_id": it["item_id"],
                    "target": target,
                    "extracted": extracted,
                    "correct": is_correct,
                    "token_count": token_count,
                    "raw_output": raw_out,
                }
            )

        acc = (correct_count / len(items)) * 100
        ci_low, ci_high = wilson_score_interval(correct_count, len(items))
        trunc_rate = (truncated_count / len(items)) * 100
        extractable_rate = (extractable_count / len(items)) * 100

        # Always A accuracy
        always_a_acc = (key_dist.get("A", 0) / len(items)) * 100
        most_common_key = max(key_dist, key=key_dist.get)
        most_common_acc = (key_dist[most_common_key] / len(items)) * 100

        return {
            "desc": desc,
            "total": len(items),
            "correct": correct_count,
            "accuracy": round(acc, 2),
            "ci_95": (ci_low, ci_high),
            "truncation_rate": round(trunc_rate, 2),
            "extractable_rate": round(extractable_rate, 2),
            "pred_dist": pred_dist,
            "key_dist": key_dist,
            "always_a_acc": round(always_a_acc, 2),
            "most_common_key": most_common_key,
            "most_common_acc": round(most_common_acc, 2),
            "records": records,
        }

    # 1. Science MCQ (n=200)
    print("\nRunning Science MCQ (n=200)...")
    sci_results = run_mcq_batch(sci_val, "science_mcq (n=200)")

    # 2. Knowledge MCQ (n=300)
    print("\nRunning Knowledge MCQ (n=300)...")
    know_results = run_mcq_batch(know_val, "knowledge_mcq (n=300)")

    # Train key distributions
    sci_train_keys = Counter(it["target"] for it in sci_train)
    know_train_keys = Counter(it["target"] for it in know_train)

    # 3. Shuffled Option Permutations (3 permutations)
    print("\nRunning Option Shuffling (3 permutations) on science_mcq...")
    sci_shuffled_accs = []
    for p_idx, seed in enumerate([42, 1337, 2026], start=1):
        shuffled_items = [shuffle_mcq_item(it, seed=seed + i) for i, it in enumerate(sci_val)]
        res = run_mcq_batch(shuffled_items, f"science_mcq shuffled perm {p_idx}")
        sci_shuffled_accs.append(res["accuracy"])
        print(f"  Permutation {p_idx}: {res['accuracy']}%")

    print("\nRunning Option Shuffling (3 permutations) on knowledge_mcq...")
    know_shuffled_accs = []
    for p_idx, seed in enumerate([42, 1337, 2026], start=1):
        shuffled_items = [shuffle_mcq_item(it, seed=seed + i) for i, it in enumerate(know_val)]
        res = run_mcq_batch(shuffled_items, f"knowledge_mcq shuffled perm {p_idx}")
        know_shuffled_accs.append(res["accuracy"])
        print(f"  Permutation {p_idx}: {res['accuracy']}%")

    # ==============================================================================
    # F8d: KNOWLEDGE-QA PROMPT AND SCORING ON ALL 300 ITEMS
    # ==============================================================================
    print("\n" + "=" * 80)
    print("F8d: KNOWLEDGE-QA EVALUATION ON ALL 300 VALIDATION ITEMS")
    print("=" * 80)

    corpus_path = REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl"
    print(f"Loading BM25 index from {corpus_path}...")
    retriever = BM25Retriever.from_jsonl(corpus_path)

    qa_records = []
    em_count = 0
    f1_total = 0.0
    containment_count = 0
    truncated_qa = 0

    for _idx, it in enumerate(kqa_val, start=1):
        # Format prompt with BM25 top-3 context and Answer: prefill
        augmented_prompt, _ = retriever.augment_knowledge_qa_prompt(it, top_k=3)
        question = extract_question_text(it)
        target = it["target"]
        passage = it.get("passage", "")

        # Build clean user prompt without baked prompt
        user_content = f"Context:\n{augmented_prompt.split('Context:\n')[1].split('\n\nQuestion:')[0]}\n\nQuestion: {question}"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a factual question answering assistant. "
                    "Answer the question with only the direct short answer (e.g. name, date, or number). "
                    "Do not write full sentences or explanations."
                ),
            },
            {"role": "user", "content": user_content},
        ]
        prompt_str = (
            tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            + "Answer:"
        )

        inputs = tokenizer(prompt_str, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=32,
                do_sample=False,
                eos_token_id=[tokenizer.eos_token_id, 198, 271],
            )
        gen_tokens = outputs[0][inputs["input_ids"].shape[1] :]
        if len(gen_tokens) >= 32:
            truncated_qa += 1
        raw_out = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        # Clean raw_out of any redundant Answer: prefix
        clean_pred = re.sub(r"^(?:Answer:|\s*:\s*)\s*", "", raw_out, flags=re.IGNORECASE).strip()

        em = score_exact_match_qa(clean_pred, target, passage=passage)
        f1 = score_token_f1_qa(clean_pred, target)
        cont = score_containment_qa(clean_pred, target)

        if em:
            em_count += 1
        f1_total += f1
        if cont:
            containment_count += 1

        qa_records.append(
            {
                "item_id": it["item_id"],
                "question": question,
                "target": target,
                "prediction": clean_pred,
                "raw_output": raw_out,
                "tokens": len(gen_tokens),
                "exact_match": em,
                "token_f1": round(f1, 4),
                "containment": cont,
                "rule_family": it.get("rule_family", ""),
            }
        )

    em_acc = (em_count / len(kqa_val)) * 100
    avg_f1 = (f1_total / len(kqa_val)) * 100
    cont_acc = (containment_count / len(kqa_val)) * 100
    qa_trunc_rate = (truncated_qa / len(kqa_val)) * 100

    # Find disagreeing cases
    disagreements = [
        r
        for r in qa_records
        if not (r["exact_match"] == (r["token_f1"] == 1.0) == r["containment"])
    ]
    print(f"Total QA disagreement cases: {len(disagreements)}")

    # Compile comprehensive results
    summary = {
        "science_mcq": {
            "accuracy": sci_results["accuracy"],
            "ci_95": sci_results["ci_95"],
            "truncation_rate": sci_results["truncation_rate"],
            "extractable_rate": sci_results["extractable_rate"],
            "pred_dist": sci_results["pred_dist"],
            "val_key_dist": sci_results["key_dist"],
            "train_key_dist": dict(sci_train_keys),
            "always_a_acc": sci_results["always_a_acc"],
            "most_common_acc": sci_results["most_common_acc"],
            "shuffled_accs": sci_shuffled_accs,
            "shuffled_avg": round(sum(sci_shuffled_accs) / len(sci_shuffled_accs), 2),
        },
        "knowledge_mcq": {
            "accuracy": know_results["accuracy"],
            "ci_95": know_results["ci_95"],
            "truncation_rate": know_results["truncation_rate"],
            "extractable_rate": know_results["extractable_rate"],
            "pred_dist": know_results["pred_dist"],
            "val_key_dist": know_results["key_dist"],
            "train_key_dist": dict(know_train_keys),
            "always_a_acc": know_results["always_a_acc"],
            "most_common_acc": know_results["most_common_acc"],
            "shuffled_accs": know_shuffled_accs,
            "shuffled_avg": round(sum(know_shuffled_accs) / len(know_shuffled_accs), 2),
        },
        "knowledge_qa": {
            "total": len(kqa_val),
            "exact_match_acc": round(em_acc, 2),
            "avg_token_f1": round(avg_f1, 2),
            "containment_acc": round(cont_acc, 2),
            "truncation_rate": round(qa_trunc_rate, 2),
            "disagreement_count": len(disagreements),
            "sample_disagreements": disagreements[:25],
        },
    }

    out_path = REPO_ROOT / "reports" / "step2" / "f8_evaluation_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSaved evaluation results to {out_path}")
    print("\n=== SUMMARY OF RESULTS ===")
    print(f"Science MCQ Accuracy: {sci_results['accuracy']}% [95% CI: {sci_results['ci_95']}]")
    print(f"  Predicted Distribution: {sci_results['pred_dist']}")
    print(f"  Validation Keys: {sci_results['key_dist']}")
    print(f"  Train Keys: {dict(sci_train_keys)}")
    print(
        f"  Always A: {sci_results['always_a_acc']}% | Most common key: {sci_results['most_common_acc']}%"
    )
    print(f"  Shuffled Avg (3 perms): {summary['science_mcq']['shuffled_avg']}%")
    print(f"Knowledge MCQ Accuracy: {know_results['accuracy']}% [95% CI: {know_results['ci_95']}]")
    print(f"  Predicted Distribution: {know_results['pred_dist']}")
    print(f"  Validation Keys: {know_results['key_dist']}")
    print(f"  Train Keys: {dict(know_train_keys)}")
    print(
        f"  Always A: {know_results['always_a_acc']}% | Most common key: {know_results['most_common_acc']}%"
    )
    print(f"  Shuffled Avg (3 perms): {summary['knowledge_mcq']['shuffled_avg']}%")
    print("Knowledge QA (n=300):")
    print(f"  Exact Match: {em_acc:.2f}%")
    print(f"  Token F1: {avg_f1:.2f}%")
    print(f"  Containment: {cont_acc:.2f}%")
    print(f"  Disagreements: {len(disagreements)} cases")


if __name__ == "__main__":
    from collections import Counter

    main()
