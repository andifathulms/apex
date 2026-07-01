"""Small pure helpers shared by ingestion modules."""
import pandas as pd

VALID_COMPOUNDS = {"SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"}

# FastF1 DRS numeric codes that mean DRS is active/open (see CLAUDE.md).
DRS_ACTIVE_VALUES = {10, 12, 14}


def to_timedelta_or_none(value):
    """Convert a pandas Timedelta/NaT to a Python timedelta or None."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timedelta):
        return value.to_pytimedelta()
    return value


def normalize_compound(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    compound = str(value).strip().upper()
    return compound if compound in VALID_COMPOUNDS else ""


def normalize_track_status(raw) -> str:
    """Map FastF1 TrackStatus flags to our enum.

    FastF1 TrackStatus is a string of concatenated digit codes where
    1=clear/green, 2=yellow, 4=SC, 5=red, 6=VSC, 7=VSC ending. We take the
    most severe flag present.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return "clear"
    codes = set(str(raw))
    if "5" in codes:
        return "red"
    if "4" in codes:
        return "sc"
    if "6" in codes or "7" in codes:
        return "vsc"
    if "2" in codes:
        return "yellow"
    return "clear"


def drs_is_active(value) -> bool:
    try:
        return int(value) in DRS_ACTIVE_VALUES
    except (TypeError, ValueError):
        return False
