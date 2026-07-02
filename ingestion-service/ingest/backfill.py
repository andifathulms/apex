"""Historical backfill from Jolpica-F1 (Ergast-compatible).

Populates seasons, grands prix, sessions, drivers and teams so that FastF1
lap-level ingestion has internal rows to attach to. Scope: 2018–present per the
PRD note that telemetry quality drops before 2018.
"""
import logging

import requests

from .db import get_connection, list_sessions
from .sessions import ingest_session_laps

logger = logging.getLogger(__name__)

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"
EARLIEST_SEASON = 2018

# Sessions to create per weekend. Sprint sessions are added only when the
# schedule marks a sprint event (not modelled here in the scaffold).
DEFAULT_SESSIONS = ["FP1", "FP2", "FP3", "Q", "R"]


def _get(path: str) -> dict:
    resp = requests.get(f"{JOLPICA_BASE}/{path}", timeout=20)
    resp.raise_for_status()
    return resp.json()


def backfill_season(year: int):
    """Create Season + GrandPrix + Session rows for a year's schedule."""
    data = _get(f"{year}.json")
    races = data["MRData"]["RaceTable"]["Races"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO seasons_season (year, race_count, is_current,
                    created_at, updated_at)
                VALUES (%s, %s, FALSE, NOW(), NOW())
                ON CONFLICT (year) DO UPDATE SET race_count = EXCLUDED.race_count,
                    updated_at = NOW()
                RETURNING id
                """,
                (year, len(races)),
            )
            season_id = cur.fetchone()[0]

            for race in races:
                circuit = race.get("Circuit", {})
                location = circuit.get("Location", {})
                cur.execute(
                    """
                    INSERT INTO seasons_grandprix (season_id, round_number, name,
                        official_name, circuit_name, circuit_country,
                        circuit_location, date_start, date_end,
                        external_meeting_key, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, '', NOW(), NOW())
                    ON CONFLICT (season_id, round_number) DO UPDATE SET
                        name = EXCLUDED.name, updated_at = NOW()
                    RETURNING id
                    """,
                    (
                        season_id, int(race["round"]), race["raceName"],
                        race["raceName"], circuit.get("circuitName", ""),
                        location.get("country", ""), location.get("locality", ""),
                        race.get("date"), race.get("date"),
                    ),
                )
                gp_id = cur.fetchone()[0]
                for stype in DEFAULT_SESSIONS:
                    cur.execute(
                        """
                        INSERT INTO seasons_session (grand_prix_id, session_type,
                            external_session_key, weather_summary, is_loaded,
                            created_at, updated_at)
                        VALUES (%s, %s, '', '{}'::jsonb, FALSE, NOW(), NOW())
                        ON CONFLICT (grand_prix_id, session_type) DO NOTHING
                        """,
                        (gp_id, stype),
                    )

    logger.info("Backfilled %d races for %s", len(races), year)
    return {"year": year, "races": len(races)}


def backfill_all(start: int = EARLIEST_SEASON, end: int | None = None):
    import datetime

    end = end or datetime.date.today().year
    results = []
    for year in range(start, end + 1):
        try:
            results.append(backfill_season(year))
        except requests.RequestException as exc:
            logger.warning("Backfill failed for %s: %s", year, exc)
    return results


def backfill_laps(year: int, session_types: tuple[str, ...] = ("R",),
                  skip_loaded: bool = True, delay_seconds: float = 2.5):
    """Ingest lap-level data (no telemetry) for a season's sessions.

    Defaults to race sessions only. Pass e.g. ('FP2', 'FP3', 'Q', 'R') for a
    fuller backfill. Telemetry stays on-demand. Skips already-loaded sessions by
    default so this is safe to resume.

    `delay_seconds` throttles between sessions: hammering the FastF1 schedule/
    timing API too fast triggers a temporary block ("Failed to load any schedule
    data"), so we pace requests.
    """
    import time

    sessions = list_sessions(year, session_types, only_unloaded=skip_loaded)
    logger.info("Backfilling laps for %d sessions in %s", len(sessions), year)

    done, failed = 0, 0
    for gp_name, stype, _is_loaded in sessions:
        try:
            ingest_session_laps(year, gp_name, stype)
            done += 1
        except Exception as exc:  # a single missing session shouldn't halt the run
            failed += 1
            logger.warning("Lap ingest failed for %s %s %s: %s", year, gp_name, stype, exc)
        if delay_seconds:
            time.sleep(delay_seconds)
    return {"year": year, "ingested": done, "failed": failed, "total": len(sessions)}


def backfill_laps_all(start: int = EARLIEST_SEASON, end: int | None = None,
                      session_types: tuple[str, ...] = ("R",)):
    """Lap backfill across all seasons. This is the heavy, long-running job —
    a full multi-season telemetry-free lap load, run as a background task."""
    import datetime

    end = end or datetime.date.today().year
    return [backfill_laps(y, session_types) for y in range(start, end + 1)]


if __name__ == "__main__":
    # Manual invocation: python -m ingest.backfill  (schedule only)
    backfill_all()
