"""Celery worker for the ingestion service.

Shares the same broker as the Django backend. Registers tasks under the SAME
dotted names the Django API enqueues (e.g. the on-demand telemetry trigger), so
this worker performs the heavy FastF1 work while the Django process never
imports FastF1.
"""
import logging
import os

from celery import Celery

from . import telemetry as telemetry_ingest
from . import sessions as session_ingest

logging.basicConfig(level=logging.INFO)

app = Celery("apex_ingestion")
app.conf.broker_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
app.conf.result_backend = os.environ.get("REDIS_URL", "redis://redis:6379/0")
app.conf.task_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_serializer = "json"
app.conf.timezone = "UTC"


@app.task(name="apps.telemetry.tasks.trigger_telemetry_ingestion")
def trigger_telemetry_ingestion(session_id: int, driver_code: str, lap_number: int):
    """Consume the on-demand telemetry trigger enqueued by the Django API."""
    from .db import resolve_session_args

    args = resolve_session_args(session_id)
    if not args:
        raise ValueError(f"Cannot resolve session {session_id}")
    year, gp_name, session_type = args
    return telemetry_ingest.ingest_lap_telemetry(
        year, gp_name, session_type, driver_code, lap_number
    )


@app.task(name="ingest.ingest_session_data")
def ingest_session_data(year: int, gp_name: str, session_type: str):
    """Lap-level ingestion for a session (triggered, not scheduled)."""
    return session_ingest.ingest_session_laps(year, gp_name, session_type)
