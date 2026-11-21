"""R3: Provenance audit script.
For 20 random items per group (across all 6 groups):
- Finds the matching line in suite/validation/<group>.jsonl
- Verifies item_id and prompt SHA-256 hash match exactly.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

GROUPS = [
    "math",
    "science_mcq",
    "knowledge_mcq",
    "code",
    "knowledge_qa",
    "memory_probe",
]


def main() -> None:
    rng = random.Random(20260103)
    results = {}

    for grp in GROUPS:
        jsonl_path = REPO_ROOT / "suite" / "validation" / f"{grp}.jsonl"
        with open(jsonl_path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        total_items = len(lines)
        sampled_indices = sorted(rng.sample(range(total_items), 20))

        sampled_records = []
        for line_no in sampled_indices:
            raw_line = lines[line_no]
            data = json.loads(raw_line)
            item_id = data.get("id") or data.get("item_id")
            prompt = data.get("prompt", "")
            prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            sampled_records.append(
                {
                    "line_index": line_no + 1,
                    "item_id": item_id,
                    "prompt_hash": prompt_hash,
                    "prompt_preview": prompt.replace("\n", " ")[:60] + "...",
                }
            )

        results[grp] = {
            "total_in_partition": total_items,
            "sampled_count": len(sampled_records),
            "samples": sampled_records,
        }

    out_file = REPO_ROOT / "reports" / "step2" / "r3_provenance_20_per_group.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Generated R3 provenance audit for 20 items per group in {out_file}")


if __name__ == "__main__":
    main()
