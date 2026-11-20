"""Re-run code group validation items with fixed prompts (Step 2 Part 3b).

Protocol:
- Re-runs ONLY the 100 validation code items for Qwen2.5-0.5B and Qwen2.5-1.5B (NF4).
- Uses updated prompts: MBPP with function name and first test assertion; Synthetic with 'Define a top-level function named X, no class'.
- max_new_tokens = 512, do_sample = False (greedy deterministic).
- Executes unit tests in the standard sandbox.
- Updates the code records in run_qwen2.5-0.5b-instruct-q4_validation.jsonl and run_qwen2.5-1.5b-instruct-q4_validation.jsonl.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from evaluation.extractors import extract_answer_for_group
from evaluation.prompts import format_prompt_for_model

REPO_ROOT = Path(__file__).resolve().parent.parent

CANDIDATES = [
    {
        "id": "qwen2.5-0.5b-instruct-q4",
        "model_id": "Qwen/Qwen2.5-0.5B-Instruct",
        "jsonl": REPO_ROOT / "reports/step2/run_qwen2.5-0.5b-instruct-q4_validation.jsonl",
    },
    {
        "id": "qwen2.5-1.5b-instruct-q4",
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "jsonl": REPO_ROOT / "reports/step2/run_qwen2.5-1.5b-instruct-q4_validation.jsonl",
    },
]

BNB_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)


def rerun_candidate_code(cand: dict[str, Any]):
    model_name = cand["model_id"]
    jsonl_path = cand["jsonl"]

    print("\n" + "=" * 80)
    print(f"RE-RUNNING CODE GROUP FOR: {cand['id']} ({model_name})")
    print("=" * 80)

    # 1. Load 100 code validation items
    code_path = REPO_ROOT / "suite/validation/code.jsonl"
    with open(code_path) as f:
        code_items = [json.loads(line) for line in f]
    assert len(code_items) == 100, f"Expected 100 code items, got {len(code_items)}"

    # 2. Load tokenizer and model
    print(f"Loading tokenizer: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)

    print(f"Loading NF4 model onto cuda:0...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=BNB_CONFIG,
        device_map="cuda:0",
        local_files_only=True,
    )

    # Warmup
    _ = model.generate(torch.tensor([[100, 200]], device=model.device), max_new_tokens=2)
    torch.cuda.synchronize()

    new_code_records = {}
    correct_count = 0
    mbpp_correct = 0
    synthetic_correct = 0
    truncation_count = 0

    t_start = time.perf_counter()
    for idx, item in enumerate(code_items, 1):
        prompt_str, prompt_hash, _ = format_prompt_for_model(
            item, tokenizer=tokenizer, use_retrieval=False
        )
        inputs = tokenizer(prompt_str, return_tensors="pt").to(model.device)
        in_len = inputs.input_ids.shape[1]

        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        torch.cuda.synchronize()
        t1 = time.perf_counter()

        wall_ms = (t1 - t0) * 1000.0
        gen_len = len(out[0]) - in_len
        raw_output = tokenizer.decode(out[0][in_len:], skip_special_tokens=True).strip()
        is_trunc = gen_len >= 512
        if is_trunc:
            truncation_count += 1

        ext_answer, is_correct = extract_answer_for_group(item, raw_output)
        if is_correct:
            correct_count += 1
            if item.get("arm") == "public":
                mbpp_correct += 1
            else:
                synthetic_correct += 1

        rec = {
            "run_id": f"run-c2-{cand['id']}-validation",
            "item_id": item["id"],
            "group": "code",
            "arm": item.get("arm", "public"),
            "prompt_hash": prompt_hash,
            "raw_output": raw_output,
            "extracted_answer": ext_answer,
            "target": item.get("target", ""),
            "correct": is_correct,
            "tokens_generated": gen_len,
            "wall_time_ms": round(wall_ms, 2),
            "truncated": is_trunc,
            "metadata": item.get("metadata", {}),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        new_code_records[item["id"]] = rec

        if idx % 20 == 0 or idx == len(code_items):
            print(f"  Processed {idx:3d}/100 items | Current Code Accuracy: {correct_count}/{idx} ({correct_count/idx:.1%})")

    total_time = time.perf_counter() - t_start
    print(f"\nFinished in {total_time:.1f}s.")
    print(f"Code Total Accuracy: {correct_count}/100 ({correct_count:.1%})")
    print(f"  MBPP (public)     : {mbpp_correct}/50 ({mbpp_correct/50:.1%})")
    print(f"  Synthetic         : {synthetic_correct}/50 ({synthetic_correct/50:.1%})")
    print(f"Truncation count    : {truncation_count}/100 ({truncation_count/100:.1%})")

    # Clean up GPU
    del model
    del tokenizer
    torch.cuda.empty_cache()

    # 3. Update the JSONL file
    print(f"Updating {jsonl_path}...")
    with open(jsonl_path) as f:
        existing_records = [json.loads(line) for line in f]

    updated_records = []
    old_code_correct = 0
    for r in existing_records:
        if r.get("group") == "code":
            if r.get("correct"):
                old_code_correct += 1
            iid = r["item_id"]
            if iid in new_code_records:
                updated_records.append(new_code_records[iid])
            else:
                updated_records.append(r)
        else:
            updated_records.append(r)

    assert len(updated_records) == len(existing_records) == 1250

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in updated_records:
            f.write(json.dumps(r) + "\n")

    print(f"Updated {jsonl_path}: code correct changed from {old_code_correct} to {correct_count} (+{correct_count - old_code_correct})")
    return {
        "candidate": cand["id"],
        "old_correct": old_code_correct,
        "new_correct": correct_count,
        "mbpp_correct": mbpp_correct,
        "synthetic_correct": synthetic_correct,
        "truncation_count": truncation_count,
    }


def main():
    results = []
    for cand in CANDIDATES:
        res = rerun_candidate_code(cand)
        results.append(res)

    print("\n" + "=" * 80)
    print("CODE RE-RUN SUMMARY TABLE")
    print("=" * 80)
    for r in results:
        print(f"Candidate {r['candidate']}:")
        print(f"  Before: {r['old_correct']}/100 ({r['old_correct']}%)")
        print(f"  After : {r['new_correct']}/100 ({r['new_correct']}%) [MBPP: {r['mbpp_correct']}/50 ({r['mbpp_correct']*2}%), Synth: {r['synthetic_correct']}/50 ({r['synthetic_correct']*2}%)]")
        print(f"  Truncation: {r['truncation_count']}/100 ({r['truncation_count']}%)")


if __name__ == "__main__":
    main()

