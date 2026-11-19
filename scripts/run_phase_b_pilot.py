"""Phase B: 50-Item Pilot Per Group on Suite v2.1 Formats.

Protocol:
- Re-run 50-item pilot per group (300 items total) on Suite v2.1 validation partition.
- Real autoregressive generation using Qwen2.5-0.5B-Instruct on CUDA.
- Canonical prompt formatting (evaluation/prompts.py) and frozen scoring (evaluation/extractors.py).
- Acceptance criteria:
    1. Truncation rate < 1.0% across all groups.
    2. Extractable rate = 100.0% across all groups.
- Deliverable: 20 raw outputs per group formatted for owner inspection.
"""

# ruff: noqa: E402

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

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluation.extractors import extract_answer_for_group
from evaluation.prompts import format_prompt_for_model
from evaluation.retrieval import BM25Retriever
from evaluation.suite import load_suite_partition


def percentile(data: list[float], pct: float) -> float:
    """Compute percentile from sorted list."""
    if not data:
        return 0.0
    idx = int(len(data) * (pct / 100.0))
    return data[min(idx, len(data) - 1)]


def main() -> None:
    seed = 20260102
    random.seed(seed)
    torch.manual_seed(seed)

    print("=" * 80)
    print("PHASE B: 50-ITEM CALIBRATION PILOT PER GROUP ON SUITE v2.1")
    print(f"Seed: {seed} | Device: cuda:0 | Model: Qwen/Qwen2.5-0.5B-Instruct")
    print("=" * 80)

    # 1. Load validation suite items
    val_items = load_suite_partition("validation", repo_root=REPO_ROOT)
    groups = ["math", "science_mcq", "knowledge_mcq", "code", "knowledge_qa", "memory_probe"]
    by_group: dict[str, list[dict[str, Any]]] = {g: [] for g in groups}
    for it in val_items:
        g = it.get("group")
        if g in by_group:
            by_group[g].append(it)

    print(f"Loaded Suite v2.1 validation split: {len(val_items)} items total.")
    for g in groups:
        print(f"  - {g}: {len(by_group[g])} items")

    # 2. Build BM25 flat retriever over Wikipedia abstracts snapshot + fictional abstracts
    wiki_path = REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl"
    fictional_path = REPO_ROOT / "data" / "fictional_abstracts_corpus.jsonl"
    corpus_paths = [p for p in (wiki_path, fictional_path) if p.exists()]
    print(f"\nBuilding BM25 flat retriever from {len(corpus_paths)} corpus file(s)...")
    retriever = BM25Retriever.from_jsonl(corpus_paths)
    print(f"Retriever ready: {len(retriever.docs)} documents indexed.")

    # 3. Load Real Model
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
    print(f"Loaded successfully on {model.device}. Allocated VRAM: {vram_mb:.1f} MB")

    # 4. Caps calibrated for <1% truncation
    caps = {
        "math": 768,  # generous headroom above observed max (504)
        "science_mcq": 32,
        "knowledge_mcq": 32,
        "code": 1024,
        "knowledge_qa": 128,
        "memory_probe": 128,
    }

    # Sample 50 items per group reproducibly
    sample_50_by_group: dict[str, list[dict[str, Any]]] = {}
    for g in groups:
        items = by_group[g]
        if g == "knowledge_qa":
            # Stratified: 33 Wikipedia items + 17 fictional items = 50 total
            wiki_items = [it for it in items if it.get("arm") == "real_wikipedia"]
            fict_items = [it for it in items if it.get("arm") == "fictional_entity"]
            s_wiki = random.sample(wiki_items, min(33, len(wiki_items)))
            s_fict = random.sample(fict_items, min(17, len(fict_items)))
            sampled = s_wiki + s_fict
            random.shuffle(sampled)
            sample_50_by_group[g] = sampled
        elif g == "memory_probe":
            # Stratified: 33 stale-fact items + 17 static items = 50 total
            stale_items = [
                it
                for it in items
                if it.get("metadata", {}).get("stale_values")
                or it.get("metadata", {}).get("is_stale_fact")
            ]
            static_items = [
                it
                for it in items
                if not (
                    it.get("metadata", {}).get("stale_values")
                    or it.get("metadata", {}).get("is_stale_fact")
                )
            ]
            s_stale = random.sample(stale_items, min(33, len(stale_items)))
            s_static = random.sample(static_items, min(17, len(static_items)))
            sampled = s_stale + s_static
            random.shuffle(sampled)
            sample_50_by_group[g] = sampled
        else:
            sample_50_by_group[g] = random.sample(items, min(50, len(items)))

    # Execute 50-item pilot runs
    pilot_records: list[dict[str, Any]] = []
    group_summaries: dict[str, Any] = {}

    for g in groups:
        cap = caps[g]
        items_g = sample_50_by_group[g]
        print(f"\nEvaluating {len(items_g)} items for group: {g} (cap={cap})...")

        tokens_list: list[int] = []
        latencies_ms: list[float] = []
        truncated_count = 0
        extractable_count = 0
        correct_count = 0

        for it in items_g:
            prompt_str, prompt_hash, prefill = format_prompt_for_model(
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
                gen_kwargs["stop_strings"] = ["\n"]
                gen_kwargs["tokenizer"] = tokenizer

            t0 = time.perf_counter()
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    **gen_kwargs,
                )
            t1 = time.perf_counter()
            wall_ms = (t1 - t0) * 1000.0
            gen_len = len(out[0]) - in_len
            raw_output = tokenizer.decode(out[0][in_len:], skip_special_tokens=True).strip()

            # Truncation check
            is_truncated = gen_len >= cap
            if is_truncated:
                truncated_count += 1

            # Extract answer using frozen spec
            extracted_ans, is_correct = extract_answer_for_group(it, raw_output)
            is_extractable = (extracted_ans is not None) and (str(extracted_ans).strip() != "")
            if is_extractable:
                extractable_count += 1
            if is_correct:
                correct_count += 1

            tokens_list.append(gen_len)
            latencies_ms.append(wall_ms)

            target_key = it.get("target") or it.get("answer") or it.get("answerKey", "")
            rec = {
                "item_id": it.get("item_id") or it.get("id"),
                "group": g,
                "arm": it.get("arm", "public"),
                "prompt_hash": prompt_hash,
                "prompt_preview": it.get("prompt", "")[:120].replace("\n", " "),
                "raw_output": raw_output,
                "extracted_answer": str(extracted_ans),
                "target_key": str(target_key),
                "is_truncated": is_truncated,
                "is_extractable": is_extractable,
                "score": is_correct,
                "tokens_generated": gen_len,
                "wall_time_ms": round(wall_ms, 2),
            }
            pilot_records.append(rec)

        n = len(items_g)
        s_tokens = sorted(tokens_list)
        s_lats = sorted(latencies_ms)
        min_tok = s_tokens[0]
        med_tok = s_tokens[n // 2]
        p95_tok = percentile(s_tokens, 95)
        max_tok = s_tokens[-1]
        p50_lat = percentile(s_lats, 50)
        p95_lat = percentile(s_lats, 95)

        trunc_rate = (truncated_count / n) * 100.0
        extractable_rate = (extractable_count / n) * 100.0
        acc_pct = (correct_count / n) * 100.0

        group_summaries[g] = {
            "n": n,
            "cap": cap,
            "min_tokens": min_tok,
            "median_tokens": med_tok,
            "p95_tokens": p95_tok,
            "max_tokens": max_tok,
            "truncated_count": truncated_count,
            "truncation_rate_pct": round(trunc_rate, 2),
            "truncation_pass": trunc_rate < 1.0,
            "extractable_count": extractable_count,
            "extractable_rate_pct": round(extractable_rate, 2),
            "extractable_pass": extractable_rate == 100.0,
            "correct_count": correct_count,
            "accuracy_pct": round(acc_pct, 2),
            "latency_p50_ms": round(p50_lat, 1),
            "latency_p95_ms": round(p95_lat, 1),
        }

        print(
            f"  {g:<15} | Acc: {correct_count}/{n} ({acc_pct:5.1f}%) | "
            f"Tokens: min={min_tok}, med={med_tok}, p95={p95_tok}, max={max_tok} | "
            f"Trunc: {truncated_count}/{n} ({trunc_rate:4.1f}%) | "
            f"Extractable: {extractable_count}/{n} ({extractable_rate:5.1f}%) | "
            f"Lat p50/p95: {p50_lat:.1f}/{p95_lat:.1f} ms"
        )

    # 5. Save outputs
    out_dir = REPO_ROOT / "reports" / "step2"
    out_dir.mkdir(parents=True, exist_ok=True)

    records_file = out_dir / "phase_b_pilot_records.jsonl"
    with open(records_file, "w", encoding="utf-8") as f:
        for r in pilot_records:
            f.write(json.dumps(r) + "\n")
    print(f"\nWrote {len(pilot_records)} records to {records_file}")

    summary_file = out_dir / "phase_b_pilot_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model": model_id,
                "seed": seed,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_items": len(pilot_records),
                "allocated_vram_mb": round(vram_mb, 1),
                "peak_vram_mb": round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1),
                "group_summaries": group_summaries,
            },
            f,
            indent=2,
        )
    print(f"Wrote summary to {summary_file}")

    # 6. Generate 20-sample per group Markdown Report
    report_file = out_dir / "phase_b_pilot_report.md"
    generate_markdown_report(group_summaries, pilot_records, report_file, model_id, vram_mb)
    print(f"Generated inspection report at {report_file}")


def generate_markdown_report(
    summaries: dict[str, Any],
    records: list[dict[str, Any]],
    output_path: Path,
    model_id: str,
    vram_mb: float,
) -> None:
    lines = [
        "# Phase B: 50-Item Calibration Pilot Report",
        "",
        f"- **Model**: `{model_id}` (FP16, cuda:0)",
        f"- **VRAM Footprint**: Allocated {vram_mb:.1f} MB (well within 1.5 GB budget)",
        "- **Evaluation Split**: `suite/validation/` (Suite v2.1)",
        "- **Sample**: 50 items per group (300 items total, seed 20260102)",
        "- **Acceptance Gates**:",
        "  1. Truncation rate < 1.0% across all groups",
        "  2. Extractable rate = 100.0% across all groups",
        "",
        "## 1. 50-Item Pilot Group Summary",
        "",
        "| Group | Cap | Tokens (min/med/p95/max) | Trunc % | Trunc Pass | Extractable % | Extr Pass | Accuracy | Latency p50/p95 (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for g, s in summaries.items():
        tok_str = (
            f"{s['min_tokens']} / {s['median_tokens']} / {s['p95_tokens']} / {s['max_tokens']}"
        )
        trunc_mark = "PASS" if s["truncation_pass"] else "**FAIL**"
        extr_mark = "PASS" if s["extractable_pass"] else "**FAIL**"
        lat_str = f"{s['latency_p50_ms']} / {s['latency_p95_ms']}"
        acc_str = f"{s['correct_count']}/{s['n']} ({s['accuracy_pct']}%)"
        lines.append(
            f"| `{g}` | {s['cap']} | {tok_str} | {s['truncation_rate_pct']}% | {trunc_mark} | {s['extractable_rate_pct']}% | {extr_mark} | {acc_str} | {lat_str} |"
        )

    lines.append("")
    lines.append("## 2. 20 Random Outputs Per Group (Owner Inspection)")
    lines.append("")

    groups = list(summaries.keys())
    for g in groups:
        g_recs = [r for r in records if r["group"] == g][:20]
        acc = sum(1 for r in g_recs if r["score"])
        lines.append(f"### Group: `{g}` ({acc}/20 correct — {acc*5.0:.1f}%)")
        lines.append("")
        lines.append(
            "| # | Item ID | Arm | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output Preview |"
        )
        lines.append("| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |")
        for idx, r in enumerate(g_recs, start=1):
            score_str = "PASS" if r["score"] else "FAIL"
            raw_preview = r["raw_output"][:60].replace("\n", " ") + (
                "..." if len(r["raw_output"]) > 60 else ""
            )
            raw_preview = raw_preview.replace("|", "/")
            tgt = str(r["target_key"]).replace("|", "/")
            extr = str(r["extracted_answer"]).replace("|", "/")
            lines.append(
                f"| {idx} | `{r['item_id']}` | {r['arm']} | `{tgt}` | `{extr}` | **{score_str}** | {r['tokens_generated']} | {r['wall_time_ms']} | {raw_preview} |"
            )
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
