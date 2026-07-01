from django.db import models

from apps.common import BaseModel


class SeasonStanding(BaseModel):
    """Race-by-race championship snapshot (cached from Jolpica-F1).

    One row per driver per completed round, capturing points and position
    *after* that round — this powers the points-progression chart.
    """

    season = models.ForeignKey(
        "seasons.Season", on_delete=models.CASCADE, related_name="standings"
    )
    after_round = models.PositiveIntegerField()
    driver = models.ForeignKey(
        "seasons.Driver", on_delete=models.CASCADE, related_name="standings"
    )
    team = models.ForeignKey(
        "seasons.Team", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="standings",
    )
    points = models.FloatField(default=0)
    position = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["season", "after_round", "position"]
        unique_together = ("season", "after_round", "driver")
        indexes = [
            models.Index(fields=["season", "after_round"]),
        ]

    def __str__(self):
        return f"{self.season.year} R{self.after_round} P{self.position} {self.driver.code}"
