"""Race pace prediction from FP2/FP3 long-run analysis.

Lightweight, educational model (per PRD): find each driver's practice long runs
(representative race-simulation stints), fuel-correct the lap times to a common
load, aggregate per team, and rank teams into a predicted competitive order.

Pure ORM — no FastF1. Runs off already-ingested practice laps.
"""
import logging
import statistics

from celery import shared_task

from apps.seasons.models import GrandPrix, Session
from apps.timing.models import DriverSessionEntry, Lap

from .models import RacePacePrediction

logger = logging.getLogger(__name__)

# A long run must have at least this many valid green laps in one stint.
MIN_STINT_LAPS = 5
# Drop laps slower than this multiple of the stint's best (traffic/lift-and-coast).
OUTLIER_FACTOR = 1.07
# Approx fuel-burn benefit per lap (seconds). Used to normalize a stint's laps
# to a common fuel load so early (heavy) and late (light) laps are comparable.
FUEL_EFFECT_S_PER_LAP = 0.055


def _driver_team_map(gp: GrandPrix) -> dict[int, int]:
    """driver_id -> team_id, taken from the race entry list for this weekend."""
    race = gp.sessions.filter(session_type=Session.SessionType.R).first()
    if race is None:
        return {}
    return {
        e.driver_id: e.team_id
        for e in DriverSessionEntry.objects.filter(session=race, team__isnull=False)
    }


def _long_run_laps(gp: GrandPrix):
    """Green, non-pit practice laps grouped into (driver, session, stint)."""
    practice = gp.sessions.filter(
        session_type__in=[Session.SessionType.FP2, Session.SessionType.FP3]
    )
    laps = (
        Lap.objects.filter(
            session__in=practice,
            lap_time__isnull=False,
            pit_in=False,
            pit_out=False,
            track_status=Lap.TrackStatus.CLEAR,
        )
        .exclude(compound="")
        .order_by("driver_id", "session_id", "stint_number", "lap_number")
    )
    stints: dict[tuple, list] = {}
    for lap in laps:
        key = (lap.driver_id, lap.session_id, lap.stint_number)
        stints.setdefault(key, []).append(lap)
    return stints


def _fuel_corrected_seconds(stint_laps) -> list[float]:
    """Corrected lap seconds for one long-run stint, or [] if not a long run."""
    times = [l.lap_time.total_seconds() for l in stint_laps]
    if len(times) < MIN_STINT_LAPS:
        return []
    best = min(times)
    corrected = []
    for i, secs in enumerate(times):
        if secs > best * OUTLIER_FACTOR:
            continue  # traffic / out-of-shape lap
        # Normalize to the stint's heavy-fuel start by adding back the burn
        # benefit accrued by lap i.
        corrected.append(secs + FUEL_EFFECT_S_PER_LAP * i)
    return corrected if len(corrected) >= MIN_STINT_LAPS - 1 else []


def _actual_race_ranks(gp: GrandPrix) -> dict[int, int]:
    """team_id -> actual rank by best race finishing position (post-race)."""
    race = gp.sessions.filter(session_type=Session.SessionType.R).first()
    if race is None:
        return {}
    best: dict[int, int] = {}
    for e in DriverSessionEntry.objects.filter(
        session=race, team__isnull=False, finish_position__isnull=False
    ):
        cur = best.get(e.team_id)
        if cur is None or e.finish_position < cur:
            best[e.team_id] = e.finish_position
    ordered = sorted(best.items(), key=lambda kv: kv[1])
    return {team_id: rank for rank, (team_id, _) in enumerate(ordered, start=1)}


@shared_task
def compute_race_pace_prediction(gp_id: int):
    """Rank teams by fuel-corrected practice long-run pace for one Grand Prix."""
    gp = GrandPrix.objects.filter(pk=gp_id).first()
    if gp is None:
        return {"computed": False, "reason": "grand prix not found"}

    driver_team = _driver_team_map(gp)
    if not driver_team:
        return {"computed": False, "reason": "no race entries (need driver->team map)"}

    team_pace: dict[int, list[float]] = {}
    for (driver_id, _sid, _stint), stint_laps in _long_run_laps(gp).items():
        team_id = driver_team.get(driver_id)
        if team_id is None:
            continue
        team_pace.setdefault(team_id, []).extend(_fuel_corrected_seconds(stint_laps))

    team_avg = {t: statistics.mean(v) for t, v in team_pace.items() if v}
    if not team_avg:
        return {"computed": False, "reason": "no qualifying long runs in FP2/FP3"}

    actual = _actual_race_ranks(gp)
    ranked = sorted(team_avg.items(), key=lambda kv: kv[1])

    written = 0
    for rank, (team_id, avg_pace) in enumerate(ranked, start=1):
        RacePacePrediction.objects.update_or_create(
            grand_prix=gp,
            team_id=team_id,
            defaults={
                "predicted_pace_rank": rank,
                "avg_long_run_pace": round(avg_pace, 3),
                "actual_race_rank": actual.get(team_id),
            },
        )
        written += 1

    logger.info("Race pace prediction for %s: %d teams ranked", gp.name, written)
    return {"computed": True, "gp": gp.name, "teams_ranked": written}
