"""Standings sync from Jolpica-F1 (Ergast-compatible schema)."""
import logging

import requests
from celery import shared_task
from django.conf import settings

from apps.seasons.models import Driver, Season, Team

from .models import SeasonStanding

logger = logging.getLogger(__name__)


@shared_task
def sync_standings(year: int, after_round: int | None = None):
    """Pull driver standings for a season and snapshot them.

    Response shape matches legacy Ergast — nested under MRData.StandingsTable.
    When `after_round` is given, snapshot standings as of that round.
    """
    base = settings.JOLPICA_BASE
    url = (
        f"{base}/{year}/{after_round}/driverStandings.json"
        if after_round
        else f"{base}/{year}/driverStandings.json"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Jolpica standings sync failed for %s: %s", year, exc)
        return {"synced": False, "reason": str(exc)}

    data = resp.json()
    lists = (
        data.get("MRData", {})
        .get("StandingsTable", {})
        .get("StandingsLists", [])
    )
    if not lists:
        return {"synced": False, "reason": "no standings lists"}

    standings_list = lists[0]
    rnd = int(standings_list.get("round", after_round or 0))
    season, _ = Season.objects.get_or_create(year=year)

    count = 0
    for row in standings_list.get("DriverStandings", []):
        d = row["Driver"]
        driver, _ = Driver.objects.get_or_create(
            external_driver_id=d.get("driverId", ""),
            defaults={
                "code": d.get("code", d.get("driverId", "")[:5].upper()),
                "full_name": f"{d.get('givenName', '')} {d.get('familyName', '')}".strip(),
                "nationality": d.get("nationality", ""),
            },
        )
        team = None
        constructors = row.get("Constructors", [])
        if constructors:
            team, _ = Team.objects.get_or_create(
                name=constructors[0].get("name", "Unknown"),
                season=season,
                defaults={"nationality": constructors[0].get("nationality", "")},
            )
        SeasonStanding.objects.update_or_create(
            season=season,
            after_round=rnd,
            driver=driver,
            defaults={
                "team": team,
                "points": float(row.get("points", 0)),
                "position": int(row.get("position", 0)) or None,
            },
        )
        count += 1

    logger.info("Synced %d standings rows for %s R%s", count, year, rnd)
    return {"synced": True, "count": count, "round": rnd}
