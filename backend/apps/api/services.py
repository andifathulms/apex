"""Helper functions that build API payloads and parse query params.

Kept separate from views so the request-parsing / data-shaping logic is unit
testable and views stay thin.
"""
from dataclasses import dataclass

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.seasons.models import Session
from apps.telemetry.models import Telemetry
from apps.timing.models import Lap


@dataclass
class TelemetryCompareParams:
    session: Session
    driver1: str
    lap1: int
    driver2: str
    lap2: int


def _int_param(request, key: str) -> int:
    raw = request.query_params.get(key)
    if raw is None:
        raise ValidationError({key: "This query parameter is required."})
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError({key: "Must be an integer."})


def _str_param(request, key: str) -> str:
    raw = request.query_params.get(key)
    if not raw:
        raise ValidationError({key: "This query parameter is required."})
    return raw


def parse_telemetry_compare_params(request) -> TelemetryCompareParams:
    session_id = _int_param(request, "session")
    session = get_object_or_404(Session, pk=session_id)
    return TelemetryCompareParams(
        session=session,
        driver1=_str_param(request, "driver1"),
        lap1=_int_param(request, "lap1"),
        driver2=_str_param(request, "driver2"),
        lap2=_int_param(request, "lap2"),
    )


def _serialize_telemetry_trace(lap: Lap) -> list[dict]:
    rows = (
        Telemetry.objects.filter(lap=lap)
        .order_by("distance")
        .values(
            "distance", "time_offset", "speed_kmh", "throttle_pct",
            "brake", "gear", "rpm", "drs", "x_position", "y_position",
        )
    )
    return list(rows)


def _resolve_lap(session: Session, driver_code: str, lap_number: int) -> Lap | None:
    return (
        Lap.objects.filter(
            session=session, driver__code=driver_code, lap_number=lap_number
        )
        .select_related("driver")
        .first()
    )


def compute_delta_trace(trace1: list[dict], trace2: list[dict]) -> list[dict]:
    """Cumulative time delta between two drivers along track distance.

    Positive delta => driver 2 is behind driver 1 at that distance. We resample
    driver 2 onto driver 1's distance axis by nearest-lower sample and diff the
    within-lap time offsets.
    """
    if not trace1 or not trace2:
        return []

    d2 = [(row["distance"], row["time_offset"]) for row in trace2]
    delta = []
    j = 0
    for row in trace1:
        dist = row["distance"]
        while j + 1 < len(d2) and d2[j + 1][0] <= dist:
            j += 1
        t2 = d2[j][1]
        t1 = row["time_offset"]
        if t1 is not None and t2 is not None:
            delta.append({"distance": dist, "delta": round(t2 - t1, 4)})
    return delta


def build_comparison_payload(params: TelemetryCompareParams) -> dict:
    lap1 = _resolve_lap(params.session, params.driver1, params.lap1)
    lap2 = _resolve_lap(params.session, params.driver2, params.lap2)
    trace1 = _serialize_telemetry_trace(lap1) if lap1 else []
    trace2 = _serialize_telemetry_trace(lap2) if lap2 else []

    return {
        "status": "ready",
        "session_id": params.session.id,
        "driver1": {
            "code": params.driver1,
            "lap_number": params.lap1,
            "telemetry": trace1,
        },
        "driver2": {
            "code": params.driver2,
            "lap_number": params.lap2,
            "telemetry": trace2,
        },
        "delta_trace": compute_delta_trace(trace1, trace2),
    }
