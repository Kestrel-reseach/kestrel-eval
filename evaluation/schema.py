"""JSONL run record schema and validator for Kestrel Prototype 1.

Every evaluation run writes one record per item to a ``.jsonl`` file. This
module defines the required fields and validates that records conform to the
schema defined in ``evaluation/manifest.yaml`` and ``PLAN.md``.

Required fields:
    run_id, git_commit, config_hash, seed, split, group, item_id, system,
    git_dirty, energy_status, tokens_generated, passes, verifier_score,
    retrieval_hits, bytes_read_from_ssd, energy_joules, wall_time_ms,
    peak_vram_mb, correct

Usage::

    from evaluation.schema import REQUIRED_FIELDS, validate_record
    errors = validate_record(record)
    if errors:
        raise ValueError(errors)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

__all__ = [
    "ENERGY_STATUSES",
    "REQUIRED_FIELDS",
    "SPLITS",
    "SYSTEMS",
    "SchemaError",
    "validate_jsonl_file",
    "validate_record",
]

# ── Constants ──────────────────────────────────────────────────────────────────

#: Every run record must contain at least these fields.
REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "git_commit",
    "config_hash",
    "seed",
    "split",
    "group",
    "item_id",
    "system",
    "git_dirty",
    "energy_status",
    "tokens_generated",
    "passes",
    "verifier_score",
    "retrieval_hits",
    "bytes_read_from_ssd",
    "energy_joules",
    "wall_time_ms",
    "peak_vram_mb",
    "correct",
)

#: Valid partition names. Never use "locked_test" in development runs.
SPLITS: frozenset[str] = frozenset({"train", "validation", "locked_test"})

#: Known system identifiers.
SYSTEMS: frozenset[str] = frozenset({"F", "B_LLM", "P1"})

#: Valid energy status values.
ENERGY_STATUSES: frozenset[str] = frozenset(
    {
        "measured_calibrated",
        "measured_uncalibrated",
        "relative_only",
        "unmeasured",
    }
)

# ── Types ──────────────────────────────────────────────────────────────────────

#: A run record is an arbitrary dict loaded from one JSONL line.
Record = dict[str, Any]


class SchemaError(ValueError):
    """Raised when a run record violates the schema."""


# ── Validation ─────────────────────────────────────────────────────────────────


def validate_record(
    record: Record,
    *,
    allow_locked_test: bool = False,
    manifest_frozen: bool = False,
    expected_config_hash: str | None = None,
) -> list[str]:
    """Return a list of validation errors for *record*.

    Returns an empty list when the record is valid.

    Args:
        record: A dict loaded from one JSONL line.
        allow_locked_test: Set to ``True`` only at Step 10 when running the
            locked-test partition once with the frozen config. Normally
            ``False`` to prevent accidental use of the locked partition.
        manifest_frozen: Whether the manifest is marked frozen (``frozen: true``).
            Required when evaluating the locked-test partition.
        expected_config_hash: The expected SHA-256 hash of the frozen config.
            Required when evaluating the locked-test partition.
    """
    errors: list[str] = []

    # ── Required fields present ────────────────────────────────────────────────
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"missing required field: {field!r}")

    if errors:
        # Type checks below depend on the fields being present.
        return errors

    # ── Type constraints ───────────────────────────────────────────────────────
    if not isinstance(record["run_id"], str) or not record["run_id"]:
        errors.append("run_id must be a non-empty string")

    if not isinstance(record["git_commit"], str) or len(record["git_commit"]) < 7:
        errors.append("git_commit must be a hex string of at least 7 characters")

    if not isinstance(record["config_hash"], str) or not record["config_hash"]:
        errors.append("config_hash must be a non-empty string")

    if not isinstance(record["seed"], int):
        errors.append("seed must be an integer")

    if record["split"] not in SPLITS:
        errors.append(f"split must be one of {sorted(SPLITS)!r}, got {record['split']!r}")

    # ── Locked test partition guard ────────────────────────────────────────────
    if record["split"] == "locked_test":
        if not allow_locked_test:
            errors.append(
                "split 'locked_test' is locked; set allow_locked_test=True only at Step 10"
            )
        if os.environ.get("KESTREL_LOCKED_RUN") != "1":
            errors.append("split 'locked_test' requires KESTREL_LOCKED_RUN=1 environment variable")
        if not manifest_frozen:
            errors.append("split 'locked_test' requires manifest frozen=true")
        if expected_config_hash is None or record["config_hash"] != expected_config_hash:
            errors.append(
                f"split 'locked_test' requires matching config_hash "
                f"(expected {expected_config_hash!r}, got {record.get('config_hash')!r})"
            )

    if not isinstance(record["group"], str) or not record["group"]:
        errors.append("group must be a non-empty string")

    if not isinstance(record["item_id"], str) or not record["item_id"]:
        errors.append("item_id must be a non-empty string")

    if record["system"] not in SYSTEMS:
        errors.append(f"system must be one of {sorted(SYSTEMS)!r}, got {record['system']!r}")

    if not isinstance(record["git_dirty"], bool):
        errors.append("git_dirty must be a boolean")

    if record["energy_status"] not in ENERGY_STATUSES:
        errors.append(
            f"energy_status must be one of {sorted(ENERGY_STATUSES)!r}, "
            f"got {record['energy_status']!r}"
        )

    _check_non_negative_int(errors, record, "tokens_generated")
    _check_positive_int(errors, record, "passes")
    _check_float_in_range(errors, record, "verifier_score", 0.0, 1.0, nullable=True)
    _check_non_negative_int(errors, record, "retrieval_hits")
    _check_non_negative_int(errors, record, "bytes_read_from_ssd")
    _check_non_negative_float(errors, record, "energy_joules")
    _check_non_negative_float(errors, record, "wall_time_ms")
    _check_non_negative_float(errors, record, "peak_vram_mb")

    if not isinstance(record["correct"], bool):
        errors.append("correct must be a boolean")

    return errors


def validate_jsonl_file(
    path: Path | str,
    *,
    allow_locked_test: bool = False,
    manifest_frozen: bool = False,
    expected_config_hash: str | None = None,
) -> list[str]:
    """Validate every record in a ``.jsonl`` file.

    Returns a list of error strings (empty when the file is valid). Each
    error is prefixed with its line number for easy location.

    Args:
        path: Path to the JSONL file.
        allow_locked_test: Passed through to :func:`validate_record`.
        manifest_frozen: Passed through to :func:`validate_record`.
        expected_config_hash: Passed through to :func:`validate_record`.
    """
    errors: list[str] = []
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        for line_number, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON — {exc}")
                continue
            line_errors = validate_record(
                record,
                allow_locked_test=allow_locked_test,
                manifest_frozen=manifest_frozen,
                expected_config_hash=expected_config_hash,
            )
            for error in line_errors:
                errors.append(f"line {line_number}: {error}")
    return errors


# ── Helpers ────────────────────────────────────────────────────────────────────


def _check_non_negative_int(errors: list[str], record: Record, field: str) -> None:
    value = record.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{field} must be a non-negative integer, got {value!r}")


def _check_positive_int(errors: list[str], record: Record, field: str) -> None:
    value = record.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        errors.append(f"{field} must be a positive integer (>= 1), got {value!r}")


def _check_non_negative_float(errors: list[str], record: Record, field: str) -> None:
    value = record.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        errors.append(f"{field} must be a non-negative number, got {value!r}")


def _check_float_in_range(
    errors: list[str],
    record: Record,
    field: str,
    lo: float,
    hi: float,
    *,
    nullable: bool = False,
) -> None:
    value = record.get(field)
    if nullable and value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{field} must be a number in [{lo}, {hi}] or null, got {value!r}")
        return
    if not (lo <= value <= hi):
        errors.append(f"{field} must be in [{lo}, {hi}], got {value!r}")
