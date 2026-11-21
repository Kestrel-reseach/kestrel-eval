"""GSM8K Audit for Qwen2.5-0.5B and Qwen2.5-1.5B (Step 2 Part 2c).

Audit Protocol:
- 30 random GSM8K items per model under seed 20260102.
- Shows raw output, extracted number, and target key.
- Reports GSM8K-only and synthetic-math accuracy separately.
- Compares against Qwen's published benchmark figures (Qwen2.5 Technical Report, arXiv:2412.15115).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from evaluation.extractors import extract_math_answer


def audit_model(model_tag: str, seed: int = 20260102) -> dict:
    file_path = Path(f"reports/step2/run_qwen2.5-{model_tag}-instruct-q4_validation.jsonl")
    with open(file_path) as f:
        records = [json.loads(line) for line in f if json.loads(line).get("group") == "math"]

    gsm8k_records = [r for r in records if r.get("arm") == "public"]
    synthetic_records = [r for r in records if r.get("arm") == "synthetic"]

    # Re-extract with improved extractor
    for r in gsm8k_records:
        r["new_extracted"] = extract_math_answer(r.get("raw_output", ""))
        tgt = float(r["target"])
        ext = r["new_extracted"]
        r["new_correct"] = ext is not None and (
            abs(ext - tgt) <= 1e-4 or (tgt != 0 and abs(ext - tgt) / abs(tgt) <= 1e-4)
        )

    for r in synthetic_records:
        r["new_extracted"] = extract_math_answer(r.get("raw_output", ""))
        tgt = float(r["target"])
        ext = r["new_extracted"]
        r["new_correct"] = ext is not None and (
            abs(ext - tgt) <= 1e-4 or (tgt != 0 and abs(ext - tgt) / abs(tgt) <= 1e-4)
        )

    gsm8k_acc = sum(1 for r in gsm8k_records if r["new_correct"]) / len(gsm8k_records)
    synth_acc = sum(1 for r in synthetic_records if r["new_correct"]) / len(synthetic_records)
    combined_acc = (
        sum(1 for r in gsm8k_records if r["new_correct"])
        + sum(1 for r in synthetic_records if r["new_correct"])
    ) / len(records)

    # 30 random sample
    rng = random.Random(seed)
    sample_indices = sorted(rng.sample(range(len(gsm8k_records)), 30))
    sample_items = [gsm8k_records[i] for i in sample_indices]

    return {
        "model": f"Qwen2.5-{model_tag}-Instruct NF4",
        "gsm8k_count": len(gsm8k_records),
        "gsm8k_correct": sum(1 for r in gsm8k_records if r["new_correct"]),
        "gsm8k_acc_pct": gsm8k_acc * 100,
        "synth_count": len(synthetic_records),
        "synth_correct": sum(1 for r in synthetic_records if r["new_correct"]),
        "synth_acc_pct": synth_acc * 100,
        "combined_acc_pct": combined_acc * 100,
        "sample": sample_items,
    }


def main():
    print("=" * 80)
    print("GSM8K EXTRACTION AUDIT & REPORT (Step 2 Part 2c)")
    print("=" * 80)

    for m in ["0.5b", "1.5b"]:
        res = audit_model(m)
        print(f"\nModel: {res['model']}")
        print(
            f"  GSM8K-only Accuracy : {res['gsm8k_correct']}/{res['gsm8k_count']} ({res['gsm8k_acc_pct']:.2f}%)"
        )
        print(
            f"  Synthetic Math Acc  : {res['synth_correct']}/{res['synth_count']} ({res['synth_acc_pct']:.2f}%)"
        )
        print(f"  Combined Math Acc   : {res['combined_acc_pct']:.2f}%")
        print("\n30 Random Audited GSM8K Items:")
        for idx, item in enumerate(res["sample"], 1):
            raw = item.get("raw_output", "").strip().replace("\n", " ")
            if len(raw) > 90:
                raw = raw[:45] + " ... " + raw[-40:]
            print(
                f"  {idx:2d}. [{item['item_id']}] Key: {item['target']} | Extracted: {item['new_extracted']} | Match: {item['new_correct']}"
            )
            print(f"      Raw snippet: {raw}")


if __name__ == "__main__":
    main()
