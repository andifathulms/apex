from django.db import models

from apps.common import BaseModel


class Compound(models.TextChoices):
    SOFT = "SOFT", "Soft"
    MEDIUM = "MEDIUM", "Medium"
    HARD = "HARD", "Hard"
    INTERMEDIATE = "INTERMEDIATE", "Intermediate"
    WET = "WET", "Wet"


class DriverSessionEntry(BaseModel):
    """A driver's result/summary for one session."""

    class Status(models.TextChoices):
        FINISHED = "Finished", "Finished"
        DNF = "DNF", "Did Not Finish"
        DSQ = "DSQ", "Disqualified"
        DNS = "DNS", "Did Not Start"

    session = models.ForeignKey(
        "seasons.Session", on_delete=models.CASCADE, related_name="entries"
    )
    driver = models.ForeignKey(
        "seasons.Driver", on_delete=models.CASCADE, related_name="session_entries"
    )
    team = models.ForeignKey(
        "seasons.Team", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="session_entries",
    )
    grid_position = models.PositiveIntegerField(null=True, blank=True)
    finish_position = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.FINISHED
    )
    points = models.FloatField(default=0)
    fastest_lap_time = models.DurationField(null=True, blank=True)
    fastest_lap_number = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["session", "finish_position"]
        unique_together = ("session", "driver")
        verbose_name_plural = "Driver session entries"

    def __str__(self):
        return f"{self.driver.code} @ {self.session}"


class Lap(BaseModel):
    class TrackStatus(models.TextChoices):
        CLEAR = "clear", "Clear"
        YELLOW = "yellow", "Yellow flag"
        SC = "sc", "Safety car"
        VSC = "vsc", "Virtual safety car"
        RED = "red", "Red flag"

    session = models.ForeignKey(
        "seasons.Session", on_delete=models.CASCADE, related_name="laps"
    )
    driver = models.ForeignKey(
        "seasons.Driver", on_delete=models.CASCADE, related_name="laps"
    )
    lap_number = models.PositiveIntegerField()
    lap_time = models.DurationField(null=True, blank=True)
    sector1_time = models.DurationField(null=True, blank=True)
    sector2_time = models.DurationField(null=True, blank=True)
    sector3_time = models.DurationField(null=True, blank=True)
    compound = models.CharField(
        max_length=12, choices=Compound.choices, blank=True
    )
    tyre_life = models.PositiveIntegerField(null=True, blank=True)
    stint_number = models.PositiveIntegerField(null=True, blank=True)
    is_personal_best = models.BooleanField(default=False)
    pit_in = models.BooleanField(default=False)
    pit_out = models.BooleanField(default=False)
    track_status = models.CharField(
        max_length=8, choices=TrackStatus.choices, default=TrackStatus.CLEAR
    )

    class Meta:
        ordering = ["session", "driver", "lap_number"]
        unique_together = ("session", "driver", "lap_number")
        indexes = [
            models.Index(fields=["session", "driver"]),
        ]

    def __str__(self):
        return f"{self.driver.code} L{self.lap_number} ({self.session})"


class PitStop(BaseModel):
    session = models.ForeignKey(
        "seasons.Session", on_delete=models.CASCADE, related_name="pit_stops"
    )
    driver = models.ForeignKey(
        "seasons.Driver", on_delete=models.CASCADE, related_name="pit_stops"
    )
    lap_number = models.PositiveIntegerField()
    duration_seconds = models.FloatField(null=True, blank=True)
    compound_in = models.CharField(
        max_length=12, choices=Compound.choices, blank=True
    )

    class Meta:
        ordering = ["session", "driver", "lap_number"]

    def __str__(self):
        return f"{self.driver.code} pit L{self.lap_number} ({self.duration_seconds}s)"
