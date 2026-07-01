"""Raw psycopg2 connection layer for the shared Apex database.

Deliberately does NOT import Django. Uses the same DATABASE_URL as the backend.
"""
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://apex:password@db:5432/apex"
)


@contextmanager
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor(dict_rows: bool = False):
    with get_connection() as conn:
        factory = psycopg2.extras.RealDictCursor if dict_rows else None
        cur = conn.cursor(cursor_factory=factory)
        try:
            yield cur
        finally:
            cur.close()


# --- Resolution helpers -------------------------------------------------------

def resolve_session_key(year: int, gp_name: str, session_type: str) -> int | None:
    """Look up the internal seasons_session.id for a session."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT s.id
            FROM seasons_session s
            JOIN seasons_grandprix gp ON gp.id = s.grand_prix_id
            JOIN seasons_season se ON se.id = gp.season_id
            WHERE se.year = %s
              AND (gp.name ILIKE %s OR gp.official_name ILIKE %s)
              AND s.session_type = %s
            LIMIT 1
            """,
            (year, f"%{gp_name}%", f"%{gp_name}%", session_type),
        )
        row = cur.fetchone()
        return row[0] if row else None


def resolve_session_args(session_id: int) -> tuple[int, str, str] | None:
    """Reverse of resolve_session_key: (year, gp_name, session_type)."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT se.year, gp.name, s.session_type
            FROM seasons_session s
            JOIN seasons_grandprix gp ON gp.id = s.grand_prix_id
            JOIN seasons_season se ON se.id = gp.season_id
            WHERE s.id = %s
            """,
            (session_id,),
        )
        row = cur.fetchone()
        return (row[0], row[1], row[2]) if row else None


def resolve_season_id(session_id: int) -> int | None:
    """The seasons_season.id that a session belongs to."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT se.id
            FROM seasons_session s
            JOIN seasons_grandprix gp ON gp.id = s.grand_prix_id
            JOIN seasons_season se ON se.id = gp.season_id
            WHERE s.id = %s
            """,
            (session_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def list_sessions(year: int, session_types: tuple[str, ...] | None = None,
                  only_unloaded: bool = False) -> list[tuple]:
    """List (gp_name, session_type, is_loaded) for a season, for lap backfill."""
    clauses = ["se.year = %s"]
    params: list = [year]
    if session_types:
        clauses.append("s.session_type = ANY(%s)")
        params.append(list(session_types))
    if only_unloaded:
        clauses.append("s.is_loaded = FALSE")
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT gp.name, s.session_type, s.is_loaded
            FROM seasons_session s
            JOIN seasons_grandprix gp ON gp.id = s.grand_prix_id
            JOIN seasons_season se ON se.id = gp.season_id
            WHERE {' AND '.join(clauses)}
            ORDER BY gp.round_number, s.session_type
            """,
            params,
        )
        return [(r[0], r[1], r[2]) for r in cur.fetchall()]


def resolve_round_number(session_id: int) -> int | None:
    """The Grand Prix round number for a session (for Jolpica URLs)."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT gp.round_number
            FROM seasons_session s
            JOIN seasons_grandprix gp ON gp.id = s.grand_prix_id
            WHERE s.id = %s
            """,
            (session_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def resolve_driver_id(driver_code: str) -> int | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id FROM seasons_driver WHERE code = %s LIMIT 1",
            (driver_code,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def resolve_lap_id(session_id: int, driver_code: str, lap_number: int) -> int | None:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT l.id
            FROM timing_lap l
            JOIN seasons_driver d ON d.id = l.driver_id
            WHERE l.session_id = %s AND d.code = %s AND l.lap_number = %s
            LIMIT 1
            """,
            (session_id, driver_code, lap_number),
        )
        row = cur.fetchone()
        return row[0] if row else None
