"""A4 / G4: Knowledge QA Evaluation & Re-scoring under the Frozen Scoring Specification.

Evaluates all 300 validation items of knowledge_qa on Qwen2.5-0.5B-Instruct with BM25:
- Prompt explicitly instructs: "Answer with only the direct factual value (e.g. date, number, or name). Do not write full sentences or explanations."
- Assistant prefill: "Answer:"
- Token cap: 32
- Frozen Primary Metric: Span-extracted normalized exact match with strict date comparison (year-only NOT credited for full date) and number normalization.
- Compares side-by-side with old exact match, token F1, and containment.
- Reports 10 raw outputs per question family and lists 20 disagreement cases.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, ".")
from evaluation.prompts import extract_question_text  # noqa: E402
from evaluation.retrieval import BM25Retriever  # noqa: E402
from evaluation.suite import load_suite_partition  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def normalize_text_basic(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(?:the|a|an)\s+", "", s)
    s = re.sub(r"[.,;:'\"!?]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_number_str(s: str) -> str:
    s = re.sub(r"(?<=\d),(?=\d)", "", s)
    m = re.match(r"^(\d+(?:\.\d+)?)\s*million$", s.lower())
    if m:
        val = float(m.group(1)) * 1_000_000
        return str(int(val))
    return s


def parse_date_strict(s: str) -> tuple[Any | None, str]:
    clean = normalize_text_basic(s)
    if re.fullmatch(r"\d{4}", clean):
        try:
            val = int(clean)
            if 100 <= val <= 2100:
                return val, "year_only"
        except ValueError:
            pass

    fmts = (
        "%d %B %Y",
        "%B %d %Y",
        "%B %d, %Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%b %d %Y",
        "%b %d, %Y",
    )
    for fmt in fmts:
        try:
            dt = datetime.strptime(clean, fmt).date()
            return dt, "full_date"
        except ValueError:
            pass
    return None, "none"


def extract_answer_span(raw_text: str) -> str:
    """Isolate candidate answer value from potential conversational wrappers."""
    clean = raw_text.strip()
    clean = re.sub(r"^(?:Answer:|\s*:\s*)\s*", "", clean, flags=re.IGNORECASE).strip()
    patterns = [
        r"(?i)^(?:the\s+)?answer\s*(?:is|:|=)\s*",
        r"(?i)^according\s+to\s+(?:the\s+)?(?:context|passage|text)[,\s]+(?:the\s+answer\s+is\s+)?",
        r"(?i)^.*?\bwas\s+born\s+(?:on|in)\s+",
        r"(?i)^.*?\bdied\s+(?:on|in)\s+",
        r"(?i)^.*?\b(?:the\s+)?profession\s+(?:or\s+occupation\s+)?of\s+.*?\s+was\s+",
        r"(?i)^.*?\b(?:the\s+)?reported\s+population\s+(?:of\s+.*?\s+)?was\s+",
        r"(?i)^.*?\b(?:the\s+)?award\s+(?:or\s+prize\s+)?.*?\s+received\s+was\s+",
        r"(?i)^.*?\bwas\s+founded\s+in\s+",
        r"(?i)^.*?\bwas\s+released\s+in\s+",
    ]
    for pat in patterns:
        m = re.search(pat, clean)
        if m:
            clean = clean[m.end() :].strip()
            break

    clean = re.sub(r",\s*aged\s+\d+.*$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"[.,;:'\"!?]+$", "", clean).strip()
    return clean


def score_frozen_exact_match(pred: str, target: str, aliases: list[str] | None = None) -> bool:
    span = extract_answer_span(pred)
    norm_pred = normalize_number_str(normalize_text_basic(span))
    norm_target = normalize_number_str(normalize_text_basic(target))

    if norm_pred == norm_target:
        return True

    if aliases:
        for al in aliases:
            if norm_pred == normalize_number_str(normalize_text_basic(al)):
                return True

    dt_target, gran_target = parse_date_strict(target)
    if gran_target != "none":
        dt_pred, gran_pred = parse_date_strict(span)
        if gran_target == "full_date":
            return gran_pred == "full_date" and dt_pred == dt_target
        elif gran_target == "year_only":
            return gran_pred == "year_only" and dt_pred == dt_target

    num_pred = re.sub(r"[^\d.-]", "", norm_pred)
    num_target = re.sub(r"[^\d.-]", "", norm_target)
    if num_pred and num_target and num_pred == num_target:
        return True

    return False


def score_old_exact_match(pred: str, target: str) -> bool:
    np = normalize_number_str(normalize_text_basic(pred))
    nt = normalize_number_str(normalize_text_basic(target))
    return np == nt


def score_token_f1(pred: str, target: str) -> float:
    span = extract_answer_span(pred)
    np = normalize_text_basic(normalize_number_str(span))
    nt = normalize_text_basic(normalize_number_str(target))
    pred_tokens = re.findall(r"\w+", np)
    gold_tokens = re.findall(r"\w+", nt)
    if not pred_tokens or not gold_tokens:
        return 1.0 if pred_tokens == gold_tokens else 0.0
    common = set(pred_tokens) & set(gold_tokens)
    num_same = sum(min(pred_tokens.count(w), gold_tokens.count(w)) for w in common)
    if num_same == 0:
        return 0.0
    p = num_same / len(pred_tokens)
    r = num_same / len(gold_tokens)
    return (2 * p * r) / (p + r)


def score_containment(pred: str, target: str) -> bool:
    np = normalize_number_str(normalize_text_basic(pred))
    nt = normalize_number_str(normalize_text_basic(target))
    words = np.split()
    if len(words) > 8:
        return False
    if ("," in pred or ";" in pred or " and " in pred) and (
        "," not in target and " and " not in target
    ):
        return False
    return nt in np


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

    val_items = load_suite_partition("validation", group="knowledge_qa")
    print(f"Loaded {len(val_items)} knowledge_qa validation items.")

    corpus_path = REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl"
    retriever = BM25Retriever.from_jsonl(corpus_path)

    records = []
    frozen_em_count = 0
    old_em_count = 0
    f1_total = 0.0
    containment_count = 0

    outputs_by_family: dict[str, list[dict[str, Any]]] = {}

    for it in val_items:
        augmented_prompt, _ = retriever.augment_knowledge_qa_prompt(it, top_k=3)
        question = extract_question_text(it)
        target = it["target"]
        fam = it.get("rule_family", "general")
        aliases = it.get("aliases") or it.get("metadata", {}).get("aliases", [])

        user_content = f"Context:\n{augmented_prompt.split('Context:\n')[1].split('\n\nQuestion:')[0]}\n\nQuestion: {question}"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a factual question answering assistant. "
                    "Answer with only the direct factual value (e.g. date, number, or name). "
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
        raw_out = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        frozen_em = score_frozen_exact_match(raw_out, target, aliases=aliases)
        old_em = score_old_exact_match(raw_out, target)
        f1 = score_token_f1(raw_out, target)
        cont = score_containment(raw_out, target)

        if frozen_em:
            frozen_em_count += 1
        if old_em:
            old_em_count += 1
        f1_total += f1
        if cont:
            containment_count += 1

        rec = {
            "item_id": it["item_id"],
            "rule_family": fam,
            "question": question,
            "target": target,
            "raw_output": raw_out,
            "extracted_span": extract_answer_span(raw_out),
            "frozen_exact_match": frozen_em,
            "old_exact_match": old_em,
            "token_f1": round(f1, 4),
            "containment": cont,
        }
        records.append(rec)

        if fam not in outputs_by_family:
            outputs_by_family[fam] = []
        if len(outputs_by_family[fam]) < 10:
            outputs_by_family[fam].append(
                {
                    "item_id": it["item_id"],
                    "target": target,
                    "raw_output": raw_out,
                    "extracted_span": extract_answer_span(raw_out),
                    "frozen_em": frozen_em,
                }
            )

    total = len(val_items)
    res_summary = {
        "total": total,
        "frozen_exact_match_acc": round(frozen_em_count / total * 100, 2),
        "old_exact_match_acc": round(old_em_count / total * 100, 2),
        "mean_token_f1": round(f1_total / total * 100, 2),
        "containment_acc": round(containment_count / total * 100, 2),
        "outputs_by_family": outputs_by_family,
        "disagreements": [
            r
            for r in records
            if not (r["frozen_exact_match"] == r["old_exact_match"] == r["containment"])
        ][:25],
    }

    out_file = REPO_ROOT / "reports" / "step2" / "qa_frozen_spec_rescore.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res_summary, f, indent=2)

    print("\n" + "=" * 80)
    print("A4: KNOWLEDGE QA RESCORE UNDER FROZEN SCORING SPECIFICATION")
    print("=" * 80)
    print(f"Total Items: {total}")
    print(
        f"Frozen Exact Match (Primary Metric): {res_summary['frozen_exact_match_acc']}% ({frozen_em_count}/{total})"
    )
    print(
        f"Old Exact Match (Without Span Normalization): {res_summary['old_exact_match_acc']}% ({old_em_count}/{total})"
    )
    print(f"Mean Token F1: {res_summary['mean_token_f1']}%")
    print(f"Containment Accuracy: {res_summary['containment_acc']}% ({containment_count}/{total})")
    print(f"Disagreements between metrics: {len(res_summary['disagreements'])} items sampled")
    print(f"Saved full audit report to {out_file}")


if __name__ == "__main__":
    main()
