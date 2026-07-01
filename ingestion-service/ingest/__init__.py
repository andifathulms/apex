"""Apex FastF1 ingestion service.

Standalone data pipeline — Python 3.10+, FastF1 only. Talks to the shared
PostgreSQL database directly via psycopg2 (NOT the Django ORM).
"""
import os

# Session type codes (see CLAUDE.md)
SESSION_TYPES = ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"]


def enable_cache():
    """Enable FastF1's on-disk cache (mandatory — sessions are 50-100MB and
    FastF1 re-downloads without it). Called lazily by the ingest entrypoints so
    importing this package doesn't require FastF1 to be installed (e.g. for unit
    tests of the pure helpers)."""
    import fastf1

    cache_dir = os.environ.get("FASTF1_CACHE_DIR", "/data/fastf1-cache")
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)
