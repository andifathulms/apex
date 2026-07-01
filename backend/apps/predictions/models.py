from django.db import models

from apps.common import BaseModel


class RacePacePrediction(BaseModel):
    """Pre-race pace prediction from FP2/FP3 long-run analysis.

    `actual_race_rank` is backfilled after the race for accuracy tracking.
    """

    grand_prix = models.ForeignKey(
        "seasons.GrandPrix", on_delete=models.CASCADE, related_name="predictions"
    )
    team = models.ForeignKey(
        "seasons.Team", on_delete=models.CASCADE, related_name="predictions"
    )
    predicted_pace_rank = models.PositiveIntegerField()
    avg_long_run_pace = models.FloatField(
        help_text="Fuel-corrected mean long-run lap time (seconds)"
    )
    actual_race_rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["grand_prix", "predicted_pace_rank"]
        unique_together = ("grand_prix", "team")

    def __str__(self):
        return f"{self.grand_prix.name} — {self.team.name} #{self.predicted_pace_rank}"
