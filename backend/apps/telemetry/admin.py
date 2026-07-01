from django.contrib import admin

from .models import Telemetry


@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ("lap", "distance", "time_offset", "speed_kmh", "gear", "drs")
    list_filter = ("brake", "drs")
    # High-volume table — avoid loading all rows in the changelist by default
    show_full_result_count = False
