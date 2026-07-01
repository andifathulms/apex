from django.contrib import admin

from .models import DriverSessionEntry, Lap, PitStop


@admin.register(DriverSessionEntry)
class DriverSessionEntryAdmin(admin.ModelAdmin):
    list_display = (
        "driver", "session", "team", "grid_position",
        "finish_position", "status", "points",
    )
    list_filter = ("status", "team")
    search_fields = ("driver__code",)


@admin.register(Lap)
class LapAdmin(admin.ModelAdmin):
    list_display = (
        "driver", "session", "lap_number", "lap_time",
        "compound", "stint_number", "track_status",
    )
    list_filter = ("compound", "track_status")
    search_fields = ("driver__code",)


@admin.register(PitStop)
class PitStopAdmin(admin.ModelAdmin):
    list_display = ("driver", "session", "lap_number", "duration_seconds", "compound_in")
    list_filter = ("compound_in",)
