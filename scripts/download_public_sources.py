"""Download official public benchmark datasets for Project Kestrel Suite v2.0.

Datasets:
1. GSM8K (Grade School Math 8K) - MIT License
2. ARC-Challenge (AI2) - CC BY-SA 4.0
3. MMLU (Hendrycks et al.) - MIT License
4. HumanEval (OpenAI) - MIT License
5. MBPP (Google Research) - CC BY 4.0

Downloads directly to data/raw/ (gitignored) and computes authoritative SHA-256 digests.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest_path: Path) -> tuple[int, str]:
    print(f"Downloading {url} -> {dest_path.name}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as out:
        shutil.copyfileobj(resp, out)
    size = dest_path.stat().st_size
    digest = sha256_file(dest_path)
    print(f"  Done: {size:,} bytes | SHA256: {digest}")
    return size, digest


def main() -> None:
    manifest_records = {}

    # 1. GSM8K
    print("\n=== 1. GSM8K ===")
    gsm8k_train_path = RAW_DIR / "gsm8k_train.jsonl"
    gsm8k_test_path = RAW_DIR / "gsm8k_test.jsonl"
    if not gsm8k_train_path.exists():
        download_file(
            "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/train.jsonl",
            gsm8k_train_path,
        )
    if not gsm8k_test_path.exists():
        download_file(
            "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl",
            gsm8k_test_path,
        )

    with open(gsm8k_train_path, encoding="utf-8") as f:
        gsm8k_train_count = sum(1 for line in f if line.strip())
    with open(gsm8k_test_path, encoding="utf-8") as f:
        gsm8k_test_count = sum(1 for line in f if line.strip())

    manifest_records["gsm8k"] = {
        "name": "GSM8K (Grade School Math 8K)",
        "url": "https://github.com/openai/grade-school-math",
        "license": "MIT",
        "license_url": "https://github.com/openai/grade-school-math/blob/master/LICENSE",
        "version": "1.0",
        "files": {
            "train": {
                "path": str(gsm8k_train_path.relative_to(REPO_ROOT)),
                "size_bytes": gsm8k_train_path.stat().st_size,
                "sha256": sha256_file(gsm8k_train_path),
                "count": gsm8k_train_count,
            },
            "test": {
                "path": str(gsm8k_test_path.relative_to(REPO_ROOT)),
                "size_bytes": gsm8k_test_path.stat().st_size,
                "sha256": sha256_file(gsm8k_test_path),
                "count": gsm8k_test_count,
            },
        },
        "total_count": gsm8k_train_count + gsm8k_test_count,
    }

    # 2. ARC-Challenge
    print("\n=== 2. ARC-Challenge ===")
    arc_zip_path = RAW_DIR / "ARC-V1-Feb2018.zip"
    if not arc_zip_path.exists():
        download_file(
            "https://ai2-public-datasets.s3.amazonaws.com/arc/ARC-V1-Feb2018.zip",
            arc_zip_path,
        )

    arc_extracted_dir = RAW_DIR / "ARC-V1-Feb2018-2"
    if not arc_extracted_dir.exists():
        arc_extracted_dir = RAW_DIR / "ARC-V1-Feb2018"
    if not arc_extracted_dir.exists():
        with zipfile.ZipFile(arc_zip_path, "r") as z:
            z.extractall(RAW_DIR)
        if (RAW_DIR / "ARC-V1-Feb2018-2").exists():
            arc_extracted_dir = RAW_DIR / "ARC-V1-Feb2018-2"
        else:
            arc_extracted_dir = RAW_DIR / "ARC-V1-Feb2018"

    arc_challenge_dir = arc_extracted_dir / "ARC-Challenge"
    arc_splits = {}
    total_arc = 0
    for split_name in ("Train", "Dev", "Test"):
        fpath = arc_challenge_dir / f"ARC-Challenge-{split_name}.jsonl"
        with open(fpath, encoding="utf-8") as f:
            cnt = sum(1 for line in f if line.strip())
        arc_splits[split_name.lower()] = {
            "path": str(fpath.relative_to(REPO_ROOT)),
            "size_bytes": fpath.stat().st_size,
            "sha256": sha256_file(fpath),
            "count": cnt,
        }
        total_arc += cnt

    manifest_records["arc_challenge"] = {
        "name": "AI2 Reasoning Challenge (ARC-Challenge)",
        "url": "https://allenai.org/data/arc",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "version": "1.0 (Feb 2018)",
        "archive_sha256": sha256_file(arc_zip_path),
        "files": arc_splits,
        "total_count": total_arc,
    }

    # 3. MMLU
    print("\n=== 3. MMLU ===")
    mmlu_tar_path = RAW_DIR / "data.tar"
    if not mmlu_tar_path.exists():
        download_file(
            "https://people.eecs.berkeley.edu/~hendrycks/data.tar",
            mmlu_tar_path,
        )

    mmlu_extracted_dir = RAW_DIR / "mmlu_data"
    if not mmlu_extracted_dir.exists():
        with tarfile.open(mmlu_tar_path, "r") as t:
            t.extractall(RAW_DIR)
        (RAW_DIR / "data").rename(mmlu_extracted_dir)

    target_subjects = [
        "college_computer_science",
        "college_physics",
        "college_biology",
        "college_chemistry",
        "elementary_mathematics",
        "high_school_world_history",
        "high_school_geography",
        "professional_law",
        "clinical_knowledge",
        "econometrics",
    ]

    subject_counts = {}
    total_mmlu_selected = 0
    for subj in target_subjects:
        counts_by_split = {}
        for sp in ("dev", "val", "test"):
            csv_path = mmlu_extracted_dir / sp / f"{subj}_{sp}.csv"
            if csv_path.exists():
                with open(csv_path, encoding="utf-8") as f:
                    cnt = sum(1 for _ in csv.reader(f))
                counts_by_split[sp] = cnt
            else:
                counts_by_split[sp] = 0
        tot_subj = sum(counts_by_split.values())
        subject_counts[subj] = {
            "splits": counts_by_split,
            "total": tot_subj,
        }
        total_mmlu_selected += tot_subj

    manifest_records["mmlu"] = {
        "name": "MMLU (Measuring Massive Multitask Language Understanding)",
        "url": "https://github.com/hendrycks/test",
        "license": "MIT",
        "license_url": "https://github.com/hendrycks/test/blob/master/LICENSE",
        "version": "1.0",
        "archive_sha256": sha256_file(mmlu_tar_path),
        "selected_subjects": target_subjects,
        "subject_breakdown": subject_counts,
        "total_selected_count": total_mmlu_selected,
    }

    # 4. HumanEval
    print("\n=== 4. HumanEval ===")
    he_gz_path = RAW_DIR / "HumanEval.jsonl.gz"
    if not he_gz_path.exists():
        download_file(
            "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
            he_gz_path,
        )

    he_jsonl_path = RAW_DIR / "HumanEval.jsonl"
    if not he_jsonl_path.exists():
        with gzip.open(he_gz_path, "rb") as gz, open(he_jsonl_path, "wb") as out:
            shutil.copyfileobj(gz, out)

    with open(he_jsonl_path, encoding="utf-8") as f:
        he_count = sum(1 for line in f if line.strip())

    manifest_records["humaneval"] = {
        "name": "HumanEval",
        "url": "https://github.com/openai/human-eval",
        "license": "MIT",
        "license_url": "https://github.com/openai/human-eval/blob/master/LICENSE",
        "version": "1.0",
        "file": {
            "path": str(he_jsonl_path.relative_to(REPO_ROOT)),
            "size_bytes": he_jsonl_path.stat().st_size,
            "sha256": sha256_file(he_jsonl_path),
            "count": he_count,
        },
        "total_count": he_count,
    }

    # 5. MBPP
    print("\n=== 5. MBPP ===")
    mbpp_path = RAW_DIR / "mbpp.jsonl"
    if not mbpp_path.exists():
        download_file(
            "https://raw.githubusercontent.com/google-research/google-research/master/mbpp/mbpp.jsonl",
            mbpp_path,
        )

    with open(mbpp_path, encoding="utf-8") as f:
        mbpp_count = sum(1 for line in f if line.strip())

    manifest_records["mbpp"] = {
        "name": "MBPP (Mostly Basic Python Problems)",
        "url": "https://github.com/google-research/google-research/tree/master/mbpp",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "version": "1.0",
        "file": {
            "path": str(mbpp_path.relative_to(REPO_ROOT)),
            "size_bytes": mbpp_path.stat().st_size,
            "sha256": sha256_file(mbpp_path),
            "count": mbpp_count,
        },
        "total_count": mbpp_count,
    }

    # Save summary manifest
    out_manifest = REPO_ROOT / "reports" / "step2" / "public_sources_manifest.json"
    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest_records, f, indent=2)

    print("\n" + "=" * 80)
    print("PUBLIC BENCHMARK DOWNLOAD AUDIT COMPLETE")
    print("=" * 80)
    print(
        f"GSM8K: {manifest_records['gsm8k']['total_count']} items (Train={gsm8k_train_count}, Test={gsm8k_test_count})"
    )
    print(
        f"ARC-Challenge: {manifest_records['arc_challenge']['total_count']} items (Train={arc_splits['train']['count']}, Dev={arc_splits['dev']['count']}, Test={arc_splits['test']['count']})"
    )
    print(f"MMLU (10 subjects): {total_mmlu_selected} items across 10 subjects")
    for s, d in subject_counts.items():
        print(
            f"  - {s}: {d['total']} (dev={d['splits']['dev']}, val={d['splits']['val']}, test={d['splits']['test']})"
        )
    print(f"HumanEval: {he_count} items")
    print(f"MBPP: {mbpp_count} items")
    print(f"Saved manifest to {out_manifest}")


if __name__ == "__main__":
    main()
