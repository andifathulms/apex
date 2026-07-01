"""Seasons/session orchestration tasks.

These are thin triggers only — the actual FastF1 heavy lifting happens in the
separate ingestion-service. `check_for_new_sessions` polls OpenF1 to reconcile
external keys and decide *whether* to enqueue ingestion; it does not import
FastF1. Auto-triggered ingestion is sent to the ingestion worker by task name.
"""
import logging
from datetime import datetime, timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.seasons.models import GrandPrix, Session

logger = logging.getLogger(__name__)

# OpenF1 session_name -> our Session.session_type
_OPENF1_SESSION_TYPES = {
    "Practice 1": "FP1",
    "Practice 2": "FP2",
    "Practice 3": "FP3",
    "Qualifying": "Q",
    "Sprint Qualifying": "SQ",
    "Sprint Shootout": "SQ",
    "Sprint": "S",
    "Race": "R",
}


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _openf1_get(path: str, params: dict):
    resp = requests.get(f"{settings.OPENF1_BASE}/{path}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_current_meeting(year: int) -> dict | None:
    """The current/most-recent OpenF1 meeting (not in the future)."""
    meetings = _openf1_get("meetings", {"year": year})
    now = timezone.now()
    past = [
        m for m in meetings
        if (_parse_dt(m.get("date_start")) or now) <= now + timedelta(days=1)
    ]
    if not past:
        return None
    return max(past, key=lambda m: _parse_dt(m.get("date_start")) or now)


def _match_grand_prix(year: int, meeting: dict) -> GrandPrix | None:
    """Match an OpenF1 meeting to a GrandPrix by closest date (country names
    differ between sources, dates don't)."""
    meeting_date = _parse_dt(meeting.get("date_start"))
    candidates = GrandPrix.objects.filter(season__year=year)
    if meeting_date is None:
        return candidates.filter(
            circuit_country__iexact=meeting.get("country_name", "")
        ).first()

    best, best_gap = None, None
    for gp in candidates:
        if gp.date_start is None:
            continue
        gap = abs((gp.date_start - meeting_date.date()).days)
        if best_gap is None or gap < best_gap:
            best, best_gap = gp, gap
    # Only trust matches within a few days of the meeting start.
    return best if best_gap is not None and best_gap <= 5 else None


def _enqueue_ingestion(year: int, gp_name: str, session_type: str):
    """Send lap ingestion to the ingestion-service worker (by task name)."""
    from config.celery import app as celery_app

    celery_app.send_task(
        "ingest.ingest_session_data", args=[year, gp_name, session_type]
    )


@shared_task
def check_for_new_sessions(dry_run: bool = False):
    """Poll OpenF1 for the current meeting, reconcile keys, auto-trigger loads.

    Runs every 30 min (Celery beat). Scoped to the current meeting so it never
    fans out across the whole season. For each session that has ended and is not
    yet loaded, enqueue lap ingestion in the ingestion-service.
    """
    year = timezone.now().year
    try:
        meeting = get_current_meeting(year)
    except requests.RequestException as exc:
        logger.warning("OpenF1 poll failed: %s", exc)
        return {"checked": False, "reason": str(exc)}

    if not meeting:
        return {"checked": True, "meeting": None}

    gp = _match_grand_prix(year, meeting)
    if gp is None:
        return {"checked": True, "meeting": meeting.get("meeting_name"),
                "matched_gp": None}

    # Persist the OpenF1 meeting key on the Grand Prix.
    meeting_key = str(meeting.get("meeting_key", ""))
    if meeting_key and gp.external_meeting_key != meeting_key:
        gp.external_meeting_key = meeting_key
        gp.save(update_fields=["external_meeting_key", "updated_at"])

    try:
        openf1_sessions = _openf1_get("sessions", {"meeting_key": meeting.get("meeting_key")})
    except requests.RequestException as exc:
        logger.warning("OpenF1 sessions fetch failed: %s", exc)
        return {"checked": False, "reason": str(exc)}

    now = timezone.now()
    reconciled, triggered = 0, []
    for os in openf1_sessions:
        stype = _OPENF1_SESSION_TYPES.get(os.get("session_name"))
        if not stype:
            continue
        session = Session.objects.filter(grand_prix=gp, session_type=stype).first()
        if session is None:
            continue

        # Reconcile external key + session date.
        session_key = str(os.get("session_key", ""))
        changed = []
        if session_key and session.external_session_key != session_key:
            session.external_session_key = session_key
            changed.append("external_session_key")
        start = _parse_dt(os.get("date_start"))
        if start and session.date != start:
            session.date = start
            changed.append("date")
        if changed:
            session.save(update_fields=[*changed, "updated_at"])
            reconciled += 1

        # Auto-trigger lap ingestion for sessions that have ended.
        ended = (_parse_dt(os.get("date_end")) or now) < now
        if ended and not session.is_loaded:
            triggered.append({"session": stype, "id": session.id})
            if not dry_run:
                _enqueue_ingestion(year, gp.name, stype)

    logger.info(
        "OpenF1 reconcile: meeting=%s gp=%s reconciled=%d triggered=%d%s",
        meeting.get("meeting_name"), gp.name, reconciled, len(triggered),
        " (dry-run)" if dry_run else "",
    )
    return {
        "checked": True,
        "meeting": meeting.get("meeting_name"),
        "matched_gp": gp.name,
        "reconciled": reconciled,
        "triggered": triggered,
        "dry_run": dry_run,
    }
