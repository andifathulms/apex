from django.db import models

from apps.common import BaseModel


class Season(BaseModel):
    year = models.PositiveIntegerField(unique=True)
    race_count = models.PositiveIntegerField(default=0)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-year"]

    def __str__(self):
        return str(self.year)


class Driver(BaseModel):
    driver_number = models.PositiveIntegerField(null=True, blank=True)
    code = models.CharField(max_length=5, db_index=True)
    full_name = models.CharField(max_length=120)
    nationality = models.CharField(max_length=60, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    # Jolpica/Ergast driverRef (e.g. "max_verstappen")
    external_driver_id = models.CharField(max_length=80, blank=True, db_index=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.full_name}"


class Team(BaseModel):
    name = models.CharField(max_length=120)
    nationality = models.CharField(max_length=60, blank=True)
    color_hex = models.CharField(max_length=7, default="#FFFFFF")
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="teams"
    )

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "season")

    def __str__(self):
        return f"{self.name} ({self.season.year})"


class GrandPrix(BaseModel):
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="grands_prix"
    )
    round_number = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    official_name = models.CharField(max_length=200, blank=True)
    circuit_name = models.CharField(max_length=160, blank=True)
    circuit_country = models.CharField(max_length=80, blank=True)
    circuit_location = models.CharField(max_length=120, blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    # OpenF1 meeting_key
    external_meeting_key = models.CharField(max_length=40, blank=True, db_index=True)

    class Meta:
        ordering = ["season__year", "round_number"]
        unique_together = ("season", "round_number")
        verbose_name_plural = "Grands Prix"

    def __str__(self):
        return f"{self.season.year} R{self.round_number} — {self.name}"


class Session(BaseModel):
    class SessionType(models.TextChoices):
        FP1 = "FP1", "Practice 1"
        FP2 = "FP2", "Practice 2"
        FP3 = "FP3", "Practice 3"
        Q = "Q", "Qualifying"
        SQ = "SQ", "Sprint Qualifying"
        S = "S", "Sprint"
        R = "R", "Race"

    grand_prix = models.ForeignKey(
        GrandPrix, on_delete=models.CASCADE, related_name="sessions"
    )
    session_type = models.CharField(max_length=3, choices=SessionType.choices)
    date = models.DateTimeField(null=True, blank=True)
    # OpenF1 session_key
    external_session_key = models.CharField(max_length=40, blank=True, db_index=True)
    weather_summary = models.JSONField(default=dict, blank=True)
    # Has FastF1 lap-level data been ingested?
    is_loaded = models.BooleanField(default=False)

    class Meta:
        ordering = ["grand_prix", "date"]
        unique_together = ("grand_prix", "session_type")

    def __str__(self):
        return f"{self.grand_prix.name} — {self.session_type}"
