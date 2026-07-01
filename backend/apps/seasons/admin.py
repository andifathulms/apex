from django.contrib import admin

from .models import Driver, GrandPrix, Season, Session, Team


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("year", "race_count", "is_current")
    list_filter = ("is_current",)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("code", "full_name", "driver_number", "nationality")
    search_fields = ("code", "full_name", "external_driver_id")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "color_hex", "nationality")
    list_filter = ("season",)
    search_fields = ("name",)


@admin.register(GrandPrix)
class GrandPrixAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "round_number", "circuit_country", "date_start")
    list_filter = ("season",)
    search_fields = ("name", "official_name", "circuit_name")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("grand_prix", "session_type", "date", "is_loaded")
    list_filter = ("session_type", "is_loaded")
