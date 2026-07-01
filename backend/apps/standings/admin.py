from django.contrib import admin

from .models import SeasonStanding


@admin.register(SeasonStanding)
class SeasonStandingAdmin(admin.ModelAdmin):
    list_display = ("season", "after_round", "position", "driver", "team", "points")
    list_filter = ("season", "after_round")
    search_fields = ("driver__code",)
