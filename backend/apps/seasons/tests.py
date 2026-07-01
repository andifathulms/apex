"""Pure-function tests for live-polling helpers (no DB)."""
from apps.seasons.tasks import _OPENF1_SESSION_TYPES, _parse_dt


def test_parse_dt_handles_iso_and_bad_input():
    dt = _parse_dt("2026-06-28T13:00:00+00:00")
    assert dt is not None and dt.year == 2026 and dt.hour == 13
    assert _parse_dt(None) is None
    assert _parse_dt("not-a-date") is None


def test_parse_dt_accepts_trailing_z():
    dt = _parse_dt("2026-06-28T13:00:00Z")
    assert dt is not None and dt.year == 2026


def test_openf1_session_type_mapping():
    assert _OPENF1_SESSION_TYPES["Race"] == "R"
    assert _OPENF1_SESSION_TYPES["Qualifying"] == "Q"
    assert _OPENF1_SESSION_TYPES["Practice 2"] == "FP2"
    assert _OPENF1_SESSION_TYPES["Sprint"] == "S"
