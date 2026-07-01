"""Unit tests for the pure ingestion helpers (no DB, no FastF1)."""
import pandas as pd

from ingest.helpers import (
    drs_is_active,
    map_status,
    normalize_compound,
    normalize_team_color,
    normalize_track_status,
    safe_float,
    to_timedelta_or_none,
)


def test_safe_float_maps_nan_and_none_to_default():
    assert safe_float(float("nan")) == 0.0
    assert safe_float(None, 5.0) == 5.0
    assert safe_float("3.5") == 3.5
    assert safe_float("not-a-number", 1.0) == 1.0


def test_drs_is_active_only_for_open_codes():
    assert drs_is_active(10) and drs_is_active(12) and drs_is_active(14)
    assert not drs_is_active(8)
    assert not drs_is_active(0)
    assert not drs_is_active(None)


def test_normalize_compound():
    assert normalize_compound("soft") == "SOFT"
    assert normalize_compound("MEDIUM") == "MEDIUM"
    assert normalize_compound("unknown") == ""
    assert normalize_compound(float("nan")) == ""


def test_normalize_track_status_picks_most_severe():
    assert normalize_track_status("1") == "clear"
    assert normalize_track_status("2") == "yellow"
    assert normalize_track_status("4") == "sc"
    assert normalize_track_status("24") == "sc"  # SC outranks yellow
    assert normalize_track_status("5") == "red"
    assert normalize_track_status("6") == "vsc"
    assert normalize_track_status(float("nan")) == "clear"


def test_map_status():
    assert map_status("1", "Finished") == "Finished"
    assert map_status("R", "Retired") == "DNF"
    assert map_status("D", "Disqualified") == "DSQ"
    assert map_status("W", "Withdrew") == "DNS"
    assert map_status("", "+1 Lap") == "Finished"
    assert map_status("", "Accident") == "DNF"


def test_normalize_team_color():
    assert normalize_team_color("3671C6") == "#3671C6"
    assert normalize_team_color("#FF8000") == "#FF8000"
    assert normalize_team_color(float("nan")) == "#FFFFFF"
    assert normalize_team_color("") == "#FFFFFF"


def test_to_timedelta_or_none():
    assert to_timedelta_or_none(pd.NaT) is None
    assert to_timedelta_or_none(None) is None
    td = to_timedelta_or_none(pd.Timedelta(seconds=90.5))
    assert abs(td.total_seconds() - 90.5) < 1e-6
