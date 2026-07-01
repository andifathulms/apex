"""Pure-function tests for API services (no DB)."""
from apps.api.services import compute_delta_trace


def test_delta_trace_measures_gap_at_distance():
    t1 = [
        {"distance": 0, "time_offset": 0.0},
        {"distance": 100, "time_offset": 2.0},
    ]
    t2 = [
        {"distance": 0, "time_offset": 0.0},
        {"distance": 100, "time_offset": 2.5},
    ]
    delta = compute_delta_trace(t1, t2)
    # Driver 2 is 0.5s slower by 100m => positive delta.
    assert delta[-1]["distance"] == 100
    assert abs(delta[-1]["delta"] - 0.5) < 1e-6


def test_delta_trace_resamples_driver2_by_nearest_lower():
    t1 = [{"distance": d, "time_offset": d / 50.0} for d in (0, 50, 100)]
    t2 = [{"distance": 0, "time_offset": 0.0}, {"distance": 100, "time_offset": 2.2}]
    delta = compute_delta_trace(t1, t2)
    assert len(delta) == 3  # one point per driver-1 sample


def test_delta_trace_empty_when_a_side_missing():
    assert compute_delta_trace([], [{"distance": 0, "time_offset": 0.0}]) == []
    assert compute_delta_trace([{"distance": 0, "time_offset": 0.0}], []) == []
