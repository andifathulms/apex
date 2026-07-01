from django.db import models


class Telemetry(models.Model):
    """A single telemetry sample within a lap.

    Highest-volume table in the system (hundreds of rows per lap). Stored as a
    TimescaleDB hypertable partitioned on `time_offset` (within-lap seconds) —
    non-standard, but queries are always scoped to a single lap_id, so the
    btree index on lap_id is the primary filter. See CLAUDE.md.

    Telemetry is ingested on-demand only (never bulk for every lap).
    """

    lap = models.ForeignKey(
        "timing.Lap", on_delete=models.CASCADE, related_name="telemetry"
    )
    distance = models.FloatField(help_text="Meters from lap start")
    time_offset = models.FloatField(help_text="Seconds from lap start")
    # Integer millisecond mirror of time_offset. TimescaleDB hypertable
    # dimensions must be integer/timestamp/date (not double precision), so this
    # is the actual partition column — the within-lap time axis, as intended.
    time_offset_ms = models.IntegerField(
        default=0, help_text="Milliseconds from lap start (hypertable partition key)"
    )
    speed_kmh = models.FloatField(null=True, blank=True)
    throttle_pct = models.FloatField(null=True, blank=True)
    brake = models.BooleanField(default=False)
    gear = models.SmallIntegerField(null=True, blank=True)
    rpm = models.FloatField(null=True, blank=True)
    drs = models.BooleanField(default=False)
    x_position = models.FloatField(null=True, blank=True)
    y_position = models.FloatField(null=True, blank=True)

    class Meta:
        # No AutoField PK: TimescaleDB hypertables cannot enforce a PK that
        # doesn't include the partition column. Ordering/index on lap+distance.
        indexes = [
            models.Index(fields=["lap", "distance"]),
        ]
        ordering = ["lap", "distance"]
        verbose_name_plural = "Telemetry samples"

    def __str__(self):
        return f"tel lap={self.lap_id} d={self.distance:.0f}m v={self.speed_kmh}"
