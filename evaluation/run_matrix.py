"""Run matrix: iterate over systems × splits × configs — Step 0 scaffold.

This module orchestrates evaluation runs and writes JSONL records. It is a
scaffold for Steps 2–10; the actual model calls are injected via the
``ModelRunner`` protocol.

Usage::

    from evaluation.run_matrix import RunConfig, RunMatrix

    config = RunConfig(
        run_id="run-20260101-001",
        git_commit="abc1234",
        seed=20260101,
        split="validation",
        system="P1",
        output_path=Path("runs/run-001.jsonl"),
    )
    # Inject a real model runner at Steps 2+.
    matrix = RunMatrix(config, runner=None)
    matrix.run(items)
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from evaluation.schema import validate_record

__all__ = [
    "ModelRunner",
    "RunConfig",
    "RunMatrix",
    "load_checkpoint",
]

Record = dict[str, Any]


# ── Protocol for model runners ─────────────────────────────────────────────────


class ModelRunner(Protocol):
    """Seam for model inference. Implement this for each system (F, B-LLM, P1)."""

    def run_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Run a single suite item and return a partial JSONL record.

        The returned dict must contain at least:
            tokens_generated, passes, verifier_score, retrieval_hits,
            bytes_read_from_ssd, energy_joules, wall_time_ms, peak_vram_mb, correct

        The harness fills: run_id, git_commit, config_hash, seed, split, group,
        item_id, system, git_dirty, energy_status.
        """
        ...


# ── Run configuration ─────────────────────────────────────────────────────────


@dataclass
class RunConfig:
    """Configuration for one evaluation run."""

    run_id: str
    git_commit: str
    seed: int
    split: str
    system: str
    output_path: Path

    git_dirty: bool = False
    """True if the repository had uncommitted changes at run time."""

    energy_status: str = "unmeasured"
    """One of: measured_calibrated, measured_uncalibrated, relative_only, unmeasured."""

    allow_locked_test: bool = False
    """Set to True only at Step 10 for the final locked-test run."""

    manifest_frozen: bool = False
    """Set to True only when the manifest has been frozen."""

    extra: dict[str, Any] = field(default_factory=dict)
    """Any extra fields saved alongside the config (not in JSONL records)."""

    @property
    def config_hash(self) -> str:
        """SHA-256 of this config (excluding output_path and extra)."""
        payload = {
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "run_id": self.run_id,
            "seed": self.seed,
            "split": self.split,
            "system": self.system,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def save(self, path: Path) -> None:
        """Save a config JSON alongside the JSONL file."""
        payload = {
            "config_hash": self.config_hash,
            "energy_status": self.energy_status,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "manifest_frozen": self.manifest_frozen,
            "output_path": str(self.output_path),
            "run_id": self.run_id,
            "seed": self.seed,
            "split": self.split,
            "system": self.system,
            **self.extra,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


# ── Checkpoint helpers ─────────────────────────────────────────────────────────


def load_checkpoint(path: Path) -> set[str]:
    """Return the set of item_ids already written to a checkpoint JSONL file."""
    done: set[str] = set()
    if not path.exists():
        return done
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                item_id = rec.get("item_id")
                if item_id:
                    done.add(item_id)
            except json.JSONDecodeError:
                continue
    return done


# ── Run matrix ────────────────────────────────────────────────────────────────


class RunMatrix:
    """Run one (system, split, config) combination over a list of items.

    Records are written to a JSONL file incrementally (checkpoint-safe).
    Already-written item_ids are skipped on resume.

    Args:
        config: The run configuration.
        runner: A ``ModelRunner`` implementation, or None for dry-run / testing.
    """

    def __init__(self, config: RunConfig, runner: ModelRunner | None) -> None:
        self.config = config
        self.runner = runner

    def run(self, items: list[dict[str, Any]]) -> list[Record]:
        """Run all items, skipping those already in the checkpoint file.

        Returns the list of newly written records (not including previously
        checkpointed items).
        """
        config = self.config
        output_path = config.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        done_ids = load_checkpoint(output_path)
        remaining = [item for item in items if item["item_id"] not in done_ids]

        new_records: list[Record] = []
        with output_path.open("a", encoding="utf-8") as fh:
            for item in remaining:
                record = self._run_one(item)
                errors = validate_record(
                    record,
                    allow_locked_test=config.allow_locked_test,
                    manifest_frozen=config.manifest_frozen,
                    expected_config_hash=config.config_hash,
                )
                if errors:
                    raise ValueError(f"Invalid record for {item['item_id']!r}: {errors}")
                line = json.dumps(record) + "\n"
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
                new_records.append(record)

        return new_records

    def _run_one(self, item: dict[str, Any]) -> Record:
        """Build a full JSONL record for one item."""
        config = self.config
        if self.runner is not None:
            partial = self.runner.run_item(item)
        else:
            # Dry-run stub: all fields are zero / null, correct is False.
            partial = {
                "bytes_read_from_ssd": 0,
                "correct": False,
                "energy_joules": 0.0,
                "energy_status": config.energy_status,
                "passes": 1,
                "peak_vram_mb": 0.0,
                "retrieval_hits": 0,
                "tokens_generated": 0,
                "verifier_score": None,
                "wall_time_ms": 0.0,
            }

        item_id = item["item_id"]
        group = item.get("group", item_id.split("-")[0] if "-" in item_id else item_id)
        energy_status = partial.pop("energy_status", config.energy_status)

        record: Record = {
            "config_hash": config.config_hash,
            "energy_status": energy_status,
            "git_commit": config.git_commit,
            "git_dirty": config.git_dirty,
            "group": group,
            "item_id": item_id,
            "run_id": config.run_id,
            "seed": config.seed,
            "split": config.split,
            "system": config.system,
            **partial,
        }
        return record
