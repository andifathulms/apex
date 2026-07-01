"""Celery application for Apex.

Note: the heavy FastF1 telemetry/lap ingestion runs in the *separate*
ingestion-service container. The tasks defined in Django apps here are thin
triggers / DB-side orchestration (standings sync, marking sessions, enqueueing
on-demand telemetry work). Keeping FastF1 out of the Django image is a
deliberate architecture decision (see CLAUDE.md).
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("apex")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Periodic schedule (see PRD "Ingestion Architecture")
app.conf.beat_schedule = {
    "check-for-new-sessions": {
        "task": "apps.seasons.tasks.check_for_new_sessions",
        # Every 30 minutes — the task itself no-ops outside race weekends
        "schedule": crontab(minute="*/30"),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
