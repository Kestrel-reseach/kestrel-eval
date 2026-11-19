"""Fictional-entity Knowledge QA Pilot on Qwen2.5-0.5B-Instruct (Step A6).

Evaluates 50 fictional items across two conditions:
1. No-Retrieval (Parametric Only): Model receives only the question.
   Expected: ~0% accuracy because entities are completely fictional.
2. Retrieval (BM25 top-3 over combined 5,090-article corpus):
   Measures BM25 Recall@3 and retrieval-augmented accuracy under frozen exact match.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.extractors import extract_answer_span, score_frozen_exact_match  # noqa: E402
from evaluation.retrieval import BM25Retriever  # noqa: E402
from evaluation.suite import load_suite_partition  # noqa: E402


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    print(f"Loading {model_name} on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map=device,
        local_files_only=True,
    )
    model.eval()

    # Load validation knowledge_qa items and filter to fictional_entity arm
    val_items = load_suite_partition("validation", group="knowledge_qa")
    fict_items = [it for it in val_items if it.get("arm") == "fictional_entity"][:50]
    print(f"Loaded {len(fict_items)} fictional-entity validation items for pilot.")

    # Build BM25 index over combined corpus: Wikipedia 5k + Fictional Abstracts
    wiki_corpus = REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl"
    fict_corpus = REPO_ROOT / "data" / "fictional_abstracts_corpus.jsonl"
    print(f"Building BM25 index over combined corpus ({wiki_corpus.name} + {fict_corpus.name})...")
    retriever = BM25Retriever.from_jsonl([wiki_corpus, fict_corpus])
    print(f"Total documents indexed in BM25: {len(retriever.docs)}")

    results = []
    no_retrieval_correct = 0
    retrieval_correct = 0
    recall_hits = 0

    system_prompt = (
        "You are a factual question answering assistant. "
        "Answer with only the direct factual value (e.g. date, number, or name). "
        "Do not write full sentences or explanations."
    )

    for idx, it in enumerate(fict_items, 1):
        question = (
            it.get("question")
            or it.get("prompt", "").split("Question:")[-1].split("Answer:")[0].strip()
        )
        target = it["target"]
        passage_id = it.get("metadata", {}).get("passage_id", "")
        passage_title = it.get("metadata", {}).get("passage_title", "")
        rule_fam = it.get("template_family", "general")

        # Condition 1: No-Retrieval
        no_ret_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"},
        ]
        no_ret_prompt = (
            tokenizer.apply_chat_template(
                no_ret_messages, tokenize=False, add_generation_prompt=True
            )
            + "Answer:"
        )
        inputs_no_ret = tokenizer(no_ret_prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out_no_ret = model.generate(
                **inputs_no_ret,
                max_new_tokens=32,
                do_sample=False,
                eos_token_id=[tokenizer.eos_token_id, 198, 271],
            )
        gen_tokens_no_ret = out_no_ret[0][inputs_no_ret["input_ids"].shape[1] :]
        raw_no_ret = tokenizer.decode(gen_tokens_no_ret, skip_special_tokens=True).strip()
        no_ret_is_correct = score_frozen_exact_match(raw_no_ret, target)
        if no_ret_is_correct:
            no_retrieval_correct += 1

        # Condition 2: Retrieval (BM25 Top-3)
        retrieved_docs = retriever.retrieve(question, top_k=3)
        # Check recall@3: gold document title or passage_id in retrieved
        hit = any(
            doc["article_id"] == passage_id or passage_title.lower() in doc["title"].lower()
            for doc in retrieved_docs
        )
        if hit:
            recall_hits += 1

        context_blocks = "\n\n".join(f"[{doc['title']}]\n{doc['text']}" for doc in retrieved_docs)
        ret_messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context:\n{context_blocks}\n\nQuestion: {question}",
            },
        ]
        ret_prompt = (
            tokenizer.apply_chat_template(ret_messages, tokenize=False, add_generation_prompt=True)
            + "Answer:"
        )
        inputs_ret = tokenizer(ret_prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out_ret = model.generate(
                **inputs_ret,
                max_new_tokens=32,
                do_sample=False,
                eos_token_id=[tokenizer.eos_token_id, 198, 271],
            )
        gen_tokens_ret = out_ret[0][inputs_ret["input_ids"].shape[1] :]
        raw_ret = tokenizer.decode(gen_tokens_ret, skip_special_tokens=True).strip()
        ret_is_correct = score_frozen_exact_match(raw_ret, target)
        if ret_is_correct:
            retrieval_correct += 1

        results.append(
            {
                "index": idx,
                "item_id": it["id"],
                "rule_family": rule_fam,
                "entity_title": passage_title,
                "question": question,
                "target": target,
                "recall_hit": hit,
                "no_retrieval_raw": raw_no_ret,
                "no_retrieval_correct": no_ret_is_correct,
                "retrieval_raw": raw_ret,
                "retrieval_extracted_span": extract_answer_span(raw_ret),
                "retrieval_correct": ret_is_correct,
            }
        )

    n = len(fict_items)
    summary = {
        "n_items": n,
        "bm25_recall_at_3": round(recall_hits / n * 100, 2),
        "recall_hits": f"{recall_hits}/{n}",
        "no_retrieval_accuracy": round(no_retrieval_correct / n * 100, 2),
        "no_retrieval_score": f"{no_retrieval_correct}/{n}",
        "retrieval_accuracy": round(retrieval_correct / n * 100, 2),
        "retrieval_score": f"{retrieval_correct}/{n}",
        "retrieval_gain_pp": round((retrieval_correct - no_retrieval_correct) / n * 100, 2),
        "sample_cases": results[:15],
    }

    out_file = REPO_ROOT / "reports" / "step2" / "fictional_qa_pilot_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print("A6 FICTIONAL-ENTITY KNOWLEDGE QA PILOT (Qwen2.5-0.5B-Instruct)")
    print("=" * 80)
    print(f"Sample Size: {n} items")
    print(f"BM25 Recall@3 on Combined Corpus: {summary['bm25_recall_at_3']}% ({recall_hits}/{n})")
    print(
        f"No-Retrieval Accuracy: {summary['no_retrieval_accuracy']}% ({no_retrieval_correct}/{n})"
    )
    print(f"Retrieval Accuracy (BM25): {summary['retrieval_accuracy']}% ({retrieval_correct}/{n})")
    print(f"Clean Retrieval Gain: +{summary['retrieval_gain_pp']} pp")
    print(f"Saved full audit report to {out_file}")


if __name__ == "__main__":
    main()
