"""Lap-level session ingestion (fast path — no telemetry).

Always run for every session. Telemetry is handled separately, on-demand.
"""
import logging

import fastf1
import pandas as pd

from .db import get_connection, resolve_driver_id, resolve_session_key
from .helpers import (
    normalize_compound,
    normalize_track_status,
    to_timedelta_or_none,
)

logger = logging.getLogger(__name__)


def upsert_lap_row(conn, session_key, driver_id, lap):
    """Insert or update a single lap row using the shared DB connection."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO timing_lap (
                session_id, driver_id, lap_number, lap_time,
                sector1_time, sector2_time, sector3_time,
                compound, tyre_life, stint_number, is_personal_best,
                pit_in, pit_out, track_status, created_at, updated_at
            ) VALUES (
                %(session_id)s, %(driver_id)s, %(lap_number)s, %(lap_time)s,
                %(sector1)s, %(sector2)s, %(sector3)s,
                %(compound)s, %(tyre_life)s, %(stint)s, %(is_pb)s,
                %(pit_in)s, %(pit_out)s, %(track_status)s, NOW(), NOW()
            )
            ON CONFLICT (session_id, driver_id, lap_number) DO UPDATE SET
                lap_time = EXCLUDED.lap_time,
                sector1_time = EXCLUDED.sector1_time,
                sector2_time = EXCLUDED.sector2_time,
                sector3_time = EXCLUDED.sector3_time,
                compound = EXCLUDED.compound,
                tyre_life = EXCLUDED.tyre_life,
                stint_number = EXCLUDED.stint_number,
                is_personal_best = EXCLUDED.is_personal_best,
                pit_in = EXCLUDED.pit_in,
                pit_out = EXCLUDED.pit_out,
                track_status = EXCLUDED.track_status,
                updated_at = NOW()
            """,
            {
                "session_id": session_key,
                "driver_id": driver_id,
                "lap_number": int(lap["LapNumber"]),
                "lap_time": to_timedelta_or_none(lap["LapTime"]),
                "sector1": to_timedelta_or_none(lap["Sector1Time"]),
                "sector2": to_timedelta_or_none(lap["Sector2Time"]),
                "sector3": to_timedelta_or_none(lap["Sector3Time"]),
                "compound": normalize_compound(lap["Compound"]),
                "tyre_life": None if pd.isna(lap["TyreLife"]) else int(lap["TyreLife"]),
                "stint": None if pd.isna(lap["Stint"]) else int(lap["Stint"]),
                "is_pb": bool(lap.get("IsPersonalBest", False)),
                "pit_in": not pd.isna(lap["PitInTime"]),
                "pit_out": not pd.isna(lap["PitOutTime"]),
                "track_status": normalize_track_status(lap.get("TrackStatus")),
            },
        )


def ingest_session_laps(year: int, gp_name: str, session_type: str):
    """Load lap/results data for a session and persist Lap rows."""
    session_key = resolve_session_key(year, gp_name, session_type)
    if session_key is None:
        raise ValueError(
            f"No session row for {year} {gp_name} {session_type}. "
            "Backfill seasons/grands prix first."
        )

    session = fastf1.get_session(year, gp_name, session_type)
    session.load(telemetry=False, weather=True, messages=False)  # fast path

    inserted = 0
    with get_connection() as conn:
        for _, lap in session.laps.iterrows():
            driver_id = resolve_driver_id(lap["Driver"])
            if driver_id is None:
                logger.warning("Unknown driver code %s — skipping lap", lap["Driver"])
                continue
            upsert_lap_row(conn, session_key, driver_id, lap)
            inserted += 1

        # Persist weather summary + mark loaded
        weather = _summarize_weather(session)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE seasons_session SET weather_summary = %s::jsonb, "
                "is_loaded = TRUE, updated_at = NOW() WHERE id = %s",
                (weather, session_key),
            )

    logger.info("Ingested %d laps for %s %s %s", inserted, year, gp_name, session_type)
    return {"session_id": session_key, "laps": inserted}


def _summarize_weather(session) -> str:
    import json

    try:
        wdf = session.weather_data
        if wdf is None or wdf.empty:
            return json.dumps({})
        return json.dumps({
            "air_temp": round(float(wdf["AirTemp"].mean()), 1),
            "track_temp": round(float(wdf["TrackTemp"].mean()), 1),
            "humidity": round(float(wdf["Humidity"].mean()), 1),
            "rainfall": bool(wdf["Rainfall"].any()),
        })
    except Exception as exc:  # weather is best-effort
        logger.warning("Weather summary failed: %s", exc)
        return json.dumps({})
