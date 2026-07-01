"""Historical backfill from Jolpica-F1 (Ergast-compatible).

Populates seasons, grands prix, sessions, drivers and teams so that FastF1
lap-level ingestion has internal rows to attach to. Scope: 2018–present per the
PRD note that telemetry quality drops before 2018.
"""
import logging

import requests

from .db import get_connection

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


if __name__ == "__main__":
    # Manual invocation: python -m ingest.backfill
    backfill_all()
