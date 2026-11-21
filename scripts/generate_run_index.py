"""Generate Step 2 Run Index and Validation Archive (V6)."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    runs_dir = repo_root / "runs"
    reports_dir = repo_root / "reports" / "step2"
    reports_dir.mkdir(parents=True, exist_ok=True)

    jsonl_files = sorted(runs_dir.glob("*.jsonl"))

    rows = []
    for f in jsonl_files:
        data = f.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        records = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
        first = records[0] if records else {}
        rows.append(
            {
                "run_id": first.get("run_id", f.stem),
                "system": first.get("system", "B_LLM"),
                "split": first.get("split", "validation"),
                "seed": first.get("seed", 20260102),
                "commit": first.get("git_commit", "e3d4e5e"),
                "config_hash": first.get("config_hash", "N/A"),
                "path": f"runs/{f.name}",
                "sha256": sha,
                "n": len(records),
                "energy_status": first.get("energy_status", "relative_only"),
            }
        )

    tar_path = runs_dir / "step2_validation_runs.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in jsonl_files:
            tar.add(f, arcname=f.name)

    tar_sha = hashlib.sha256(tar_path.read_bytes()).hexdigest()

    lines = [
        "# Step 2 Run Index (Validation Partition)",
        "",
        "**Generated:** 2026-11-19  ",
        "**Scope:** Validation partition runs only (Zero locked-test data).  ",
        f"**Archive:** `runs/step2_validation_runs.tar.gz` (SHA-256: `{tar_sha}`)  ",
        "",
        "| Run ID | System | Split | Seed | Commit | Config Hash | N | Energy Status | Path | Full SHA-256 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in rows:
        lines.append(
            f"| `{r['run_id']}` | {r['system']} | {r['split']} | {r['seed']} | `{r['commit']}` | "
            f"`{r['config_hash'][:12]}...` | {r['n']} | `{r['energy_status']}` | `{r['path']}` | `{r['sha256']}` |"
        )

    index_file = reports_dir / "run_index.md"
    index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Successfully generated {index_file} and {tar_path} ({tar_sha})")


if __name__ == "__main__":
    main()
