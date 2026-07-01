import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.predictions.models import RacePacePrediction
from apps.seasons.models import Driver, GrandPrix, Season, Session
from apps.standings.models import SeasonStanding
from apps.telemetry.models import Telemetry
from apps.telemetry.tasks import trigger_telemetry_ingestion
from apps.timing.models import DriverSessionEntry, Lap, PitStop

from .serializers import (
    DriverSerializer,
    DriverSessionEntrySerializer,
    GrandPrixListSerializer,
    GrandPrixSerializer,
    LapSerializer,
    PitStopSerializer,
    RacePacePredictionSerializer,
    SeasonSerializer,
    SeasonStandingSerializer,
)
from .services import build_comparison_payload, parse_telemetry_compare_params


# --- Standard read-only resource viewsets -------------------------------------

class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    lookup_field = "year"


class GrandPrixViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GrandPrix.objects.select_related("season").all()
    filterset_fields = ["season__year", "round_number"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return GrandPrixSerializer
        return GrandPrixListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related("sessions")
        return qs


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    lookup_field = "code"
    filterset_fields = ["nationality"]


# --- Season standings ---------------------------------------------------------

class SeasonStandingsView(APIView):
    """Latest driver standings for a season (highest round captured)."""

    def get(self, request, year):
        season = get_object_or_404(Season, year=year)
        latest = (
            SeasonStanding.objects.filter(season=season)
            .order_by("-after_round")
            .values_list("after_round", flat=True)
            .first()
        )
        rows = (
            SeasonStanding.objects.filter(season=season, after_round=latest)
            .select_related("driver", "team")
            .order_by("position")
            if latest is not None
            else SeasonStanding.objects.none()
        )
        return Response({
            "year": year,
            "after_round": latest,
            "standings": SeasonStandingSerializer(rows, many=True).data,
        })


class SeasonStandingsProgressionView(APIView):
    """Race-by-race points progression, shaped for a line chart."""

    def get(self, request, year):
        season = get_object_or_404(Season, year=year)
        rows = (
            SeasonStanding.objects.filter(season=season)
            .select_related("driver")
            .order_by("driver__code", "after_round")
        )
        series: dict[str, dict] = {}
        for row in rows:
            code = row.driver.code
            series.setdefault(code, {"driver": code, "points": []})
            series[code]["points"].append(
                {"round": row.after_round, "points": row.points, "position": row.position}
            )
        return Response({"year": year, "series": list(series.values())})


# --- Race weekend hub ---------------------------------------------------------

class RaceWeekendHubView(APIView):
    """Full weekend hub payload for one Grand Prix."""

    def get(self, request, gp_id):
        gp = get_object_or_404(
            GrandPrix.objects.select_related("season").prefetch_related("sessions"),
            pk=gp_id,
        )
        data = GrandPrixSerializer(gp).data
        # Attach fastest-lap callout per session
        callouts = []
        for session in gp.sessions.all():
            fastest = (
                Lap.objects.filter(session=session, lap_time__isnull=False)
                .select_related("driver")
                .order_by("lap_time")
                .first()
            )
            if fastest:
                callouts.append({
                    "session_type": session.session_type,
                    "driver_code": fastest.driver.code,
                    "lap_number": fastest.lap_number,
                    "lap_time": fastest.lap_time,
                })
        data["fastest_laps"] = callouts
        return Response(data)


class TrackLayoutView(APIView):
    """Circuit outline as an X/Y point list, taken from any telemetry lap already
    ingested for this Grand Prix (telemetry is on-demand, so this is populated
    once a user has opened the Telemetry Deep Dive for the weekend)."""

    def get(self, request, gp_id):
        gp = get_object_or_404(GrandPrix, pk=gp_id)
        lap_id = (
            Telemetry.objects.filter(
                lap__session__grand_prix=gp, x_position__isnull=False
            )
            .values_list("lap_id", flat=True)
            .first()
        )
        if lap_id is None:
            return Response({"gp_id": gp.id, "points": []})
        points = list(
            Telemetry.objects.filter(lap_id=lap_id)
            .order_by("distance")
            .values("x_position", "y_position", "speed_kmh")
        )
        return Response({"gp_id": gp.id, "lap_id": lap_id, "points": points})


class SeasonFormGuideView(APIView):
    """Rolling average finishing position over the last 5 races (per driver).

    Pulls the full season's finishing positions from Jolpica in one call so it
    works for every season without needing all races ingested locally.
    """

    def get(self, request, year):
        from apps.standings.tasks import jolpica_get

        # Jolpica caps results at 100 rows/page, so paginate to reach the latest
        # rounds (a naive single call would return only the first ~5 races).
        by_driver: dict[str, list] = {}
        offset, page_size, pages = 0, 100, 0
        try:
            while pages < 8:
                url = (
                    f"{settings.JOLPICA_BASE}/{year}/results.json"
                    f"?limit={page_size}&offset={offset}"
                )
                mr = jolpica_get(url).json().get("MRData", {})
                races = mr.get("RaceTable", {}).get("Races", [])
                if not races:
                    break
                for race in races:
                    rnd = int(race.get("round", 0))
                    for res in race.get("Results", []):
                        drv = res.get("Driver", {})
                        code = drv.get("code") or drv.get("driverId", "")[:3].upper()
                        try:
                            pos = int(res.get("position"))
                        except (TypeError, ValueError):
                            continue
                        by_driver.setdefault(code, []).append((rnd, pos))
                total = int(mr.get("total", 0))
                offset += page_size
                pages += 1
                if offset >= total:
                    break
        except requests.RequestException as exc:
            return Response({"year": year, "form": [], "error": str(exc)})

        form = []
        for code, rows in by_driver.items():
            rows.sort()
            last5 = [p for _, p in rows[-5:]]
            avg = round(sum(last5) / len(last5), 2) if last5 else None
            form.append({
                "driver": code,
                "last5": last5,
                "rolling_avg": avg,
                "races": len(rows),
            })
        form.sort(key=lambda f: f["rolling_avg"] if f["rolling_avg"] is not None else 99)
        return Response({"year": year, "form": form})


class SessionResultsView(APIView):
    def get(self, request, gp_id, session_type):
        session = get_object_or_404(
            Session, grand_prix_id=gp_id, session_type=session_type.upper()
        )
        entries = (
            DriverSessionEntry.objects.filter(session=session)
            .select_related("driver", "team")
            .order_by("finish_position")
        )
        return Response({
            "session_id": session.id,
            "session_type": session.session_type,
            "weather_summary": session.weather_summary,
            "results": DriverSessionEntrySerializer(entries, many=True).data,
        })


class SessionLapsView(APIView):
    def get(self, request, gp_id, session_type):
        session = get_object_or_404(
            Session, grand_prix_id=gp_id, session_type=session_type.upper()
        )
        laps = (
            Lap.objects.filter(session=session)
            .select_related("driver")
            .order_by("driver__code", "lap_number")
        )
        return Response({
            "session_id": session.id,
            "laps": LapSerializer(laps, many=True).data,
        })


# --- Comparison tools ---------------------------------------------------------

class LapCompareView(APIView):
    """Lap time + sector comparison for two (or more) drivers in a session."""

    def get(self, request):
        session_id = request.query_params.get("session")
        drivers = request.query_params.get("drivers", "")
        if not session_id or not drivers:
            raise ValidationError(
                "Both `session` and `drivers` (comma-separated codes) are required."
            )
        session = get_object_or_404(Session, pk=session_id)
        codes = [c.strip().upper() for c in drivers.split(",") if c.strip()]

        payload = []
        for code in codes:
            laps = (
                Lap.objects.filter(session=session, driver__code=code)
                .select_related("driver")
                .order_by("lap_number")
            )
            pits = PitStop.objects.filter(session=session, driver__code=code)
            payload.append({
                "driver_code": code,
                "laps": LapSerializer(laps, many=True).data,
                "pit_stops": PitStopSerializer(pits, many=True).data,
            })
        return Response({"session_id": session.id, "drivers": payload})


class TelemetryCompareView(APIView):
    """Two-driver telemetry comparison.

    Triggers on-demand ingestion (via the ingestion-service) when a requested
    lap's telemetry is not yet cached, returning 202 so the frontend can poll.
    """

    def get(self, request):
        params = parse_telemetry_compare_params(request)
        pending = []
        for code, lap_num in [
            (params.driver1, params.lap1),
            (params.driver2, params.lap2),
        ]:
            has_data = Telemetry.objects.filter(
                lap__session=params.session,
                lap__driver__code=code,
                lap__lap_number=lap_num,
            ).exists()
            if not has_data:
                trigger_telemetry_ingestion.delay(params.session.id, code, lap_num)
                pending.append({"driver": code, "lap": lap_num})

        if pending:
            return Response(
                {
                    "status": "ingesting",
                    "pending": pending,
                    "poll_after_seconds": 3,
                },
                status=202,
            )
        return Response(build_comparison_payload(params))


# --- Tire strategy ------------------------------------------------------------

class TireStrategyView(APIView):
    def get(self, request, session_id):
        session = get_object_or_404(Session, pk=session_id)
        laps = (
            Lap.objects.filter(session=session)
            .select_related("driver")
            .order_by("driver__code", "lap_number")
        )
        stints: dict[str, list] = {}
        for lap in laps:
            code = lap.driver.code
            driver_stints = stints.setdefault(code, [])
            if (
                driver_stints
                and driver_stints[-1]["stint_number"] == lap.stint_number
                and driver_stints[-1]["compound"] == lap.compound
            ):
                driver_stints[-1]["lap_end"] = lap.lap_number
                driver_stints[-1]["laps"] += 1
            else:
                driver_stints.append({
                    "stint_number": lap.stint_number,
                    "compound": lap.compound,
                    "lap_start": lap.lap_number,
                    "lap_end": lap.lap_number,
                    "laps": 1,
                })
        return Response({
            "session_id": session.id,
            "strategies": [
                {"driver_code": code, "stints": s} for code, s in stints.items()
            ],
        })


class PitStopComparisonView(APIView):
    def get(self, request, session_id):
        session = get_object_or_404(Session, pk=session_id)
        pits = (
            PitStop.objects.filter(session=session)
            .select_related("driver")
            .order_by("duration_seconds")
        )
        return Response({
            "session_id": session.id,
            "pit_stops": PitStopSerializer(pits, many=True).data,
        })


# --- Driver career / comparison ----------------------------------------------

class DriverCareerView(APIView):
    def get(self, request, code):
        driver = get_object_or_404(Driver, code=code.upper())
        entries = DriverSessionEntry.objects.filter(driver=driver)
        race_entries = entries.filter(session__session_type=Session.SessionType.R)
        total = race_entries.count()
        wins = race_entries.filter(finish_position=1).count()
        podiums = race_entries.filter(finish_position__lte=3).count()
        dnfs = race_entries.filter(status=DriverSessionEntry.Status.DNF).count()
        poles = entries.filter(
            session__session_type=Session.SessionType.Q, grid_position=1
        ).count()
        points = sum(e.points for e in race_entries)
        return Response({
            "driver": DriverSerializer(driver).data,
            "stats": {
                "races_entered": total,
                "wins": wins,
                "podiums": podiums,
                "dnfs": dnfs,
                "poles": poles,
                "total_points": points,
                "win_rate": round(wins / total, 4) if total else 0,
                "podium_rate": round(podiums / total, 4) if total else 0,
                "dnf_rate": round(dnfs / total, 4) if total else 0,
                "points_per_race": round(points / total, 3) if total else 0,
            },
        })


class DriverCompareView(APIView):
    def get(self, request):
        code_a = request.query_params.get("a")
        code_b = request.query_params.get("b")
        if not code_a or not code_b:
            raise ValidationError("Both `a` and `b` driver codes are required.")

        def career(driver):
            return DriverCareerView().get(request, driver.code).data

        driver_a = get_object_or_404(Driver, code=code_a.upper())
        driver_b = get_object_or_404(Driver, code=code_b.upper())
        return Response({"a": career(driver_a), "b": career(driver_b)})


# --- Predictions --------------------------------------------------------------

class RacePacePredictionView(APIView):
    def get(self, request, gp_id):
        gp = get_object_or_404(GrandPrix, pk=gp_id)
        preds = (
            RacePacePrediction.objects.filter(grand_prix=gp)
            .select_related("team")
            .order_by("predicted_pace_rank")
        )
        return Response({
            "gp_id": gp.id,
            "grand_prix": gp.name,
            "predictions": RacePacePredictionSerializer(preds, many=True).data,
        })
