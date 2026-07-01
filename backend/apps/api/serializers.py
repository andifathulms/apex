from rest_framework import serializers

from apps.predictions.models import RacePacePrediction
from apps.seasons.models import Driver, GrandPrix, Season, Session, Team
from apps.standings.models import SeasonStanding
from apps.timing.models import DriverSessionEntry, Lap, PitStop


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id", "driver_number", "code", "full_name",
            "nationality", "date_of_birth", "external_driver_id",
        ]


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "nationality", "color_hex"]


class SessionSerializer(serializers.ModelSerializer):
    session_type_display = serializers.CharField(
        source="get_session_type_display", read_only=True
    )

    class Meta:
        model = Session
        fields = [
            "id", "session_type", "session_type_display", "date",
            "external_session_key", "weather_summary", "is_loaded",
        ]


class GrandPrixSerializer(serializers.ModelSerializer):
    sessions = SessionSerializer(many=True, read_only=True)
    year = serializers.IntegerField(source="season.year", read_only=True)

    class Meta:
        model = GrandPrix
        fields = [
            "id", "year", "round_number", "name", "official_name",
            "circuit_name", "circuit_country", "circuit_location",
            "date_start", "date_end", "external_meeting_key", "sessions",
        ]


class GrandPrixListSerializer(serializers.ModelSerializer):
    """Lighter serializer without nested sessions, for list views."""

    year = serializers.IntegerField(source="season.year", read_only=True)

    class Meta:
        model = GrandPrix
        fields = [
            "id", "year", "round_number", "name", "official_name",
            "circuit_name", "circuit_country", "date_start", "date_end",
        ]


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["id", "year", "race_count", "is_current"]


class DriverSessionEntrySerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)
    team = TeamSerializer(read_only=True)

    class Meta:
        model = DriverSessionEntry
        fields = [
            "id", "driver", "team", "grid_position", "finish_position",
            "status", "points", "fastest_lap_time", "fastest_lap_number",
        ]


class LapSerializer(serializers.ModelSerializer):
    driver_code = serializers.CharField(source="driver.code", read_only=True)

    class Meta:
        model = Lap
        fields = [
            "id", "driver_code", "lap_number", "lap_time",
            "sector1_time", "sector2_time", "sector3_time",
            "compound", "tyre_life", "stint_number", "is_personal_best",
            "pit_in", "pit_out", "track_status",
        ]


class PitStopSerializer(serializers.ModelSerializer):
    driver_code = serializers.CharField(source="driver.code", read_only=True)

    class Meta:
        model = PitStop
        fields = ["id", "driver_code", "lap_number", "duration_seconds", "compound_in"]


class SeasonStandingSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)
    team = TeamSerializer(read_only=True)

    class Meta:
        model = SeasonStanding
        fields = ["id", "after_round", "driver", "team", "points", "position"]


class RacePacePredictionSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)

    class Meta:
        model = RacePacePrediction
        fields = [
            "id", "team", "predicted_pace_rank",
            "avg_long_run_pace", "actual_race_rank", "created_at",
        ]
