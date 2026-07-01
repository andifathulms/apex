"""On-demand telemetry ingestion (slow path).

Called only when a user requests a specific lap's telemetry via the API. Never
bulk-ingest telemetry for all laps — storage and load-time cost is too high for
data that may never be viewed. Results are cached in the Telemetry table so
repeat requests are instant.
"""
import logging

import fastf1
import pandas as pd
import psycopg2.extras

from .db import get_connection, resolve_lap_id
from .helpers import drs_is_active

logger = logging.getLogger(__name__)


def _already_cached(conn, lap_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM telemetry_telemetry WHERE lap_id = %s LIMIT 1",
            (lap_id,),
        )
        return cur.fetchone() is not None


def bulk_insert_telemetry(conn, lap_id: int, rows: list[dict]):
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO telemetry_telemetry (
                lap_id, distance, time_offset, time_offset_ms, speed_kmh,
                throttle_pct, brake, gear, rpm, drs, x_position, y_position
            ) VALUES %s
            """,
            [
                (
                    lap_id, r["distance"], r["time_offset"],
                    int(round(r["time_offset"] * 1000)), r["speed_kmh"],
                    r["throttle_pct"], r["brake"], r["gear"], r["rpm"],
                    r["drs"], r["x_position"], r["y_position"],
                )
                for r in rows
            ],
        )


def ingest_lap_telemetry(year: int, gp_name: str, session_type: str,
                         driver_code: str, lap_number: int):
    session = fastf1.get_session(year, gp_name, session_type)
    session.load(telemetry=True)

    lap = (
        session.laps.pick_drivers(driver_code)
        .pick_laps([lap_number])
        .iloc[0]
    )
    tel = lap.get_telemetry()  # Speed, Throttle, Brake, Gear, RPM, X, Y, Distance

    rows = [
        {
            "distance": float(row["Distance"]),
            "time_offset": row["Time"].total_seconds(),
            "speed_kmh": _f(row.get("Speed")),
            "throttle_pct": _f(row.get("Throttle")),
            "brake": bool(row.get("Brake")),
            "gear": _i(row.get("nGear")),
            "rpm": _f(row.get("RPM")),
            "drs": drs_is_active(row.get("DRS")),
            "x_position": _f(row.get("X")),
            "y_position": _f(row.get("Y")),
        }
        for _, row in tel.iterrows()
    ]

    with get_connection() as conn:
        lap_id = resolve_lap_id(
            _session_id(conn, year, gp_name, session_type),
            driver_code, lap_number,
        )
        if lap_id is None:
            raise ValueError(
                f"No lap row for {driver_code} L{lap_number} — ingest laps first."
            )
        if _already_cached(conn, lap_id):
            logger.info("Telemetry already cached for lap %s", lap_id)
            return {"lap_id": lap_id, "rows": 0, "cached": True}
        bulk_insert_telemetry(conn, lap_id, rows)

    logger.info("Ingested %d telemetry rows for lap %s", len(rows), lap_id)
    return {"lap_id": lap_id, "rows": len(rows), "cached": False}


def _session_id(conn, year, gp_name, session_type):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id FROM seasons_session s
            JOIN seasons_grandprix gp ON gp.id = s.grand_prix_id
            JOIN seasons_season se ON se.id = gp.season_id
            WHERE se.year = %s AND gp.name ILIKE %s AND s.session_type = %s
            LIMIT 1
            """,
            (year, f"%{gp_name}%", session_type),
        )
        row = cur.fetchone()
        return row[0] if row else None


def _f(value):
    if value is None or pd.isna(value):
        return None
    return float(value)


def _i(value):
    if value is None or pd.isna(value):
        return None
    return int(value)
