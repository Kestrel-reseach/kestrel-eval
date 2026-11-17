"""Tests for RunMatrix and checkpoint resume — Step 0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.run_matrix import RunConfig, RunMatrix, load_checkpoint


def _config(tmp_path: Path, run_id: str = "run-001") -> RunConfig:
    return RunConfig(
        run_id=run_id,
        git_commit="abc1234",
        seed=20260101,
        split="validation",
        system="P1",
        output_path=tmp_path / f"{run_id}.jsonl",
    )


def _items(n: int = 5) -> list[dict]:
    return [{"item_id": f"math-{i:03d}", "question": f"q{i}"} for i in range(n)]


class TestLoadCheckpoint:
    def test_empty_path_returns_empty_set(self, tmp_path: Path) -> None:
        done = load_checkpoint(tmp_path / "nonexistent.jsonl")
        assert done == set()

    def test_returns_written_item_ids(self, tmp_path: Path) -> None:
        path = tmp_path / "run.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps({"item_id": "math-001"}) + "\n")
            fh.write(json.dumps({"item_id": "math-002"}) + "\n")
        done = load_checkpoint(path)
        assert done == {"math-001", "math-002"}

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "run.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            fh.write("not-json\n")
            fh.write(json.dumps({"item_id": "math-001"}) + "\n")
        done = load_checkpoint(path)
        assert done == {"math-001"}


class TestRunMatrix:
    def test_dry_run_writes_all_items(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        matrix = RunMatrix(config, runner=None)
        items = _items(5)
        new = matrix.run(items)
        assert len(new) == 5
        # Verify file was written
        lines = config.output_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 5

    def test_resume_skips_already_written(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        items = _items(5)
        # First partial run: write 2 items manually
        with config.output_path.open("w", encoding="utf-8") as fh:
            for item in items[:2]:
                partial = {
                    "run_id": config.run_id,
                    "git_commit": config.git_commit,
                    "config_hash": config.config_hash,
                    "seed": config.seed,
                    "split": config.split,
                    "item_id": item["item_id"],
                    "system": config.system,
                    "tokens_generated": 0,
                    "passes": 1,
                    "verifier_score": None,
                    "retrieval_hits": 0,
                    "bytes_read_from_ssd": 0,
                    "energy_joules": 0.0,
                    "wall_time_ms": 0.0,
                    "peak_vram_mb": 0.0,
                    "correct": False,
                }
                fh.write(json.dumps(partial) + "\n")
        # Resume
        matrix = RunMatrix(config, runner=None)
        new = matrix.run(items)
        assert len(new) == 3  # only the remaining 3
        lines = config.output_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 5  # total 5 in file

    def test_records_pass_schema_validation(self, tmp_path: Path) -> None:
        from evaluation.schema import validate_record

        config = _config(tmp_path)
        matrix = RunMatrix(config, runner=None)
        new = matrix.run(_items(3))
        for rec in new:
            errors = validate_record(rec)
            assert errors == [], f"record for {rec['item_id']!r} failed: {errors}"

    def test_config_hash_is_deterministic(self, tmp_path: Path) -> None:
        config_a = _config(tmp_path, "run-001")
        config_b = _config(tmp_path, "run-001")
        assert config_a.config_hash == config_b.config_hash

    def test_different_run_ids_have_different_hashes(self, tmp_path: Path) -> None:
        config_a = _config(tmp_path, "run-001")
        config_b = _config(tmp_path, "run-002")
        assert config_a.config_hash != config_b.config_hash

    def test_config_save_and_load(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        save_path = tmp_path / "run-001_config.json"
        config.save(save_path)
        loaded = json.loads(save_path.read_text(encoding="utf-8"))
        assert loaded["run_id"] == config.run_id
        assert loaded["config_hash"] == config.config_hash
        assert loaded["git_commit"] == config.git_commit

    def test_locked_test_blocked_by_default(self, tmp_path: Path) -> None:
        config = RunConfig(
            run_id="run-001",
            git_commit="abc1234",
            seed=20260101,
            split="locked_test",
            system="P1",
            output_path=tmp_path / "run.jsonl",
            allow_locked_test=False,
        )
        matrix = RunMatrix(config, runner=None)
        with pytest.raises(ValueError, match="locked_test"):
            matrix.run(_items(1))

