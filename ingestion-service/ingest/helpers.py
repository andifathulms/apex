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


def safe_float(value, default: float = 0.0) -> float:
    """Coerce to float, mapping None/NaN to a default (never returns NaN).

    Note: `float(x or 0)` is a trap here — NaN is truthy, so `nan or 0` is nan.
    """
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# FastF1 ClassifiedPosition single-letter codes -> our DriverSessionEntry.Status.
_CLASSIFIED_STATUS = {
    "R": "DNF",  # Retired
    "D": "DSQ",  # Disqualified
    "E": "DSQ",  # Excluded
    "W": "DNS",  # Withdrew
    "F": "DNS",  # Failed to qualify
    "N": "DNS",  # Not classified
}


def map_status(classified, status) -> str:
    """Map FastF1 result status to our enum (Finished | DNF | DSQ | DNS).

    Prefer ClassifiedPosition (a numeric string means classified/finished, a
    letter means a special outcome); fall back to the free-text Status column.
    """
    c = "" if classified is None or (isinstance(classified, float) and pd.isna(classified)) else str(classified).strip()
    if c.isdigit():
        return "Finished"
    if c in _CLASSIFIED_STATUS:
        return _CLASSIFIED_STATUS[c]

    s = "" if status is None or (isinstance(status, float) and pd.isna(status)) else str(status)
    lowered = s.lower()
    if s == "Finished" or s.startswith("+"):
        return "Finished"
    if "disqualif" in lowered:
        return "DSQ"
    if "did not start" in lowered or "dns" in lowered:
        return "DNS"
    return "DNF"


def normalize_team_color(value) -> str:
    """FastF1 TeamColor ('3671C6' or NaN) -> '#RRGGBB'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "#FFFFFF"
    color = str(value).strip()
    if not color:
        return "#FFFFFF"
    return color if color.startswith("#") else f"#{color}"
