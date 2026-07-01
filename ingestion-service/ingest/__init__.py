"""Apex FastF1 ingestion service.

Standalone data pipeline — Python 3.10+, FastF1 only. Talks to the shared
PostgreSQL database directly via psycopg2 (NOT the Django ORM).
"""
import os

import fastf1

# Cache is mandatory — session data is 50-100MB and FastF1 re-downloads
# without it. A persistent volume is mounted at FASTF1_CACHE_DIR in Docker.
_CACHE_DIR = os.environ.get("FASTF1_CACHE_DIR", "/data/fastf1-cache")
os.makedirs(_CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(_CACHE_DIR)

# Session type codes (see CLAUDE.md)
SESSION_TYPES = ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"]
