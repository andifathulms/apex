"""Standings sync from Jolpica-F1 (Ergast-compatible schema)."""
import logging
import time

import requests
from celery import shared_task
from django.conf import settings

from apps.seasons.models import Driver, Season, Team

from .models import SeasonStanding

logger = logging.getLogger(__name__)

# Jolpica's unauthenticated limit is ~4 req/s (and a rolling hourly cap). Stay a
# little under it and back off on 429 so multi-season backfills don't get
# throttled midway.
JOLPICA_MIN_INTERVAL = 0.35


def jolpica_get(url: str, max_retries: int = 5) -> requests.Response:
    """GET with polite throttling + exponential backoff on HTTP 429."""
    delay = 2.0
    for _ in range(max_retries):
        resp = requests.get(url, timeout=20)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", delay))
            logger.warning("Jolpica 429 — backing off %.1fs (%s)", wait, url)
            time.sleep(wait)
            delay = min(delay * 2, 30)
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp


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
        resp = jolpica_get(url)
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


@shared_task
def sync_standings_progression(year: int):
    """Snapshot standings after every completed round (powers the progression
    chart), not just the final table."""
    final = sync_standings(year)  # also captures the latest round
    if not final.get("synced"):
        return final
    last_round = final["round"]

    rounds = 1
    for rnd in range(1, last_round):
        time.sleep(JOLPICA_MIN_INTERVAL)
        res = sync_standings(year, rnd)
        if res.get("synced"):
            rounds += 1
    logger.info("Standings progression for %s: %d rounds", year, rounds)
    return {"year": year, "rounds_captured": rounds, "last_round": last_round}


@shared_task
def sync_all_standings(start: int = 2018, end: int | None = None):
    """Full historical standings backfill (2018-present per PRD scope)."""
    import datetime

    end = end or datetime.date.today().year
    results = []
    for year in range(start, end + 1):
        results.append(sync_standings_progression(year))
    return results
