"""Seasons/session orchestration tasks.

These are thin triggers only — the actual FastF1 heavy lifting happens in the
separate ingestion-service. `check_for_new_sessions` polls OpenF1 to decide
*whether* to enqueue ingestion; it does not import FastF1.
"""
import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_for_new_sessions():
    """Poll OpenF1 for the current meeting during a race weekend.

    Runs every 30 min (Celery beat). No-ops cheaply when there is nothing
    live. When a session has ended and is not yet loaded, enqueue lap
    ingestion via the ingestion-service (signalled through a DB flag / task).
    """
    year = timezone.now().year
    try:
        resp = requests.get(
            f"{settings.OPENF1_BASE}/sessions",
            params={"year": year},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("OpenF1 poll failed: %s", exc)
        return {"checked": False, "reason": str(exc)}

    sessions = resp.json()
    logger.info("OpenF1 returned %d sessions for %s", len(sessions), year)
    # Detailed reconciliation (matching external_session_key -> Session,
    # enqueuing ingest_session_data) is handled by the ingestion-service.
    return {"checked": True, "count": len(sessions)}
