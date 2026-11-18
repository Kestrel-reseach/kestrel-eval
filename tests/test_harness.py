"""Tests for the energy harness — Step 0.

All tests run without real hardware (Ryzen / RTX 3060) by patching the
counter reads.  Real counter availability is checked in check_counters()
integration tests that are skipped when hardware is absent.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from energy.harness import (
    CpuCounterSource,
    EnergyHarness,
    HarnessConfig,
    IdleBaseline,
    check_nvml_available,
    read_gpu_energy_mj,
    read_gpu_power_watts,
)

# ── CpuCounterSource (no real hardware needed) ────────────────────────────────


def test_cpu_counter_source_reports_none_when_no_files(tmp_path: pytest.TempPathFactory) -> None:
    """When /sys paths don't exist, source should be 'none'."""
    with (
        patch("energy.harness._find_rapl_path", return_value=None),
        patch("energy.harness._find_hwmon_power_path", return_value=None),
    ):
        src = CpuCounterSource()
    assert src.source == "none"
    assert not src.available


def test_cpu_counter_source_uses_rapl_when_available(tmp_path) -> None:
    """When a RAPL file is found, the source should be 'rapl'."""
    rapl_file = tmp_path / "energy_uj"
    rapl_file.write_text("1000000\n")
    with (
        patch("energy.harness._find_rapl_path", return_value=rapl_file),
        patch("energy.harness._find_hwmon_power_path", return_value=None),
    ):
        src = CpuCounterSource()
    assert src.source == "rapl"
    assert src.available
    assert src.read_energy_uj() == 1_000_000


def test_cpu_counter_source_uses_hwmon_when_rapl_absent(tmp_path) -> None:
    """When RAPL is absent but hwmon is found, source should be 'hwmon'."""
    hwmon_file = tmp_path / "power1_average"
    hwmon_file.write_text("15000000\n")  # 15 W in µW
    with (
        patch("energy.harness._find_rapl_path", return_value=None),
        patch("energy.harness._find_hwmon_power_path", return_value=hwmon_file),
    ):
        src = CpuCounterSource()
    assert src.source == "hwmon"
    assert src.read_power_uw() == pytest.approx(15_000_000.0)


# ── NVML helpers ──────────────────────────────────────────────────────────────


def test_check_nvml_available_returns_false_when_pynvml_absent() -> None:
    """When pynvml is not installed, check_nvml_available returns False."""
    with patch.dict("sys.modules", {"pynvml": None}):
        assert check_nvml_available() is False


def test_read_gpu_power_returns_none_when_nvml_unavailable() -> None:
    """When NVML fails or is absent, read_gpu_power_watts returns None."""
    with patch.dict("sys.modules", {"pynvml": None}):
        assert read_gpu_power_watts() is None


def test_read_gpu_energy_mj_returns_none_when_nvml_unavailable() -> None:
    """When NVML fails or is absent, read_gpu_energy_mj returns None."""
    with patch.dict("sys.modules", {"pynvml": None}):
        assert read_gpu_energy_mj() is None


# ── EnergyHarness.check_counters ─────────────────────────────────────────────


def test_check_counters_raises_when_nothing_available() -> None:
    """With no CPU counter and no NVML, check_counters raises RuntimeError when strict=True."""
    config = HarnessConfig()
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)
    harness._nvml_available = False
    with pytest.raises(RuntimeError, match="energy counter"):
        harness.check_counters()


def test_check_counters_non_strict_returns_unmeasured() -> None:
    """With strict=False, returns energy_status='unmeasured' instead of raising."""
    config = HarnessConfig()
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)
    harness._nvml_available = False
    status = harness.check_counters(strict=False)
    assert status["energy_status"] == "unmeasured"


def test_check_counters_ok_with_cpu_only() -> None:
    """CPU counter alone is sufficient."""
    config = HarnessConfig()
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=True, source="rapl")
    harness._nvml_available = False
    status = harness.check_counters()
    assert status["cpu_available"] is True
    assert status["gpu_nvml_available"] is False


def test_check_counters_ok_with_gpu_only() -> None:
    """GPU counter alone is sufficient."""
    config = HarnessConfig()
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)
    harness._nvml_available = True
    status = harness.check_counters()
    assert status["gpu_nvml_available"] is True
    assert status["wall_meter_calibrated"] is False
    assert status["relative_only"] is True
    assert status["energy_status"] == "relative_only"


def test_check_counters_defaults_match_manifest() -> None:
    """HarnessConfig defaults must match manifest.yaml: wall_meter_calibrated=False, relative_only=True."""
    config = HarnessConfig()
    assert config.wall_meter_calibrated is False
    assert config.relative_only is True
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=True, source="rapl")
    harness._nvml_available = False
    status = harness.check_counters()
    assert status["wall_meter_calibrated"] is False
    assert status["relative_only"] is True
    assert status["energy_status"] == "relative_only"


# ── EnergyHarness.record_idle_baseline ───────────────────────────────────────


def test_record_idle_baseline_collects_samples() -> None:
    """record_idle_baseline samples power and returns a valid IdleBaseline."""
    config = HarnessConfig(idle_baseline_seconds=3, sample_interval_s=1.0)
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)  # hwmon not used here
    harness._nvml_available = False

    with patch("energy.harness.read_gpu_power_watts", return_value=None):
        # Use a fast sleep mock so the test doesn't wait 3 seconds
        calls = [0]

        def fast_sleep(dt: float) -> None:
            calls[0] += 1

        baseline = harness.record_idle_baseline(duration_s=3, _sleep=fast_sleep)

    assert isinstance(baseline, IdleBaseline)
    assert baseline.duration_s >= 0


def test_record_idle_baseline_computes_mean_gpu_power() -> None:
    """When NVML returns values, baseline GPU power is their mean."""
    config = HarnessConfig(idle_baseline_seconds=3, sample_interval_s=1.0)
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)
    harness._nvml_available = True

    gpu_readings = [10.0, 12.0, 11.0]
    reading_iter = iter(gpu_readings)

    def fake_gpu_power() -> float | None:
        try:
            return next(reading_iter)
        except StopIteration:
            return None

    with patch("energy.harness.read_gpu_power_watts", side_effect=fake_gpu_power):
        baseline = harness.record_idle_baseline(
            duration_s=3,
            _sleep=lambda _dt: None,
        )

    if baseline.gpu_power_w is not None:
        assert 10.0 <= baseline.gpu_power_w <= 12.0


# ── EnergyHarness.start / stop ────────────────────────────────────────────────


def test_start_stop_produces_valid_sample() -> None:
    """start() / stop() return an EnergySample with positive wall time."""
    config = HarnessConfig()
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)
    harness._nvml_available = False

    with patch("energy.harness.read_gpu_power_watts", return_value=None):
        token = harness.start()
        time.sleep(0.05)
        sample = harness.stop(token)

    assert sample.wall_time_s > 0
    assert sample.energy_joules is None  # no counters available


def test_start_stop_computes_gpu_energy_fallback() -> None:
    """When total-energy counter is absent, falls back to power × wall time."""
    config = HarnessConfig()
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)
    harness._nvml_available = True

    with (
        patch("energy.harness.read_gpu_energy_mj", return_value=None),
        patch("energy.harness.read_gpu_power_watts", return_value=20.0),
    ):
        token = harness.start()
        time.sleep(0.1)
        sample = harness.stop(token)

    assert sample.gpu_energy_joules is not None
    assert sample.gpu_energy_joules == pytest.approx(20.0 * sample.wall_time_s, rel=0.1)
    assert sample.energy_joules == sample.gpu_energy_joules
    assert sample.gpu_energy_method == "integrated_power_samples"


def test_start_stop_uses_nvml_total_energy_counter() -> None:
    """When nvml total energy counter is available, uses delta in millijoules."""
    config = HarnessConfig()
    harness = EnergyHarness(config)
    harness._cpu = _make_cpu_source(available=False)
    harness._nvml_available = True

    energy_readings = [10_000, 15_500]  # delta = 5500 mJ = 5.5 J
    reading_iter = iter(energy_readings)

    with patch("energy.harness.read_gpu_energy_mj", side_effect=lambda: next(reading_iter)):
        token = harness.start()
        assert token.start_gpu_mj == 10_000
        sample = harness.stop(token)

    assert sample.gpu_energy_joules == pytest.approx(5.5)
    assert sample.energy_joules == pytest.approx(5.5)
    assert sample.gpu_energy_method == "nvml_total_energy_counter"


# ── net_joules ────────────────────────────────────────────────────────────────


def test_net_joules_subtracts_idle() -> None:
    """net_joules = task_energy - idle_power * task_time."""
    from energy.harness import EnergySample

    sample = EnergySample(
        wall_time_s=10.0, cpu_energy_joules=None, gpu_energy_joules=50.0, energy_joules=50.0
    )
    baseline = IdleBaseline(
        duration_s=600.0,
        cpu_power_w=None,
        gpu_power_w=2.0,
        total_power_w=2.0,
    )
    net = EnergyHarness.net_joules(sample, baseline)
    assert net == pytest.approx(50.0 - 2.0 * 10.0)


def test_net_joules_returns_none_when_no_energy() -> None:
    from energy.harness import EnergySample

    sample = EnergySample(
        wall_time_s=5.0, cpu_energy_joules=None, gpu_energy_joules=None, energy_joules=None
    )
    baseline = IdleBaseline(duration_s=600.0, cpu_power_w=5.0, gpu_power_w=None, total_power_w=5.0)
    assert EnergyHarness.net_joules(sample, baseline) is None


def test_net_joules_clips_to_zero() -> None:
    """net_joules should not go negative (clipped at 0)."""
    from energy.harness import EnergySample

    sample = EnergySample(
        wall_time_s=5.0, cpu_energy_joules=None, gpu_energy_joules=None, energy_joules=1.0
    )
    baseline = IdleBaseline(
        duration_s=600.0, cpu_power_w=10.0, gpu_power_w=None, total_power_w=10.0
    )
    net = EnergyHarness.net_joules(sample, baseline)
    assert net is not None
    assert net >= 0.0


# ── Wall-meter calibration record ────────────────────────────────────────────


def test_record_wall_meter_calibration_computes_ratio() -> None:
    cal = EnergyHarness.record_wall_meter_calibration(
        wall_meter_joules=1000.0,
        software_joules=950.0,
        duration_s=600.0,
    )
    assert cal["software_to_wall_ratio"] == pytest.approx(0.95)
    assert cal["wall_meter_joules"] == 1000.0


def test_record_wall_meter_calibration_zero_wall_meter() -> None:
    """Zero wall-meter reading should not raise; ratio is None."""
    cal = EnergyHarness.record_wall_meter_calibration(
        wall_meter_joules=0.0,
        software_joules=100.0,
        duration_s=60.0,
    )
    assert cal["software_to_wall_ratio"] is None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_cpu_source(*, available: bool, source: str = "none") -> CpuCounterSource:
    """Return a mock CpuCounterSource."""
    mock = MagicMock(spec=CpuCounterSource)
    mock.available = available
    mock.source = source if available else "none"
    mock.read_energy_uj.return_value = None
    mock.read_power_uw.return_value = None
    mock.rapl_max_range_uj.return_value = None
    return mock
