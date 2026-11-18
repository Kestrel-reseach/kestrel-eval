"""CLI script to build, verify, hash, and route evaluation suite partitions (PR 4).

Generates:
- Validation partition (1,200 items in suite/validation/)
- Train partition (1,200 items in suite/train/)
- Locked-test partition (1,200 items strictly in KESTREL_PRIVATE_DIR outside repo)
Computes SHA-256 for all partition files and the root hash, updating manifest.yaml.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from evaluation.suite import build_suite_partitions, write_suite_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_suite")


def update_manifest_hashes(
    manifest_path: Path,
    locked_hashes: dict[str, str],
    root_hash: str,
) -> None:
    """Update locked_test_hashes and root_hash in manifest.yaml while preserving comments."""
    text = manifest_path.read_text(encoding="utf-8")

    # Format YAML block for hashes
    lines = ["locked_test_hashes:"]
    for grp in (
        "math",
        "science_mcq",
        "knowledge_mcq",
        "code",
        "knowledge_qa",
        "memory_probe",
    ):
        if grp in locked_hashes:
            lines.append(f'  {grp}: "{locked_hashes[grp]}"')
    lines.append(f'root_hash: "{root_hash}"')
    block = "\n".join(lines)

    # Replace existing locked_test_hashes: ... up to next section or hardware
    pattern = r"locked_test_hashes:.*?(?=\n# ── Hardware budget)"
    if re.search(pattern, text, flags=re.DOTALL):
        text = re.sub(pattern, block, text, flags=re.DOTALL)
    else:
        # Fallback replacement
        text = text.replace("locked_test_hashes: {}", block)

    manifest_path.write_text(text, encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "evaluation" / "manifest.yaml"
    abstracts_path = repo_root / "data" / "wikipedia_abstracts_5k.jsonl"

    logger.info("Building suite partitions...")
    partitions = build_suite_partitions(
        base_seed=20260101,
        abstracts_corpus_path=abstracts_path,
    )

    logger.info("Writing partition files and computing hashes...")
    result = write_suite_files(partitions, repo_root=repo_root)

    logger.info("Updating manifest.yaml with locked_test_hashes and root_hash...")
    update_manifest_hashes(
        manifest_path=manifest_path,
        locked_hashes=result["locked_test_hashes"],
        root_hash=result["root_hash"],
    )

    logger.info("Successfully built suite:")
    logger.info(" - Root hash: %s", result["root_hash"])
    logger.info(" - Private directory: %s", result["private_dir"])
    for grp, h in result["locked_test_hashes"].items():
        logger.info("   * %s: %s", grp, h)


if __name__ == "__main__":
    main()
