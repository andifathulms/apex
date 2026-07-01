from django.contrib import admin

from .models import RacePacePrediction


@admin.register(RacePacePrediction)
class RacePacePredictionAdmin(admin.ModelAdmin):
    list_display = (
        "grand_prix", "team", "predicted_pace_rank",
        "avg_long_run_pace", "actual_race_rank",
    )
    list_filter = ("grand_prix",)
