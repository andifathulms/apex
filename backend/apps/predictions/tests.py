"""Pure-function tests for the race-pace fuel-correction (no DB)."""
from datetime import timedelta

from apps.predictions.tasks import (
    FUEL_EFFECT_S_PER_LAP,
    MIN_STINT_LAPS,
    _fuel_corrected_seconds,
)


class _FakeLap:
    """Duck-types the ORM Lap: only .lap_time.total_seconds() is used."""

    def __init__(self, seconds: float):
        self.lap_time = timedelta(seconds=seconds)


def test_short_stint_is_not_a_long_run():
    laps = [_FakeLap(90.0) for _ in range(MIN_STINT_LAPS - 1)]
    assert _fuel_corrected_seconds(laps) == []


def test_long_run_applies_fuel_correction_trend():
    laps = [_FakeLap(90.0) for _ in range(6)]  # identical raw times
    corrected = _fuel_corrected_seconds(laps)
    assert len(corrected) == 6
    # Later laps get more fuel-benefit added back, so the series rises.
    assert corrected[-1] > corrected[0]
    assert abs((corrected[1] - corrected[0]) - FUEL_EFFECT_S_PER_LAP) < 1e-6


def test_outlier_lap_is_dropped():
    laps = [_FakeLap(90.0) for _ in range(5)] + [_FakeLap(200.0)]
    corrected = _fuel_corrected_seconds(laps)
    # The 200s traffic lap (> 107% of best) is excluded.
    assert all(v < 150 for v in corrected)
    assert len(corrected) == 5
