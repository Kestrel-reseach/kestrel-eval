"""Step 0 integration tests: no future leakage, checkpoint resume,
deterministic evaluation, and memory write timing.

These tests use only stdlib and pytest; no model weights or hardware needed.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import pytest

from evaluation.schema import validate_record

# ── 1. No future leakage ──────────────────────────────────────────────────────
# The locked-test partition must never be opened or used in any evaluation run
# that is not Step 10.


class TestNoFutureLeakage:
    """Guard that locked-test items cannot silently appear in development runs."""

    def test_locked_test_blocked_in_schema_by_default(self) -> None:
        """validate_record rejects locked_test split when allow_locked_test=False."""
        record = {
            "config_hash": "deadbeef",
            "correct": True,
            "energy_joules": 1.0,
            "energy_status": "unmeasured",
            "git_commit": "abc1234",
            "git_dirty": False,
            "group": "math",
            "item_id": "math-001",
            "passes": 1,
            "peak_vram_mb": 0.0,
            "retrieval_hits": 0,
            "bytes_read_from_ssd": 0,
            "run_id": "leak-test-001",
            "seed": 42,
            "split": "locked_test",
            "system": "P1",
            "tokens_generated": 10,
            "verifier_score": None,
            "wall_time_ms": 100.0,
            "inference_mode": "real",
            "simulated": False,
        }
        errors = validate_record(record, allow_locked_test=False)
        assert any("allow_locked_test" in e for e in errors), "schema must block locked_test"

    def test_locked_test_allowed_only_at_step_10(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With allow_locked_test=True, KESTREL_LOCKED_RUN=1, manifest_frozen=True,
        and matching config_hash, the locked_test record is accepted."""
        monkeypatch.setenv("KESTREL_LOCKED_RUN", "1")
        record = {
            "config_hash": "deadbeef",
            "correct": True,
            "energy_joules": 1.0,
            "energy_status": "unmeasured",
            "git_commit": "abc1234",
            "git_dirty": False,
            "group": "math",
            "item_id": "math-001",
            "passes": 1,
            "peak_vram_mb": 0.0,
            "retrieval_hits": 0,
            "bytes_read_from_ssd": 0,
            "run_id": "step10-001",
            "seed": 42,
            "split": "locked_test",
            "system": "P1",
            "tokens_generated": 10,
            "verifier_score": None,
            "wall_time_ms": 100.0,
            "inference_mode": "real",
            "simulated": False,
        }
        errors = validate_record(
            record,
            allow_locked_test=True,
            manifest_frozen=True,
            expected_config_hash="deadbeef",
        )
        assert errors == [], f"unexpected errors: {errors}"

    def test_partition_hashes_detect_overlap(self) -> None:
        """No item_id may appear in more than one partition."""
        partitions = {
            "train": ["math-001", "math-002", "math-003"],
            "validation": ["math-004", "math-005"],
            "locked_test": ["math-006", "math-007"],
        }
        all_ids: list[str] = []
        for ids in partitions.values():
            all_ids.extend(ids)

        seen: set[str] = set()
        duplicates: list[str] = []
        for item_id in all_ids:
            if item_id in seen:
                duplicates.append(item_id)
            seen.add(item_id)

        assert duplicates == [], f"items appear in multiple partitions: {duplicates}"

    def test_partition_hashes_detect_overlap_bad_case(self) -> None:
        """The duplicate-detection logic catches a real overlap."""
        partitions = {
            "train": ["math-001", "math-002"],
            "validation": ["math-002"],  # deliberately overlapping
        }
        all_ids: list[str] = []
        for ids in partitions.values():
            all_ids.extend(ids)

        seen: set[str] = set()
        duplicates: list[str] = []
        for item_id in all_ids:
            if item_id in seen:
                duplicates.append(item_id)
            seen.add(item_id)

        assert "math-002" in duplicates


# ── 2. Checkpoint resume ──────────────────────────────────────────────────────
# A run interrupted mid-way must be resumable from the last checkpoint without
# re-processing already-written items.


class TestCheckpointResume:
    """Simulate checkpoint/resume for a JSONL-based evaluation run."""

    def _make_checkpoint(self, path: Path, records: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")

    def _load_done_ids(self, path: Path) -> set[str]:
        done: set[str] = set()
        if not path.exists():
            return done
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    done.add(rec["item_id"])
        return done

    def test_resume_skips_already_written_items(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "run.jsonl"
        all_items = [f"math-{i:03d}" for i in range(10)]

        # First run: write first 5
        done_first_pass = all_items[:5]
        self._make_checkpoint(
            checkpoint,
            [{"item_id": item_id, "correct": True} for item_id in done_first_pass],
        )

        done_ids = self._load_done_ids(checkpoint)
        remaining = [item for item in all_items if item not in done_ids]

        assert len(remaining) == 5
        assert all(item not in done_ids for item in remaining)
        assert all(item in done_ids for item in done_first_pass)

    def test_resume_from_empty_file_processes_all(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "run.jsonl"
        all_items = [f"math-{i:03d}" for i in range(5)]
        done_ids = self._load_done_ids(checkpoint)
        remaining = [item for item in all_items if item not in done_ids]
        assert remaining == all_items

    def test_checkpoint_hash_matches_after_resume(self, tmp_path: Path) -> None:
        """The hash of a completed run must equal the hash of the same records
        written in one pass (order-stable JSONL)."""
        checkpoint = tmp_path / "run.jsonl"
        records = [
            {
                "config_hash": "deadbeef",
                "correct": i % 2 == 0,
                "energy_joules": 1.0,
                "energy_status": "unmeasured",
                "git_commit": "abc1234",
                "git_dirty": False,
                "group": "math",
                "item_id": f"math-{i:03d}",
                "passes": 1,
                "peak_vram_mb": 0.0,
                "retrieval_hits": 0,
                "bytes_read_from_ssd": 0,
                "run_id": "run-001",
                "seed": 42,
                "split": "validation",
                "system": "P1",
                "tokens_generated": 10,
                "verifier_score": None,
                "wall_time_ms": 100.0,
            }
            for i in range(10)
        ]
        # Write in two passes (simulating resume)
        with checkpoint.open("w", encoding="utf-8") as fh:
            for rec in records[:5]:
                fh.write(json.dumps(rec) + "\n")
        with checkpoint.open("a", encoding="utf-8") as fh:
            for rec in records[5:]:
                fh.write(json.dumps(rec) + "\n")

        content = checkpoint.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        assert len(sha) == 64  # valid hex digest

        # Compare to a single-pass write
        single_pass = tmp_path / "run_single.jsonl"
        with single_pass.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")
        sha2 = hashlib.sha256(single_pass.read_bytes()).hexdigest()
        assert sha == sha2


# ── 3. Deterministic evaluation ───────────────────────────────────────────────
# Same config and seed must produce the same results.


class TestDeterministicEvaluation:
    """Same config + seed → same output."""

    def _simulate_eval(self, seed: int, items: list[str]) -> list[dict]:
        """Simulate a fully deterministic eval: scores are hash(seed, item_id)."""
        results = []
        for item_id in items:
            digest = hashlib.sha256(f"{seed}:{item_id}".encode()).hexdigest()
            correct = int(digest[:2], 16) >= 128  # deterministic pseudo-label
            results.append({"correct": correct, "item_id": item_id, "seed": seed})
        return results

    def test_same_seed_same_results(self) -> None:
        items = [f"math-{i:03d}" for i in range(20)]
        run_a = self._simulate_eval(seed=20260101, items=items)
        run_b = self._simulate_eval(seed=20260101, items=items)
        assert run_a == run_b

    def test_different_seeds_differ(self) -> None:
        items = [f"math-{i:03d}" for i in range(20)]
        run_a = self._simulate_eval(seed=20260101, items=items)
        run_b = self._simulate_eval(seed=20260102, items=items)
        assert run_a != run_b

    def test_config_hash_changes_when_config_changes(self) -> None:
        def config_hash(config: dict) -> str:
            canonical = json.dumps(config, sort_keys=True).encode()
            return hashlib.sha256(canonical).hexdigest()

        config_a = {"model": "qwen3.5-0.8b", "seed": 42, "split": "validation"}
        config_b = {**config_a, "model": "granite-nano-1.5b"}

        assert config_hash(config_a) != config_hash(config_b)
        assert config_hash(config_a) == config_hash(config_a)  # idempotent

    def test_jsonl_output_is_stable_across_writes(self, tmp_path: Path) -> None:
        """Writing the same records twice produces the same bytes."""
        records = [
            {
                "correct": i % 2 == 0,
                "item_id": f"item-{i}",
                "run_id": "det-test",
                "seed": 42,
            }
            for i in range(5)
        ]

        def write(path: Path) -> None:
            with path.open("w", encoding="utf-8") as fh:
                for rec in records:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")

        p1, p2 = tmp_path / "run1.jsonl", tmp_path / "run2.jsonl"
        write(p1)
        write(p2)
        assert p1.read_bytes() == p2.read_bytes()


# ── 4. Memory write timing ────────────────────────────────────────────────────
# Write-gated memory writes must be measured and succeed without data corruption.


class TestMemoryWriteTiming:
    """Memory write timing: writes must succeed and record elapsed duration."""

    def _write_memory_entry(self, path: Path, entry: dict) -> float:
        """Write a single entry to a JSON-lines memory file, return wall time (s)."""
        start = time.monotonic()
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return time.monotonic() - start

    def _make_entry(self, index: int) -> dict:
        return {
            "confidence": 0.95,
            "correct": True,
            "decay_rule": "none",
            "entry_id": f"mem-{index:06d}",
            "source": "synthetic-history-001",
            "superseded": False,
            "text": "The capital of France is Paris.",
            "timestamp": "2026-01-01T00:00:00Z",
        }

    def test_single_memory_write_is_fast(self, tmp_path: Path) -> None:
        """A single fsync'd write to a local file completes and measures duration.

        Non-flaky check rationale:
        We assert that the write completes successfully, writes valid data, and
        finishes within a generous non-flaky bound (< 2.0 s). We do NOT assert an
        absolute 50 ms upper bound here because fsync latency is machine-dependent
        and highly vulnerable to transient I/O spikes, shared CI runner virtualization,
        or copy-on-write filesystems. Strict sub-50ms latency benchmarking belongs
        in dedicated local hardware qualification on the target NVMe drive, not CI.
        """
        path = tmp_path / "memory.jsonl"
        elapsed = self._write_memory_entry(path, self._make_entry(0))
        assert elapsed > 0.0, "Write duration must be positive"
        assert (
            elapsed < 2.0
        ), f"Memory write took {elapsed * 1000:.1f} ms, unexpectedly exceeding generous 2.0 s timeout."
        # Verify content integrity
        content = path.read_text(encoding="utf-8").strip()
        data = json.loads(content)
        assert data["entry_id"] == "mem-000000"

    def test_hundred_writes_succeeds_and_completes_reliably(self, tmp_path: Path) -> None:
        """100 sequential fsync'd writes complete reliably."""
        path = tmp_path / "memory.jsonl"
        start = time.monotonic()
        for i in range(100):
            self._write_memory_entry(path, self._make_entry(i))
        elapsed = time.monotonic() - start
        assert elapsed < 10.0, f"100 memory writes took {elapsed:.2f} s, expected < 10 s."

    def test_memory_file_contains_all_entries(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.jsonl"
        n = 10
        for i in range(n):
            self._write_memory_entry(path, self._make_entry(i))

        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) == n
        for i, line in enumerate(lines):
            rec = json.loads(line)
            assert rec["entry_id"] == f"mem-{i:06d}"

    def test_stale_fact_entry_records_superseded_flag(self, tmp_path: Path) -> None:
        """When a fact is superseded, old entry must be flagged, not deleted."""
        path = tmp_path / "memory.jsonl"
        old_entry = {
            "confidence": 0.90,
            "correct": True,
            "decay_rule": "none",
            "entry_id": "mem-000001",
            "source": "history-2024-01",
            "superseded": False,
            "text": "The CEO of Acme is Alice.",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        new_entry = {
            "confidence": 0.95,
            "correct": True,
            "decay_rule": "none",
            "entry_id": "mem-000002",
            "source": "history-2026-01",
            "superseded": False,
            "text": "The CEO of Acme is Bob.",
            "timestamp": "2026-01-01T00:00:00Z",
        }
        # Mark old entry as superseded (not deleted)
        old_entry_updated = {**old_entry, "superseded": True}

        self._write_memory_entry(path, old_entry_updated)
        self._write_memory_entry(path, new_entry)

        lines = path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines if line.strip()]

        assert len(records) == 2
        assert records[0]["superseded"] is True
        assert records[1]["superseded"] is False
        assert records[1]["text"] == "The CEO of Acme is Bob."
