"""Evaluate Qwen3.5-0.8B on 100 validation sample items under C1 protocol."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from evaluation.retrieval import BM25Retriever
from scripts.run_c1_sanity import evaluate_model, load_100_validation_sample

REPO_ROOT = Path(__file__).resolve().parent.parent


def main():
    sample = load_100_validation_sample(seed=20260102)
    retriever = BM25Retriever.from_jsonl(REPO_ROOT / "data/wikipedia_abstracts_5k.jsonl")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    model_id = "Qwen/Qwen3.5-0.8B"
    print(f"Loading {model_id} from local cache...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="cuda:0",
        local_files_only=True,
    )

    print("Evaluating 100 validation items...")
    res = evaluate_model(model, tokenizer, sample, retriever, "nf4")

    out_path = REPO_ROOT / "reports/step2/qwen3.5_0.8b_100_sample.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    print(f"DONE! Accuracy: {res['accuracy_pct']}% ({res['correct']}/{res['n']})")
    print(
        f"Latency: p50={res['p50_latency_ms']} ms, p95={res['p95_latency_ms']} ms, ms/tok={res['ms_per_token']}"
    )
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
