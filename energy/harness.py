"""Energy measurement harness for Kestrel Prototype 1 — Step 0.

Measures CPU and GPU power on the target hardware (Ryzen 7 5800H,
RTX 3060 Laptop 6 GB).  Produces joules-per-task figures for every
evaluation run.

Design constraints (from PLAN.md and rules.md):
  - Metric: joules per correct task (not tokens/s/W).
  - Record a ~10 minute idle baseline; subtract it; also report the total.
  - Calibrate counters against a wall meter once.  If that is impossible,
    report relative energy only and label every result accordingly.
  - NVML reads the GPU; RAPL / hwmon reads the CPU.
  - No inference happens inside this module; it only records power.

Usage::

    from energy.harness import EnergyHarness, HarnessConfig

    config = HarnessConfig(idle_baseline_seconds=600)
    harness = EnergyHarness(config)
    harness.check_counters()       # raises if no counter is usable
    baseline = harness.record_idle_baseline()
    token = harness.start()
    # ... run your model here ...
    sample = harness.stop(token)
    joules_net = sample.energy_joules - baseline.energy_rate_joules_per_s * sample.wall_time_s
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "CpuCounterSource",
    "EnergyHarness",
    "EnergySample",
    "HarnessConfig",
    "IdleBaseline",
    "check_nvml_available",
    "read_cpu_energy_joules",
    "read_gpu_power_watts",
]

# ── CPU energy counter discovery ───────────────────────────────────────────────

#: Search order for Ryzen energy counters on Linux.
_RAPL_PACKAGE_GLOB = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"
_HWMON_GLOB_DIRS = Path("/sys/class/hwmon")


def _find_rapl_path() -> Path | None:
    """Return the RAPL package energy file path, or None if unavailable."""
    p = Path(_RAPL_PACKAGE_GLOB)
    if p.is_file() and os.access(p, os.R_OK):
        return p
    # Try numbering rapl:0 through rapl:3
    for index in range(4):
        candidate = Path(f"/sys/class/powercap/intel-rapl/intel-rapl:{index}/energy_uj")
        if candidate.is_file() and os.access(candidate, os.R_OK):
            return candidate
    return None


def _find_hwmon_power_path() -> Path | None:
    """Return a hwmon power1_average path for Ryzen, or None."""
    if not _HWMON_GLOB_DIRS.is_dir():
        return None
    for hwmon in sorted(_HWMON_GLOB_DIRS.iterdir()):
        name_file = hwmon / "name"
        if not name_file.is_file():
            continue
        name = name_file.read_text().strip().lower()
        if name in ("k10temp", "amdgpu", "ryzen_smu"):
            for candidate in hwmon.glob("power*_average"):
                if os.access(candidate, os.R_OK):
                    return candidate
    return None


class CpuCounterSource:
    """Discover and read the best available CPU energy counter."""

    def __init__(self) -> None:
        self._rapl: Path | None = _find_rapl_path()
        self._hwmon: Path | None = _find_hwmon_power_path()
        self._source: str = "none"
        if self._rapl:
            self._source = "rapl"
        elif self._hwmon:
            self._source = "hwmon"

    @property
    def source(self) -> str:
        """'rapl', 'hwmon', or 'none'."""
        return self._source

    @property
    def available(self) -> bool:
        return self._source != "none"

    def read_energy_uj(self) -> int | None:
        """Read the cumulative counter value in micro-joules.

        Returns None when no counter is available.  RAPL is an accumulating
        counter that wraps; callers must handle the wrap at ``max_energy_range_uj``.
        hwmon returns instantaneous power in micro-watts, not cumulative energy.
        """
        if self._rapl:
            try:
                return int(self._rapl.read_text().strip())
            except (OSError, ValueError):
                return None
        if self._hwmon:
            # hwmon power*_average is in micro-watts, not energy.
            # Return None here; callers use read_power_uw() for hwmon.
            return None
        return None

    def read_power_uw(self) -> float | None:
        """Read instantaneous power in micro-watts (hwmon only)."""
        if self._hwmon:
            try:
                return float(self._hwmon.read_text().strip())
            except (OSError, ValueError):
                return None
        return None

    def rapl_max_range_uj(self) -> int | None:
        """RAPL counter wrap point in micro-joules."""
        if not self._rapl:
            return None
        max_file = self._rapl.parent / "max_energy_range_uj"
        if max_file.is_file():
            try:
                return int(max_file.read_text().strip())
            except (OSError, ValueError):
                return None
        return None


# ── GPU counter via NVML ───────────────────────────────────────────────────────


def check_nvml_available() -> bool:
    """Return True if pynvml can be imported and NVML can be initialised."""
    try:
        import pynvml  # type: ignore[import-untyped]

        pynvml.nvmlInit()
        pynvml.nvmlShutdown()
        return True
    except Exception:  # noqa: BLE001
        return False


def read_gpu_power_watts() -> float | None:
    """Read instantaneous GPU power in watts from the first NVML device.

    Returns None when NVML is unavailable or the read fails.
    """
    try:
        import pynvml  # type: ignore[import-untyped]

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        milliwatts = pynvml.nvmlDeviceGetPowerUsage(handle)
        pynvml.nvmlShutdown()
        return milliwatts / 1000.0
    except Exception:  # noqa: BLE001
        return None


def read_cpu_energy_joules(source: CpuCounterSource) -> float | None:
    """Return current CPU energy in joules (RAPL cumulative or hwmon instant)."""
    if source.source == "rapl":
        uj = source.read_energy_uj()
        return uj / 1e6 if uj is not None else None
    if source.source == "hwmon":
        uw = source.read_power_uw()
        return uw / 1e6 if uw is not None else None  # caller accumulates over time
    return None


# ── Harness data classes ───────────────────────────────────────────────────────


@dataclass
class HarnessConfig:
    """Configuration for the energy harness."""

    idle_baseline_seconds: int = 600
    """Duration of the idle baseline recording in seconds (~10 minutes)."""

    sample_interval_s: float = 1.0
    """How often to poll power counters during a measurement window."""

    wall_meter_calibrated: bool | None = None
    """
    Set to True after calibrating counters against a plug-in wall meter.
    Set to False to record relative-only energy and label results accordingly.
    None means 'not yet determined' (Step 0 initial state).
    """

    relative_only: bool = False
    """True when wall-meter calibration was not possible.  Every result
    labelled with this flag must include 'relative energy only' in reports."""


@dataclass
class EnergySample:
    """Energy measurement for one timed window (one task or one run)."""

    wall_time_s: float
    """Elapsed wall-clock time in seconds."""

    cpu_energy_joules: float | None
    """CPU energy in joules over the window, or None if the counter is unavailable."""

    gpu_energy_joules: float | None
    """GPU energy in joules over the window, or None if NVML is unavailable."""

    energy_joules: float | None
    """Total (CPU + GPU) energy in joules, or None if neither counter is available."""

    relative_only: bool = False
    """True when the energy figure is relative (not calibrated against a wall meter)."""

    @property
    def has_energy(self) -> bool:
        return self.energy_joules is not None


@dataclass
class IdleBaseline:
    """Result of a ~10 minute idle-power recording."""

    duration_s: float
    """Actual recording duration in seconds."""

    cpu_power_w: float | None
    """Mean idle CPU power in watts, or None."""

    gpu_power_w: float | None
    """Mean idle GPU power in watts, or None."""

    total_power_w: float | None
    """Mean idle total power in watts, or None."""

    relative_only: bool = False
    """Mirrors HarnessConfig.relative_only."""

    samples: int = 0
    """Number of power samples collected."""

    @property
    def energy_rate_joules_per_s(self) -> float | None:
        """Idle power in watts = joules per second."""
        return self.total_power_w


@dataclass
class _MeasurementToken:
    """Internal token that tracks an in-progress measurement window."""

    start_wall: float = field(default_factory=time.monotonic)
    start_cpu_uj: int | None = None
    gpu_samples_w: list[float] = field(default_factory=list)
    cpu_samples_j: list[float] = field(default_factory=list)


# ── Main harness ───────────────────────────────────────────────────────────────


class EnergyHarness:
    """Measure CPU and GPU energy for Kestrel evaluation runs.

    Typical use::

        harness = EnergyHarness(config)
        harness.check_counters()
        baseline = harness.record_idle_baseline()
        token = harness.start()
        # ... your model call here ...
        sample = harness.stop(token)
    """

    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or HarnessConfig()
        self._cpu = CpuCounterSource()
        self._nvml_available = check_nvml_available()

    # ── Counter availability ────────────────────────────────────────────────

    def check_counters(self, *, strict: bool = True) -> dict[str, Any]:
        """Check which counters are available and determine the energy status.

        Step 0 Gate / Kill-gate rule:
        - If counters exist and are calibrated with a wall meter: ``measured_calibrated``.
        - If counters exist but are not calibrated against a wall meter: ``relative_only``
          (or ``measured_uncalibrated`` if pending calibration). Relative energy is allowed
          and must be labelled on every result.
        - If NO counters exist at all (neither CPU nor GPU): energy cannot be measured.
          If ``strict=True``, raises ``RuntimeError``; otherwise returns status with
          ``energy_status='unmeasured'``.

        Args:
            strict: If True, raise RuntimeError when no counter is found.
        """
        cpu_ok = self._cpu.available
        gpu_ok = self._nvml_available

        if self.config.wall_meter_calibrated:
            energy_status = "measured_calibrated"
        elif self.config.relative_only or (self.config.wall_meter_calibrated is False):
            energy_status = "relative_only"
        elif cpu_ok or gpu_ok:
            energy_status = "measured_uncalibrated"
        else:
            energy_status = "unmeasured"

        status: dict[str, Any] = {
            "cpu_available": cpu_ok,
            "cpu_counter_source": self._cpu.source,
            "energy_status": energy_status,
            "gpu_nvml_available": gpu_ok,
            "relative_only": energy_status == "relative_only",
            "wall_meter_calibrated": self.config.wall_meter_calibrated,
        }
        if strict and not cpu_ok and not gpu_ok:
            raise RuntimeError(
                "No hardware energy counter is available (CPU: none, GPU: none). "
                "Per Step 0 kill-gate, energy cannot be measured on this host. "
                "Report wall-time only and mark energy_status='unmeasured'."
            )
        return status

    # ── Idle baseline ───────────────────────────────────────────────────────

    def record_idle_baseline(
        self, duration_s: int | None = None, _sleep: Any = None
    ) -> IdleBaseline:
        """Record the idle power baseline.

        Polls power counters every ``config.sample_interval_s`` seconds for
        ``duration_s`` seconds (default: ``config.idle_baseline_seconds``).
        Returns an :class:`IdleBaseline` with mean idle-power figures.

        Args:
            duration_s: Override the config duration (useful in tests).
            _sleep: Injected sleep function (default: ``time.sleep``).
        """
        sleep = _sleep if _sleep is not None else time.sleep
        total_s = duration_s if duration_s is not None else self.config.idle_baseline_seconds
        interval = self.config.sample_interval_s

        cpu_powers: list[float] = []
        gpu_powers: list[float] = []
        elapsed = 0.0

        # First RAPL reading for cumulative delta
        prev_cpu_uj = self._cpu.read_energy_uj() if self._cpu.source == "rapl" else None
        prev_wall = time.monotonic()

        while elapsed < total_s:
            sleep(min(interval, total_s - elapsed))
            now = time.monotonic()
            dt = now - prev_wall
            elapsed += dt

            # CPU
            if self._cpu.source == "rapl":
                curr_uj = self._cpu.read_energy_uj()
                if curr_uj is not None and prev_cpu_uj is not None and dt > 0:
                    max_range = self._cpu.rapl_max_range_uj() or (1 << 32)
                    delta_uj = (curr_uj - prev_cpu_uj) % max_range
                    cpu_powers.append(delta_uj / 1e6 / dt)
                prev_cpu_uj = curr_uj
            elif self._cpu.source == "hwmon":
                uw = self._cpu.read_power_uw()
                if uw is not None:
                    cpu_powers.append(uw / 1e6)

            # GPU
            gpu_w = read_gpu_power_watts()
            if gpu_w is not None:
                gpu_powers.append(gpu_w)

            prev_wall = now

        cpu_power_w = sum(cpu_powers) / len(cpu_powers) if cpu_powers else None
        gpu_power_w = sum(gpu_powers) / len(gpu_powers) if gpu_powers else None

        total_power_w: float | None
        if cpu_power_w is not None and gpu_power_w is not None:
            total_power_w = cpu_power_w + gpu_power_w
        elif cpu_power_w is not None:
            total_power_w = cpu_power_w
        elif gpu_power_w is not None:
            total_power_w = gpu_power_w
        else:
            total_power_w = None

        return IdleBaseline(
            duration_s=elapsed,
            cpu_power_w=cpu_power_w,
            gpu_power_w=gpu_power_w,
            total_power_w=total_power_w,
            relative_only=self.config.relative_only,
            samples=len(cpu_powers) + len(gpu_powers),
        )

    # ── Per-task measurement ────────────────────────────────────────────────

    def start(self) -> _MeasurementToken:
        """Start a measurement window.  Returns an opaque token."""
        token = _MeasurementToken(start_wall=time.monotonic())
        if self._cpu.source == "rapl":
            token.start_cpu_uj = self._cpu.read_energy_uj()
        return token

    def stop(self, token: _MeasurementToken) -> EnergySample:
        """Stop a measurement window and return an :class:`EnergySample`."""
        end_wall = time.monotonic()
        wall_time_s = end_wall - token.start_wall

        # CPU energy
        cpu_energy_j: float | None = None
        if self._cpu.source == "rapl" and token.start_cpu_uj is not None:
            end_cpu_uj = self._cpu.read_energy_uj()
            if end_cpu_uj is not None:
                max_range = self._cpu.rapl_max_range_uj() or (1 << 32)
                delta_uj = (end_cpu_uj - token.start_cpu_uj) % max_range
                cpu_energy_j = delta_uj / 1e6
        elif self._cpu.source == "hwmon":
            # hwmon is instantaneous; approximate with midpoint × wall time
            mid_uw = self._cpu.read_power_uw()
            if mid_uw is not None:
                cpu_energy_j = mid_uw / 1e6 * wall_time_s

        # GPU energy (integrate over wall time, single sample is an approximation)
        gpu_energy_j: float | None = None
        gpu_w = read_gpu_power_watts()
        if gpu_w is not None:
            gpu_energy_j = gpu_w * wall_time_s

        # Total
        if cpu_energy_j is not None and gpu_energy_j is not None:
            total_j: float | None = cpu_energy_j + gpu_energy_j
        elif cpu_energy_j is not None:
            total_j = cpu_energy_j
        elif gpu_energy_j is not None:
            total_j = gpu_energy_j
        else:
            total_j = None

        return EnergySample(
            wall_time_s=wall_time_s,
            cpu_energy_joules=cpu_energy_j,
            gpu_energy_joules=gpu_energy_j,
            energy_joules=total_j,
            relative_only=self.config.relative_only,
        )

    # ── Convenience: net joules (idle-subtracted) ───────────────────────────

    @staticmethod
    def net_joules(sample: EnergySample, baseline: IdleBaseline) -> float | None:
        """Return task energy minus idle power × wall time.

        Returns None when energy is not measured.
        """
        if sample.energy_joules is None:
            return None
        if baseline.energy_rate_joules_per_s is None:
            return sample.energy_joules  # cannot subtract; return gross
        idle_during_task = baseline.energy_rate_joules_per_s * sample.wall_time_s
        return max(0.0, sample.energy_joules - idle_during_task)

    # ── Wall-meter calibration record ──────────────────────────────────────

    @staticmethod
    def record_wall_meter_calibration(
        *,
        wall_meter_joules: float,
        software_joules: float,
        duration_s: float,
        notes: str = "",
    ) -> dict[str, Any]:
        """Return a calibration record dict (save to a JSON file, not to the repo).

        Args:
            wall_meter_joules: Reading from the plug-in power meter.
            software_joules: Reading from RAPL/NVML for the same window.
            duration_s: Duration of the calibration window in seconds.
            notes: Any notes about measurement conditions.
        """
        ratio = software_joules / wall_meter_joules if wall_meter_joules else None
        return {
            "wall_meter_joules": wall_meter_joules,
            "software_joules": software_joules,
            "duration_s": duration_s,
            "software_to_wall_ratio": ratio,
            "notes": notes,
        }
