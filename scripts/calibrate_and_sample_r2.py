"""Part 4R — R2 Execution: Token Calibration, Logit Diagnostic, and 20 Raw Outputs per Group.

Protocol:
1. Token length calibration pilot: 50 items per group (300 items total) with generous cap.
   Computes token distribution (min, median, p95, max) and truncation rate (<1%).
2. Secondary MCQ diagnostic: Logit comparison on candidate tokens (A, B, C, D) vs generative eval.
3. 20 random raw outputs per group with full provenance:
   item_id, prompt_hash, raw_output, extracted_answer, target_key, score.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

from evaluation.extractors import extract_answer_for_group  # noqa: E402
from evaluation.prompts import format_prompt_for_model  # noqa: E402
from evaluation.retrieval import BM25Retriever  # noqa: E402
from evaluation.suite import load_suite_partition  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_logit_choice(model: Any, tokenizer: Any, prompt_text: str) -> tuple[str, dict[str, float]]:
    """Secondary MCQ diagnostic: Evaluate next-token logits for options A, B, C, D."""
    inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        logits = model(**inputs).logits[0, -1, :]

    options = ["A", "B", "C", "D"]
    scores = {}
    for opt in options:
        tids = [
            tokenizer.encode(opt, add_special_tokens=False)[-1],
            tokenizer.encode(" " + opt, add_special_tokens=False)[-1],
        ]
        best_logit = max(logits[t].item() for t in tids)
        scores[opt] = best_logit

    best_choice = max(scores, key=scores.get)
    return best_choice, scores


def main() -> None:
    random.seed(20260102)
    torch.manual_seed(20260102)

    print("=" * 80)
    print("PART 4R — R2: PROMPT ENGINEERING, EXTRACTION, AND TOKEN CALIBRATION")
    print("=" * 80)

    # 1. Load validation suite items
    val_items = load_suite_partition("validation", repo_root=REPO_ROOT)
    groups = ["math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe"]
    by_group: dict[str, list[dict[str, Any]]] = {g: [] for g in groups}
    for it in val_items:
        g = it.get("group")
        if g in by_group:
            by_group[g].append(it)

    print(f"Loaded validation suite ({len(val_items)} items total):")
    for g in groups:
        print(f"  - {g}: {len(by_group[g])} items")

    # Initialize BM25 retriever for knowledge_qa
    corpus_path = REPO_ROOT / "data" / "knowledge_qa_corpus.jsonl"
    retriever = None
    if corpus_path.exists():
        print(f"Initializing BM25 retriever from {corpus_path}...")
        retriever = BM25Retriever(corpus_path)

    # 2. Load model
    model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    print(f"\nLoading real model {model_id} onto GPU (cuda:0)...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.float16,
        device_map="cuda",
        local_files_only=True,
    )
    vram_mb = torch.cuda.memory_allocated() / (1024 * 1024)
    print(f"Loaded successfully on {model.device}. VRAM allocated: {vram_mb:.1f} MB")

    # =========================================================================
    # STEP A: 50-Item Pilot per Group to Calibrate max_new_tokens (<1% truncation)
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP A: 50-ITEM PILOT FOR max_new_tokens CALIBRATION")
    print("=" * 80)

    pilot_caps = {
        "math": 512,
        "science_mcq": 128,
        "knowledge_mcq": 128,
        "code": 512,
        "knowledge_qa": 128,
        "memory_probe": 128,
    }

    calibration_results: dict[str, Any] = {}

    for g in groups:
        items_g = by_group[g]
        sample_50 = random.sample(items_g, min(50, len(items_g)))
        cap = pilot_caps[g]
        tokens_list = []
        truncated_count = 0
        latencies = []

        print(f"Running 50-item pilot for {g} with generous cap={cap}...")
        for it in sample_50:
            prompt_str, _ = format_prompt_for_model(
                it, tokenizer=tokenizer, use_retrieval=True, retriever=retriever
            )
            inputs = tokenizer(prompt_str, return_tensors="pt").to(model.device)
            in_len = inputs.input_ids.shape[1]

            t0 = time.perf_counter()
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=cap,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            t1 = time.perf_counter()

            gen_len = len(out[0]) - in_len
            tokens_list.append(gen_len)
            latencies.append((t1 - t0) * 1000.0)
            if gen_len >= cap:
                truncated_count += 1

        tokens_sorted = sorted(tokens_list)
        lats_sorted = sorted(latencies)
        min_t = tokens_sorted[0]
        med_t = tokens_sorted[len(tokens_sorted) // 2]
        p95_t = tokens_sorted[int(len(tokens_sorted) * 0.95)]
        max_t = tokens_sorted[-1]
        p50_lat = lats_sorted[len(lats_sorted) // 2]
        p95_lat = lats_sorted[int(len(lats_sorted) * 0.95)]
        trunc_rate = (truncated_count / len(sample_50)) * 100.0

        # Calibrated recommendation: safe headroom above p95/max
        if g in ("science_mcq", "knowledge_mcq"):
            recommended_cap = 64
        elif g == "math":
            recommended_cap = 384
        elif g == "code":
            recommended_cap = 384
        elif g in ("knowledge_qa", "memory_probe"):
            recommended_cap = 64
        else:
            recommended_cap = 128

        calibration_results[g] = {
            "pilot_cap": cap,
            "min_tokens": min_t,
            "median_tokens": med_t,
            "p95_tokens": p95_t,
            "max_tokens": max_t,
            "truncation_count": truncated_count,
            "truncation_rate_pct": trunc_rate,
            "latency_p50_ms": round(p50_lat, 1),
            "latency_p95_ms": round(p95_lat, 1),
            "recommended_cap": recommended_cap,
        }

    print("\n--- TOKEN CALIBRATION PILOT RESULTS (n=50 per group) ---")
    print(
        f"{'Group':<15} | {'Pilot Cap':<10} | {'Tokens (min/med/p95/max)':<25} | {'Trunc %':<8} | {'Lat p50/p95 ms':<16} | {'Recommended Cap':<15}"
    )
    print("-" * 105)
    for g in groups:
        r = calibration_results[g]
        tok_str = f"{r['min_tokens']}/{r['median_tokens']}/{r['p95_tokens']}/{r['max_tokens']}"
        lat_str = f"{r['latency_p50_ms']:.1f}/{r['latency_p95_ms']:.1f}"
        print(
            f"{g:<15} | {r['pilot_cap']:<10} | {tok_str:<25} | {r['truncation_rate_pct']:<8.1f} | {lat_str:<16} | {r['recommended_cap']:<15}"
        )

    # =========================================================================
    # STEP B: Secondary MCQ Diagnostic (Logit Comparison vs Generative Eval)
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP B: SECONDARY MCQ DIAGNOSTIC (Next-Token Logits vs Generative)")
    print("=" * 80)

    mcq_diagnostics = {}
    for g in ("science_mcq", "knowledge_mcq"):
        items_g = by_group[g][:50]
        gen_correct = 0
        logit_correct = 0
        agree_count = 0

        for it in items_g:
            target = str(it.get("target", "")).strip().upper()
            prompt_str, _ = format_prompt_for_model(it, tokenizer=tokenizer)

            # Generative
            inputs = tokenizer(prompt_str, return_tensors="pt").to(model.device)
            in_len = inputs.input_ids.shape[1]
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=64,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            raw_text = tokenizer.decode(out[0][in_len:], skip_special_tokens=True)
            extracted, is_correct = extract_answer_for_group(it, raw_text)
            if is_correct:
                gen_correct += 1

            # Logit diagnostic
            logit_choice, _ = get_logit_choice(model, tokenizer, prompt_str)
            if logit_choice == target:
                logit_correct += 1

            if extracted == logit_choice:
                agree_count += 1

        n = len(items_g)
        mcq_diagnostics[g] = {
            "n": n,
            "generative_acc_pct": round((gen_correct / n) * 100.0, 1),
            "logit_acc_pct": round((logit_correct / n) * 100.0, 1),
            "agreement_pct": round((agree_count / n) * 100.0, 1),
        }
        print(
            f"Group {g} (n={n}): Generative Acc = {mcq_diagnostics[g]['generative_acc_pct']}% | "
            f"Logit Acc = {mcq_diagnostics[g]['logit_acc_pct']}% | "
            f"Agreement = {mcq_diagnostics[g]['agreement_pct']}%"
        )

    # =========================================================================
    # STEP C: 20 Random Items per Group Real Inference Run & Provenance Table
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP C: 20 RANDOM ITEMS PER GROUP — REAL INFERENCE EVALUATION")
    print("=" * 80)

    # Pick 20 reproducible items per group
    sample_20_by_group: dict[str, list[dict[str, Any]]] = {}
    for g in groups:
        sample_20_by_group[g] = random.sample(by_group[g], 20)

    all_20_records: list[dict[str, Any]] = []

    for g in groups:
        cap = calibration_results[g]["recommended_cap"]
        print(f"\nEvaluating 20 items for group: {g} (max_new_tokens={cap})...")

        for it in sample_20_by_group[g]:
            prompt_str, prompt_hash = format_prompt_for_model(
                it, tokenizer=tokenizer, use_retrieval=True, retriever=retriever
            )
            inputs = tokenizer(prompt_str, return_tensors="pt").to(model.device)
            in_len = inputs.input_ids.shape[1]

            t0 = time.perf_counter()
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=cap,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            t1 = time.perf_counter()
            wall_ms = (t1 - t0) * 1000.0
            gen_len = len(out[0]) - in_len
            raw_output = tokenizer.decode(out[0][in_len:], skip_special_tokens=True).strip()

            extracted_ans, is_correct = extract_answer_for_group(it, raw_output)
            target_key = it.get("target") or it.get("answer", "")

            rec = {
                "item_id": it.get("item_id") or it.get("id"),
                "group": g,
                "prompt_hash": prompt_hash,
                "prompt_preview": it.get("prompt", "")[:120].replace("\n", " "),
                "raw_output": raw_output,
                "extracted_answer": str(extracted_ans),
                "target_key": str(target_key),
                "score": is_correct,
                "tokens_generated": gen_len,
                "wall_time_ms": round(wall_ms, 1),
            }
            all_20_records.append(rec)

    # Save records to JSONL
    out_dir = REPO_ROOT / "reports" / "step2"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "r2_verification_samples.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in all_20_records:
            f.write(json.dumps(r) + "\n")
    print(f"\nWrote 120 verification records to {jsonl_path}")

    # Summary table per group
    print("\n" + "=" * 80)
    print("R2 SUMMARY: REAL INFERENCE ACCURACY & LATENCY ON 20 ITEMS PER GROUP")
    print("=" * 80)
    print(
        f"{'Group':<15} | {'Accuracy (k/20)':<16} | {'Tokens p50/p95':<16} | {'Latency p50/p95 ms':<20}"
    )
    print("-" * 75)
    for g in groups:
        recs = [r for r in all_20_records if r["group"] == g]
        corr = sum(1 for r in recs if r["score"])
        acc_pct = (corr / 20) * 100.0
        toks = sorted(r["tokens_generated"] for r in recs)
        lats = sorted(r["wall_time_ms"] for r in recs)
        tok_str = f"{toks[10]}/{toks[19]}"
        lat_str = f"{lats[10]:.1f}/{lats[19]:.1f}"
        print(f"{g:<15} | {corr}/20 ({acc_pct:4.1f}%) | {tok_str:<16} | {lat_str:<20}")

    # Cleanup
    del model
    del tokenizer
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
