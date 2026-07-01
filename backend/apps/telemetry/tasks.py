"""Telemetry ingestion trigger.

The *real* implementation lives in the separate ingestion-service (it imports
FastF1, which is intentionally kept out of the Django image). Both processes
share the same Celery broker; the ingestion worker registers a task with this
same dotted name and does the heavy lifting. This Django-side definition is a
thin fallback/placeholder so `.delay()` can be called from API views and so the
name resolves during local eager execution.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="apps.telemetry.tasks.trigger_telemetry_ingestion")
def trigger_telemetry_ingestion(session_id: int, driver_code: str, lap_number: int):
    """Enqueue on-demand telemetry ingestion for one lap.

    Fulfilled by the ingestion-service worker. If this Django-side version runs
    (e.g. no ingestion worker is consuming the queue), it simply logs — it must
    NOT import FastF1.
    """
    logger.info(
        "Telemetry ingestion requested: session=%s driver=%s lap=%s "
        "(handled by ingestion-service)",
        session_id, driver_code, lap_number,
    )
    return {"queued": True, "session_id": session_id,
            "driver": driver_code, "lap": lap_number}
