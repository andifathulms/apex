"""Lap-level session ingestion (fast path — no telemetry).

Always run for every session. Telemetry is handled separately, on-demand.
"""
import logging

import fastf1
import pandas as pd
import requests

from . import enable_cache
from .db import (
    get_connection,
    resolve_driver_id,
    resolve_round_number,
    resolve_season_id,
    resolve_session_key,
)
from .helpers import (
    map_status,
    normalize_compound,
    normalize_team_color,
    normalize_track_status,
    safe_float,
    to_timedelta_or_none,
)

logger = logging.getLogger(__name__)

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

# Jolpica endpoint + payload key per classified session type. Practice sessions
# have no official classification, so they are absent here (skipped).
_JOLPICA_CLASSIFICATION = {
    "R": ("results.json", "Results"),
    "S": ("sprint.json", "SprintResults"),
    "Q": ("qualifying.json", "QualifyingResults"),
}


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


def _fastest_laps_by_driver(laps) -> dict:
    """Map driver code -> (fastest LapTime timedelta, lap number)."""
    out: dict[str, tuple] = {}
    valid = laps[laps["LapTime"].notna()]
    for code, grp in valid.groupby("Driver"):
        idx = grp["LapTime"].idxmin()
        row = grp.loc[idx]
        out[code] = (to_timedelta_or_none(row["LapTime"]), int(row["LapNumber"]))
    return out


def upsert_team(conn, season_id: int, name, color=None) -> int | None:
    """Upsert a team within a season, keyed by (Jolpica) constructor name.

    Only overwrites color_hex when a real color is supplied — Jolpica has no
    colors, so we keep any color previously enriched from FastF1 (and never
    clobber a good color with the #FFFFFF fallback).
    """
    if name is None or (isinstance(name, float) and pd.isna(name)) or not str(name).strip():
        return None

    hex_color = normalize_team_color(color)
    has_color = bool(color) and hex_color.upper() != "#FFFFFF"
    with conn.cursor() as cur:
        if has_color:
            cur.execute(
                """
                INSERT INTO seasons_team (name, nationality, color_hex, season_id,
                    created_at, updated_at)
                VALUES (%s, '', %s, %s, NOW(), NOW())
                ON CONFLICT (name, season_id) DO UPDATE SET
                    color_hex = EXCLUDED.color_hex, updated_at = NOW()
                RETURNING id
                """,
                (str(name).strip(), hex_color, season_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO seasons_team (name, nationality, color_hex, season_id,
                    created_at, updated_at)
                VALUES (%s, '', '#FFFFFF', %s, NOW(), NOW())
                ON CONFLICT (name, season_id) DO UPDATE SET updated_at = NOW()
                RETURNING id
                """,
                (str(name).strip(), season_id),
            )
        return cur.fetchone()[0]


def upsert_driver(conn, driver: dict) -> int | None:
    """Ensure a Jolpica driver exists (safety net; standings sync usually made it)."""
    driver_ref = driver.get("driverId", "")
    code = driver.get("code") or driver_ref[:3].upper()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM seasons_driver WHERE external_driver_id = %s LIMIT 1",
            (driver_ref,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        full_name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip()
        cur.execute(
            """
            INSERT INTO seasons_driver (driver_number, code, full_name, nationality,
                external_driver_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
            """,
            (
                int(driver["permanentNumber"]) if driver.get("permanentNumber") else None,
                code, full_name, driver.get("nationality", ""), driver_ref,
            ),
        )
        return cur.fetchone()[0]


def _fastf1_team_colors(session) -> dict:
    """Map driver code -> '#RRGGBB' from FastF1 results (its reliable field)."""
    out: dict[str, str] = {}
    results = getattr(session, "results", None)
    if results is None or results.empty:
        return out
    for _, row in results.iterrows():
        code = row.get("Abbreviation")
        if code is not None and not pd.isna(code):
            out[str(code)] = normalize_team_color(row.get("TeamColor"))
    return out


def _jolpica_classification(year: int, rnd: int, session_type: str) -> list:
    cfg = _JOLPICA_CLASSIFICATION.get(session_type)
    if cfg is None:
        return []
    path, key = cfg
    resp = requests.get(f"{JOLPICA_BASE}/{year}/{rnd}/{path}", timeout=20)
    resp.raise_for_status()
    races = resp.json().get("MRData", {}).get("RaceTable", {}).get("Races", [])
    return races[0].get(key, []) if races else []


def ingest_results(conn, session_key: int, season_id: int, fastest: dict,
                   colors: dict, year: int, rnd: int, session_type: str) -> int:
    """Persist DriverSessionEntry rows from Jolpica classification.

    FastF1's own results are Ergast-sourced and empty when Ergast is down, so
    the authoritative classification (position/grid/points/status) comes from
    Jolpica; team colors are enriched from FastF1 via the driver code.
    """
    rows = _jolpica_classification(year, rnd, session_type)
    if not rows:
        return 0

    count = 0
    for r in rows:
        drv = r.get("Driver", {})
        code = drv.get("code") or drv.get("driverId", "")[:3].upper()
        driver_id = resolve_driver_id(code) or upsert_driver(conn, drv)
        if driver_id is None:
            continue
        team_id = upsert_team(
            conn, season_id, r.get("Constructor", {}).get("name"), colors.get(code)
        )

        grid = _int_or_none(r.get("grid"))
        finish = _int_or_none(r.get("position"))
        if session_type == "Q":
            # Qualifying position is the grid slot; there is no race finish.
            grid, finish = finish, None
        fl_time, fl_num = fastest.get(code, (None, None))

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO timing_driversessionentry (
                    session_id, driver_id, team_id, grid_position, finish_position,
                    status, points, fastest_lap_time, fastest_lap_number,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (session_id, driver_id) DO UPDATE SET
                    team_id = EXCLUDED.team_id,
                    grid_position = EXCLUDED.grid_position,
                    finish_position = EXCLUDED.finish_position,
                    status = EXCLUDED.status,
                    points = EXCLUDED.points,
                    fastest_lap_time = EXCLUDED.fastest_lap_time,
                    fastest_lap_number = EXCLUDED.fastest_lap_number,
                    updated_at = NOW()
                """,
                (
                    session_key, driver_id, team_id, grid, finish,
                    map_status(r.get("positionText"), r.get("status")),
                    safe_float(r.get("points")),
                    fl_time, fl_num,
                ),
            )
        count += 1
    return count


def _int_or_none(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def ingest_pit_stops(conn, session, session_key: int) -> int:
    """Derive pit stops from lap PitIn/PitOut times.

    FastF1 marks the in-lap with PitInTime and the following out-lap with
    PitOutTime; duration is the pit-lane transit between them and compound_in is
    the tyre fitted on the out-lap. Rewritten idempotently per session.
    """
    laps = session.laps
    with conn.cursor() as cur:
        cur.execute("DELETE FROM timing_pitstop WHERE session_id = %s", (session_key,))

    if laps is None or laps.empty:
        return 0

    count = 0
    for code, grp in laps.groupby("Driver"):
        driver_id = resolve_driver_id(code)
        if driver_id is None:
            continue
        rows = grp.sort_values("LapNumber").to_dict("records")
        for i, lap in enumerate(rows):
            if pd.isna(lap.get("PitInTime")):
                continue
            duration = None
            compound_in = ""
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            if nxt is not None and not pd.isna(nxt.get("PitOutTime")):
                delta = nxt["PitOutTime"] - lap["PitInTime"]
                secs = delta.total_seconds() if hasattr(delta, "total_seconds") else None
                duration = round(secs, 3) if secs and secs > 0 else None
                compound_in = normalize_compound(nxt.get("Compound"))
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO timing_pitstop (session_id, driver_id, lap_number,
                        duration_seconds, compound_in, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (session_key, driver_id, int(lap["LapNumber"]), duration, compound_in),
                )
            count += 1
    return count


def ingest_session_laps(year: int, gp_name: str, session_type: str):
    """Load a session and persist Lap, DriverSessionEntry and PitStop rows."""
    session_key = resolve_session_key(year, gp_name, session_type)
    if session_key is None:
        raise ValueError(
            f"No session row for {year} {gp_name} {session_type}. "
            "Backfill seasons/grands prix first."
        )

    enable_cache()
    session = fastf1.get_session(year, gp_name, session_type)
    session.load(telemetry=False, weather=True, messages=False)  # fast path

    season_id = resolve_season_id(session_key)
    round_number = resolve_round_number(session_key)
    fastest = _fastest_laps_by_driver(session.laps)
    colors = _fastf1_team_colors(session)

    inserted = 0
    with get_connection() as conn:
        for _, lap in session.laps.iterrows():
            driver_id = resolve_driver_id(lap["Driver"])
            if driver_id is None:
                logger.warning("Unknown driver code %s — skipping lap", lap["Driver"])
                continue
            upsert_lap_row(conn, session_key, driver_id, lap)
            inserted += 1

        try:
            results = ingest_results(
                conn, session_key, season_id, fastest, colors,
                year, round_number, session_type,
            )
        except requests.RequestException as exc:
            logger.warning("Jolpica classification fetch failed: %s", exc)
            results = 0
        pits = ingest_pit_stops(conn, session, session_key)

        # Persist weather summary + mark loaded
        weather = _summarize_weather(session)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE seasons_session SET weather_summary = %s::jsonb, "
                "is_loaded = TRUE, updated_at = NOW() WHERE id = %s",
                (weather, session_key),
            )

    logger.info(
        "Ingested %d laps, %d results, %d pit stops for %s %s %s",
        inserted, results, pits, year, gp_name, session_type,
    )
    return {"session_id": session_key, "laps": inserted,
            "results": results, "pit_stops": pits}


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
