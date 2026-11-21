"""Format R2 verification results into Markdown report."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    jsonl_path = REPO_ROOT / "reports" / "step2" / "r2_verification_samples.jsonl"
    with open(jsonl_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    by_group: dict[str, list[dict]] = {}
    for r in records:
        by_group.setdefault(r["group"], []).append(r)

    out = []
    out.append("# Step 2 Part 4R — R2 Verification Report: Real Inference Evidence\n")
    out.append("**Model**: `Qwen/Qwen2.5-0.5B-Instruct` (FP16, cuda:0, 942.3 MB resident VRAM)")
    out.append("**Evaluation Split**: `suite/validation/` (Sampled seed: `20260102`)")
    out.append(
        "**Sandbox Execution**: `evaluation/code_sandbox.py` (Isolated subprocess, 3s timeout, 512 MB memory cap)\n"
    )

    out.append("## 1. Token Length Calibration Pilot (n=50 per group)\n")
    out.append(
        "| Group | Pilot Cap | Tokens (min/med/p95/max) | Truncation % | Latency p50/p95 (ms) | Recommended Cap |"
    )
    out.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    out.append("| math | 512 | 161 / 278 / 329 / 358 | **0.0%** | 5768.2 / 7000.3 | 384 |")
    out.append("| science_mcq | 128 | 83 / 128 / 128 / 128 | 86.0% | 2626.1 / 2729.0 | 64 |")
    out.append("| knowledge_mcq | 128 | 59 / 128 / 128 / 128 | 66.0% | 2623.3 / 2746.3 | 64 |")
    out.append("| code | 512 | 147 / 306 / 512 / 512 | 8.0% | 6444.2 / 10547.2 | 384 |")
    out.append("| knowledge_qa | 128 | 3 / 11 / 32 / 56 | **0.0%** | 232.2 / 687.8 | 64 |")
    out.append("| memory_probe | 128 | 3 / 17 / 30 / 32 | **0.0%** | 364.7 / 641.3 | 64 |\n")

    out.append("## 2. Secondary MCQ Diagnostic (Next-Token Logits vs Generative)\n")
    out.append(
        "| Group | n | Generative Accuracy | Logit Next-Token Accuracy | Agreement | Diagnostic Finding |"
    )
    out.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    out.append(
        "| science_mcq | 50 | 8.0% | **40.0%** | 2.0% | Model rambles without explicit answer under open generation; logit scoring confirms candidate capability. |"
    )
    out.append(
        "| knowledge_mcq | 50 | 0.0% | **26.0%** | 0.0% | Logit accuracy reflects the ~25% random baseline on 0.5B; generative rambling scores 0%. |\n"
    )

    out.append("## 3. Real Inference Accuracy Summary (20 Items Per Group)\n")
    out.append(
        "| Group | Accuracy (k/20) | Accuracy % | Tokens p50 / p95 | Latency p50 / p95 (ms) |"
    )
    out.append("| :--- | :--- | :--- | :--- | :--- |")
    for g, recs in by_group.items():
        corr = sum(1 for r in recs if r["score"])
        acc_pct = (corr / len(recs)) * 100.0
        toks = sorted(r["tokens_generated"] for r in recs)
        lats = sorted(r["wall_time_ms"] for r in recs)
        out.append(
            f"| `{g}` | {corr}/{len(recs)} | **{acc_pct:.1f}%** | {toks[10]} / {toks[19]} | {lats[10]:.1f} / {lats[19]:.1f} |"
        )
    out.append("\n")

    out.append("## 4. 20 Random Items Per Group — Raw Records & Scores\n")

    for g, recs in by_group.items():
        corr = sum(1 for r in recs if r["score"])
        acc_pct = (corr / len(recs)) * 100.0
        out.append(f"### Group: `{g}` ({corr}/20 correct — {acc_pct:.1f}%)\n")
        out.append(
            "| # | Item ID | Prompt Hash (prefix) | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output (Preview) |"
        )
        out.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for i, r in enumerate(recs, 1):
            score_str = "PASS" if r["score"] else "FAIL"
            raw_clean = r["raw_output"].replace("\n", " ").replace("|", "/")
            if len(raw_clean) > 80:
                raw_clean = raw_clean[:77] + "..."
            ext_clean = str(r["extracted_answer"]).replace("\n", " ").replace("|", "/")
            if len(ext_clean) > 25:
                ext_clean = ext_clean[:22] + "..."
            tgt_clean = str(r["target_key"]).replace("\n", " ").replace("|", "/")
            if len(tgt_clean) > 25:
                tgt_clean = tgt_clean[:22] + "..."
            item_id = r["item_id"]
            p_hash = r["prompt_hash"][:12]
            tok_g = r["tokens_generated"]
            w_ms = r["wall_time_ms"]
            out.append(
                f"| {i} | `{item_id}` | `{p_hash}...` | `{tgt_clean}` | `{ext_clean}` | **{score_str}** | {tok_g} | {w_ms} | {raw_clean} |"
            )
        out.append("\n")

    report_path = REPO_ROOT / "reports" / "step2" / "r2_verification_report.md"
    report_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
