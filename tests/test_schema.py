"""Tests for the JSONL run record schema (Step 0).

Covers:
- All required fields present/missing (including group, git_dirty, energy_status)
- Type constraints for each field
- Split guard & locked_test multi-factor guard:
  - allow_locked_test=True
  - KESTREL_LOCKED_RUN=1
  - manifest_frozen=True
  - matching config_hash
- File-level validation of a multi-line JSONL
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from evaluation.schema import (
    ENERGY_STATUSES,
    REQUIRED_FIELDS,
    SchemaError,  # noqa: F401
    validate_jsonl_file,
    validate_record,
)

# ── Fixtures ───────────────────────────────────────────────────────────────────


def _valid_record(**overrides: object) -> dict:
    """Return a minimal valid run record, with optional field overrides."""
    base = {
        "run_id": "run-20260101-001",
        "git_commit": "abc1234",
        "config_hash": "deadbeef12345678",
        "seed": 20260101,
        "split": "validation",
        "group": "math",
        "item_id": "math-001",
        "system": "P1",
        "git_dirty": False,
        "energy_status": "unmeasured",
        "tokens_generated": 42,
        "passes": 1,
        "verifier_score": 0.85,
        "retrieval_hits": 0,
        "bytes_read_from_ssd": 0,
        "energy_joules": 1.23,
        "wall_time_ms": 450.0,
        "peak_vram_mb": 512.0,
        "correct": True,
        "inference_mode": "real",
        "simulated": False,
    }
    base.update(overrides)
    return base


# ── Required-fields tests ──────────────────────────────────────────────────────


def test_valid_record_has_no_errors() -> None:
    errors = validate_record(_valid_record())
    assert errors == []


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_missing_required_field_raises_error(field: str) -> None:
    record = _valid_record()
    del record[field]
    errors = validate_record(record)
    assert any(field in e for e in errors), f"expected error mentioning {field!r}"


# ── Type-constraint tests ──────────────────────────────────────────────────────


def test_run_id_must_be_non_empty_string() -> None:
    assert validate_record(_valid_record(run_id="")) != []
    assert validate_record(_valid_record(run_id=123)) != []
    assert validate_record(_valid_record(run_id="ok")) == []


def test_git_commit_must_be_at_least_7_chars() -> None:
    assert validate_record(_valid_record(git_commit="abc123")) != []
    assert validate_record(_valid_record(git_commit="abc1234")) == []


def test_seed_must_be_integer() -> None:
    assert validate_record(_valid_record(seed=1.5)) != []
    assert validate_record(_valid_record(seed=42)) == []


def test_split_must_be_valid() -> None:
    assert validate_record(_valid_record(split="unknown")) != []
    assert validate_record(_valid_record(split="train")) == []
    assert validate_record(_valid_record(split="validation")) == []


def test_group_must_be_non_empty_string() -> None:
    assert validate_record(_valid_record(group="")) != []
    assert validate_record(_valid_record(group=123)) != []
    assert validate_record(_valid_record(group="math")) == []
    assert validate_record(_valid_record(group="code")) == []


def test_git_dirty_must_be_boolean() -> None:
    assert validate_record(_valid_record(git_dirty="false")) != []
    assert validate_record(_valid_record(git_dirty=0)) != []
    assert validate_record(_valid_record(git_dirty=False)) == []
    assert validate_record(_valid_record(git_dirty=True)) == []


@pytest.mark.parametrize("status", sorted(ENERGY_STATUSES))
def test_energy_status_valid_values(status: str) -> None:
    assert validate_record(_valid_record(energy_status=status)) == []


def test_energy_status_invalid_value() -> None:
    assert validate_record(_valid_record(energy_status="invalid_status")) != []
    assert validate_record(_valid_record(energy_status=123)) != []


def test_tokens_generated_must_be_non_negative_int() -> None:
    assert validate_record(_valid_record(tokens_generated=-1)) != []
    assert validate_record(_valid_record(tokens_generated=1.5)) != []
    assert validate_record(_valid_record(tokens_generated=0)) == []


def test_passes_must_be_positive_int() -> None:
    assert validate_record(_valid_record(passes=0)) != []
    assert validate_record(_valid_record(passes=-1)) != []
    assert validate_record(_valid_record(passes=1)) == []


def test_verifier_score_must_be_in_0_to_1_or_null() -> None:
    assert validate_record(_valid_record(verifier_score=-0.1)) != []
    assert validate_record(_valid_record(verifier_score=1.1)) != []
    assert validate_record(_valid_record(verifier_score=None)) == []
    assert validate_record(_valid_record(verifier_score=0.0)) == []
    assert validate_record(_valid_record(verifier_score=1.0)) == []


def test_energy_joules_must_be_non_negative() -> None:
    assert validate_record(_valid_record(energy_joules=-0.001)) != []
    assert validate_record(_valid_record(energy_joules=0.0)) == []


def test_correct_must_be_boolean() -> None:
    assert validate_record(_valid_record(correct=1)) != []
    assert validate_record(_valid_record(correct="yes")) != []
    assert validate_record(_valid_record(correct=True)) == []
    assert validate_record(_valid_record(correct=False)) == []


def test_system_must_be_known() -> None:
    assert validate_record(_valid_record(system="Unknown")) != []
    assert validate_record(_valid_record(system="F")) == []
    assert validate_record(_valid_record(system="B_LLM")) == []


# ── Locked test partition multi-factor guard ──────────────────────────────────


def test_locked_test_blocked_by_default() -> None:
    """Locked-test partition must not be used without allow_locked_test=True."""
    record = _valid_record(split="locked_test")
    errors = validate_record(record, allow_locked_test=False)
    assert any("allow_locked_test" in e for e in errors)


def test_locked_test_blocked_if_no_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Locked-test requires KESTREL_LOCKED_RUN=1."""
    monkeypatch.delenv("KESTREL_LOCKED_RUN", raising=False)
    record = _valid_record(split="locked_test")
    errors = validate_record(
        record,
        allow_locked_test=True,
        manifest_frozen=True,
        expected_config_hash="deadbeef12345678",
    )
    assert any("KESTREL_LOCKED_RUN" in e for e in errors)


def test_locked_test_blocked_if_manifest_not_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    """Locked-test requires manifest_frozen=True."""
    monkeypatch.setenv("KESTREL_LOCKED_RUN", "1")
    record = _valid_record(split="locked_test")
    errors = validate_record(
        record,
        allow_locked_test=True,
        manifest_frozen=False,
        expected_config_hash="deadbeef12345678",
    )
    assert any("frozen=true" in e for e in errors)


def test_locked_test_blocked_if_config_hash_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Locked-test requires matching config_hash."""
    monkeypatch.setenv("KESTREL_LOCKED_RUN", "1")
    record = _valid_record(split="locked_test", config_hash="actual_hash")
    errors = validate_record(
        record,
        allow_locked_test=True,
        manifest_frozen=True,
        expected_config_hash="different_expected_hash",
    )
    assert any("matching config_hash" in e for e in errors)


def test_locked_test_passes_when_all_guards_satisfied(monkeypatch: pytest.MonkeyPatch) -> None:
    """Locked-test is accepted when all 4 conditions are met simultaneously."""
    monkeypatch.setenv("KESTREL_LOCKED_RUN", "1")
    expected_hash = "deadbeef12345678"
    record = _valid_record(split="locked_test", config_hash=expected_hash)
    errors = validate_record(
        record,
        allow_locked_test=True,
        manifest_frozen=True,
        expected_config_hash=expected_hash,
    )
    assert errors == []


# ── File-level validation ──────────────────────────────────────────────────────


def test_validate_jsonl_file_accepts_valid_records() -> None:
    records = [_valid_record(item_id=f"math-{i:03d}") for i in range(5)]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
        path = Path(fh.name)
    errors = validate_jsonl_file(path)
    path.unlink()
    assert errors == []


def test_validate_jsonl_file_reports_bad_lines() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(json.dumps(_valid_record()) + "\n")
        fh.write("not-json\n")
        bad = _valid_record(split="unknown_partition")
        fh.write(json.dumps(bad) + "\n")
        path = Path(fh.name)
    errors = validate_jsonl_file(path)
    path.unlink()
    assert len(errors) >= 2
    assert any("line 2" in e for e in errors)
    assert any("line 3" in e for e in errors)


def test_validate_jsonl_file_skips_blank_lines() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as fh:
        fh.write("\n")
        fh.write(json.dumps(_valid_record()) + "\n")
        fh.write("   \n")
        path = Path(fh.name)
    errors = validate_jsonl_file(path)
    path.unlink()
    assert errors == []


def test_committed_hardware_calibration_jsonl_is_valid() -> None:
    """The committed reports/step0_hardware_calibration.jsonl must strictly pass schema validation."""
    path = Path("reports/step0_hardware_calibration.jsonl")
    if not path.is_file():
        pytest.skip("reports/step0_hardware_calibration.jsonl not present")
    errors = validate_jsonl_file(path)
    assert errors == [], f"Validation errors found in committed calibration jsonl: {errors}"
