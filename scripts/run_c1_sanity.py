"""Phase C - Step C1: 100-Item FP16 vs 4-Bit NF4 Sanity Evaluation.

Compares unquantized FP16 vs bitsandbytes 4-bit NF4 quantization on 100 validation items:
- Measures accuracy change (Delta Acc)
- Measures latency (p50, p95, ms/tok)
- Measures VRAM footprint (NVML process used, PyTorch allocated, PyTorch reserved)
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.extractors import extract_answer_for_group  # noqa: E402
from evaluation.metrics import get_vram_breakdown_mb, percentile_latency  # noqa: E402
from evaluation.retrieval import BM25Retriever  # noqa: E402
from scripts.run_phase_b_pilot import format_prompt_for_model  # noqa: E402


def load_100_validation_sample(seed: int = 20260102) -> list[dict[str, Any]]:
    random.seed(seed)
    groups = ["math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe"]
    by_group: dict[str, list[dict[str, Any]]] = {}

    for g in groups:
        path = REPO_ROOT / "suite" / "validation" / f"{g}.jsonl"
        with open(path, encoding="utf-8") as f:
            by_group[g] = [json.loads(line) for line in f]

    sample: list[dict[str, Any]] = []

    # math: 20 items
    sample.extend(random.sample(by_group["math"], 20))
    # science_mcq: 20 items
    sample.extend(random.sample(by_group["science_mcq"], 20))
    # knowledge_mcq: 20 items
    sample.extend(random.sample(by_group["knowledge_mcq"], 20))
    # code: 10 items
    sample.extend(random.sample(by_group["code"], 10))

    # knowledge_qa: 20 items (13 wiki + 7 fictional)
    kqa = by_group["knowledge_qa"]
    wiki = [it for it in kqa if it.get("arm") == "real_wikipedia"]
    fict = [it for it in kqa if it.get("arm") == "fictional_entity"]
    sample.extend(random.sample(wiki, 13) + random.sample(fict, 7))

    # memory_probe: 10 items (7 stale + 3 static)
    mem = by_group["memory_probe"]
    stale = [it for it in mem if it.get("metadata", {}).get("stale_values")]
    static = [it for it in mem if not it.get("metadata", {}).get("stale_values")]
    sample.extend(random.sample(stale, 7) + random.sample(static, 3))

    assert len(sample) == 100, f"Expected 100 items, got {len(sample)}"
    return sample


def evaluate_model(
    model: Any,
    tokenizer: Any,
    items: list[dict[str, Any]],
    retriever: BM25Retriever,
    precision_label: str,
) -> dict[str, Any]:
    caps = {
        "math": 768,
        "science_mcq": 32,
        "knowledge_mcq": 32,
        "code": 1024,
        "knowledge_qa": 128,
        "memory_probe": 128,
    }

    # Warmup
    _ = model.generate(torch.tensor([[100, 200]], device=model.device), max_new_tokens=5)

    vram_breakdown = get_vram_breakdown_mb()

    results: list[dict[str, Any]] = []
    latencies: list[float] = []
    tokens_gen: list[int] = []
    correct_count = 0

    for it in items:
        g = it.get("group", "")
        cap = caps.get(g, 128)

        prompt_str, prompt_hash, _ = format_prompt_for_model(
            it, tokenizer=tokenizer, use_retrieval=True, retriever=retriever
        )
        inputs = tokenizer(prompt_str, return_tensors="pt").to(model.device)
        in_len = inputs.input_ids.shape[1]

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": cap,
            "do_sample": False,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if g in ("science_mcq", "knowledge_mcq"):
            gen_kwargs["eos_token_id"] = [tokenizer.eos_token_id, 198, 271]

        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(**inputs, **gen_kwargs)
        t1 = time.perf_counter()
        wall_ms = (t1 - t0) * 1000.0
        gen_len = len(out[0]) - in_len
        raw_output = tokenizer.decode(out[0][in_len:], skip_special_tokens=True).strip()

        extracted, is_correct = extract_answer_for_group(it, raw_output)
        if is_correct:
            correct_count += 1

        latencies.append(wall_ms)
        tokens_gen.append(gen_len)

        results.append(
            {
                "item_id": it.get("id"),
                "group": g,
                "arm": it.get("arm", "public"),
                "tokens": gen_len,
                "wall_ms": wall_ms,
                "score": is_correct,
            }
        )

    tot_toks = sum(tokens_gen)
    tot_ms = sum(latencies)
    ms_per_tok = tot_ms / max(1, tot_toks)

    p50_lat = percentile_latency([{"wall_time_ms": lat} for lat in latencies], 50)
    p95_lat = percentile_latency([{"wall_time_ms": lat} for lat in latencies], 95)

    return {
        "precision": precision_label,
        "n": len(items),
        "correct": correct_count,
        "accuracy_pct": round(correct_count / len(items) * 100.0, 2),
        "total_tokens": tot_toks,
        "ms_per_token": round(ms_per_tok, 2),
        "p50_latency_ms": round(p50_lat, 1) if p50_lat is not None else 0.0,
        "p95_latency_ms": round(p95_lat, 1) if p95_lat is not None else 0.0,
        "vram_breakdown": vram_breakdown,
        "results": results,
    }


def main():
    print("=" * 80)
    print("PHASE C - STEP C1: 100-ITEM FP16 vs 4-BIT NF4 SANITY CHECK")
    print("=" * 80)

    model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    print(f"Candidate: {model_id}")

    # Build retriever
    corpus_files = [
        REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl",
        REPO_ROOT / "data" / "fictional_abstracts_corpus.jsonl",
    ]
    corpus_paths = [p for p in corpus_files if p.exists()]
    retriever = BM25Retriever.from_jsonl(corpus_paths)

    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    items = load_100_validation_sample(seed=20260102)

    # 1. Run FP16
    print("\n[1/2] Loading model in unquantized FP16...")
    model_fp16 = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.float16,
        device_map="cuda",
        local_files_only=True,
    )
    print("Evaluating 100 items on FP16...")
    res_fp16 = evaluate_model(model_fp16, tokenizer, items, retriever, "FP16")
    del model_fp16
    torch.cuda.empty_cache()

    # 2. Run 4-Bit NF4
    print("\n[2/2] Loading model in 4-bit NF4 (bitsandbytes)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )
    model_4bit = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="cuda",
        local_files_only=True,
    )
    print("Evaluating 100 items on 4-bit NF4...")
    res_4bit = evaluate_model(model_4bit, tokenizer, items, retriever, "4-bit NF4")
    del model_4bit
    torch.cuda.empty_cache()

    delta_acc = res_4bit["accuracy_pct"] - res_fp16["accuracy_pct"]

    print("\n" + "=" * 80)
    print("C1 SANITY CHECK SUMMARY RESULTS")
    print("=" * 80)
    print(f"Model: {model_id} | Sample: n={len(items)} validation items")
    print(
        f"FP16 Accuracy:       {res_fp16['correct']}/{res_fp16['n']} ({res_fp16['accuracy_pct']}%)"
    )
    print(
        f"4-bit NF4 Accuracy:  {res_4bit['correct']}/{res_4bit['n']} ({res_4bit['accuracy_pct']}%)"
    )
    print(f"Delta Accuracy:      {delta_acc:+.2f} pp")
    print(
        f"FP16 Latency p50:    {res_fp16['p50_latency_ms']} ms ({res_fp16['ms_per_token']} ms/tok)"
    )
    print(
        f"4-bit Latency p50:   {res_4bit['p50_latency_ms']} ms ({res_4bit['ms_per_token']} ms/tok)"
    )
    print(
        f"FP16 Peak VRAM:      NVML: {res_fp16['vram_breakdown']['nvml_process_used_mb']} MB | Torch: {res_fp16['vram_breakdown']['torch_allocated_mb']:.1f} MB"
    )
    print(
        f"4-bit Peak VRAM:     NVML: {res_4bit['vram_breakdown']['nvml_process_used_mb']} MB | Torch: {res_4bit['vram_breakdown']['torch_allocated_mb']:.1f} MB"
    )

    out_file = REPO_ROOT / "reports" / "step2" / "c1_sanity_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model": model_id,
                "n": len(items),
                "fp16": {
                    "accuracy_pct": res_fp16["accuracy_pct"],
                    "correct": res_fp16["correct"],
                    "p50_latency_ms": res_fp16["p50_latency_ms"],
                    "p95_latency_ms": res_fp16["p95_latency_ms"],
                    "ms_per_token": res_fp16["ms_per_token"],
                    "vram_breakdown": res_fp16["vram_breakdown"],
                },
                "4bit_nf4": {
                    "accuracy_pct": res_4bit["accuracy_pct"],
                    "correct": res_4bit["correct"],
                    "p50_latency_ms": res_4bit["p50_latency_ms"],
                    "p95_latency_ms": res_4bit["p95_latency_ms"],
                    "ms_per_token": res_4bit["ms_per_token"],
                    "vram_breakdown": res_4bit["vram_breakdown"],
                },
                "delta_accuracy_pp": round(delta_acc, 2),
            },
            f,
            indent=2,
        )
    print(f"\nWrote sanity summary to {out_file}")


if __name__ == "__main__":
    main()
