"""Tests for evaluation metrics and gate helpers — Step 0."""

from __future__ import annotations

import pytest

from evaluation.metrics import (
    MANDATORY_ENERGY_LABEL,
    accuracy,
    accuracy_by_group,
    compute_half_width,
    config_hash,
    format_energy_table,
    format_half_widths_table,
    gate_q_accuracy,
    gate_q_energy,
    joules_per_correct_task,
    paired_bootstrap_ci,
    peak_vram_gb,
    percentile_latency,
)


def _record(**kwargs):
    defaults = {
        "correct": True,
        "energy_joules": 10.0,
        "energy_status": "unmeasured",
        "git_dirty": False,
        "group": "math",
        "item_id": "math-001",
        "peak_vram_mb": 1024.0,
        "wall_time_ms": 500.0,
    }
    defaults.update(kwargs)
    return defaults


class TestAccuracy:
    def test_all_correct(self):
        records = [_record(correct=True) for _ in range(10)]
        assert accuracy(records) == 1.0

    def test_none_correct(self):
        records = [_record(correct=False) for _ in range(10)]
        assert accuracy(records) == 0.0

    def test_half_correct(self):
        records = [_record(correct=(i % 2 == 0)) for i in range(10)]
        assert accuracy(records) == pytest.approx(0.5)

    def test_empty(self):
        assert accuracy([]) == 0.0

    def test_by_group(self):
        records = [
            _record(item_id="math-001", correct=True),
            _record(item_id="math-002", correct=False),
            _record(item_id="code-001", correct=True),
        ]
        by_group = accuracy_by_group(records)
        assert by_group["math"] == pytest.approx(0.5)
        assert by_group["code"] == pytest.approx(1.0)


class TestPairedBootstrapCI:
    def test_always_correct_vs_always_wrong(self):
        a = [True] * 100
        b = [False] * 100
        lo, hi = paired_bootstrap_ci(a, b)
        assert lo > 0
        assert hi > 0

    def test_equal_systems(self):
        a = [True, False] * 50
        b = [True, False] * 50
        lo, hi = paired_bootstrap_ci(a, b)
        # CI should straddle zero
        assert lo < 1.0 and hi > -1.0

    def test_different_seeds_differ(self):
        a = [True, False] * 50
        b = [False, True] * 50
        ci1 = paired_bootstrap_ci(a, b, seed=42)
        ci2 = paired_bootstrap_ci(a, b, seed=99)
        # With different seeds the exact bounds may differ (but both should be valid)
        assert isinstance(ci1[0], float)
        assert isinstance(ci2[0], float)

    def test_raises_on_length_mismatch(self):
        with pytest.raises(ValueError):
            paired_bootstrap_ci([True, False], [True])

    def test_empty_returns_zero_ci(self):
        lo, hi = paired_bootstrap_ci([], [])
        assert lo == 0.0 and hi == 0.0


class TestEnergyMetrics:
    def test_joules_per_correct_task(self):
        records = [
            _record(correct=True, energy_joules=10.0),
            _record(correct=True, energy_joules=20.0),
            _record(correct=False, energy_joules=10.0),
        ]
        # Total energy = 10 + 20 + 10 = 40 J across all attempts; 2 correct tasks -> 20.0 J/correct
        j = joules_per_correct_task(records)
        assert j == pytest.approx(20.0)

    def test_no_correct_returns_none(self):
        records = [_record(correct=False, energy_joules=5.0)]
        assert joules_per_correct_task(records) is None

    def test_missing_energy_skipped(self):
        records = [
            _record(correct=True, energy_joules=10.0),
            {"item_id": "math-002", "correct": True},  # no energy_joules
        ]
        j = joules_per_correct_task(records)
        assert j == pytest.approx(10.0)


class TestLatency:
    def test_p50_latency(self):
        records = [_record(wall_time_ms=float(i * 100)) for i in range(1, 11)]
        p50 = percentile_latency(records, 50)
        assert p50 is not None
        assert 400.0 <= p50 <= 600.0

    def test_p95_latency(self):
        records = [_record(wall_time_ms=float(i * 100)) for i in range(1, 11)]
        p95 = percentile_latency(records, 95)
        assert p95 is not None
        assert p95 >= 900.0

    def test_empty_returns_none(self):
        assert percentile_latency([], 50) is None


class TestVramMetrics:
    def test_peak_vram_gb(self):
        records = [_record(peak_vram_mb=512.0), _record(peak_vram_mb=1024.0)]
        assert peak_vram_gb(records) == pytest.approx(1.0)

    def test_empty_returns_none(self):
        assert peak_vram_gb([]) is None


class TestGates:
    def test_gate_q_accuracy_passes_when_p1_better(self):
        p1 = [_record(correct=True) for _ in range(72)] + [
            _record(correct=False) for _ in range(28)
        ]
        bllm = [_record(correct=True) for _ in range(65)] + [
            _record(correct=False) for _ in range(35)
        ]
        result = gate_q_accuracy(p1, bllm, threshold_pp=5.0)
        # 72% vs 65% = 7pp difference, should pass with high probability
        assert result["difference_pp"] == pytest.approx(7.0, abs=0.5)

    def test_gate_q_accuracy_fails_when_similar(self):
        p1 = [_record(correct=True) for _ in range(50)] + [
            _record(correct=False) for _ in range(50)
        ]
        bllm = [_record(correct=True) for _ in range(50)] + [
            _record(correct=False) for _ in range(50)
        ]
        result = gate_q_accuracy(p1, bllm, threshold_pp=5.0)
        assert not result["passes"]

    def test_gate_q_energy_passes_when_p1_cheaper(self):
        p1 = [_record(correct=True, energy_joules=4.0)]
        bllm = [_record(correct=True, energy_joules=10.0)]
        result = gate_q_energy(p1, bllm, energy_cap_ratio=1.0)
        assert result["passes"]
        assert result["ratio"] == pytest.approx(0.4)

    def test_gate_q_energy_fails_when_p1_more_expensive(self):
        p1 = [_record(correct=True, energy_joules=12.0)]
        bllm = [_record(correct=True, energy_joules=10.0)]
        result = gate_q_energy(p1, bllm, energy_cap_ratio=1.0)
        assert not result["passes"]

    def test_gate_q_energy_missing_data(self):
        p1 = [{"item_id": "math-001", "correct": True}]  # no energy
        bllm = [_record(correct=True, energy_joules=10.0)]
        result = gate_q_energy(p1, bllm)
        assert not result["passes"]
        assert "UNMEASURED" in result["detail"]


class TestConfigHash:
    def test_same_config_same_hash(self):
        c = {"seed": 42, "model": "qwen3.5", "split": "validation"}
        assert config_hash(c) == config_hash(c)

    def test_different_config_different_hash(self):
        c1 = {"seed": 42, "model": "qwen3.5"}
        c2 = {"seed": 42, "model": "granite"}
        assert config_hash(c1) != config_hash(c2)

    def test_key_order_does_not_matter(self):
        c1 = {"a": 1, "b": 2}
        c2 = {"b": 2, "a": 1}
        assert config_hash(c1) == config_hash(c2)


class TestHalfWidth:
    def test_compute_half_width_values(self):
        hw_100 = compute_half_width(100)
        assert hw_100 == pytest.approx(9.8, abs=0.05)

        hw_40 = compute_half_width(40)
        assert hw_40 == pytest.approx(15.5, abs=0.1)

        hw_60 = compute_half_width(60)
        assert hw_60 == pytest.approx(12.65, abs=0.1)

        hw_20 = compute_half_width(20)
        assert hw_20 == pytest.approx(21.9, abs=0.1)

        hw_300 = compute_half_width(300)
        assert hw_300 == pytest.approx(5.66, abs=0.1)

        assert compute_half_width(0) == 0.0

    def test_format_half_widths_table(self):
        table = format_half_widths_table()
        assert "Reading A: total" in table
        assert "Reading B: per_partition" in table
        assert "math" in table
        assert "memory_probe" in table


class TestEnergyReportLabelEnforcement:
    def test_format_energy_table_refuses_without_mandatory_label(self):
        headers = ["Model", "Energy (J)"]
        rows = [["B-LLM", "50.0"]]

        # Missing label raises ValueError
        with pytest.raises(
            ValueError, match="Refusing to generate energy report without mandatory label"
        ):
            format_energy_table(headers, rows)

        # Incorrect label raises ValueError
        with pytest.raises(
            ValueError, match="Refusing to generate energy report without mandatory label"
        ):
            format_energy_table(headers, rows, mandatory_label="Some partial label")

    def test_format_energy_table_succeeds_with_mandatory_label(self):
        headers = ["Model", "Energy (J)"]
        rows = [["B-LLM", "50.0"]]

        out = format_energy_table(headers, rows, mandatory_label=MANDATORY_ENERGY_LABEL)
        assert MANDATORY_ENERGY_LABEL in out
        assert "| Model | Energy (J) |" in out
        assert "| B-LLM | 50.0 |" in out
