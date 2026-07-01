from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("seasons", views.SeasonViewSet, basename="season")
router.register("races", views.GrandPrixViewSet, basename="race")
router.register("drivers", views.DriverViewSet, basename="driver")

# NOTE: explicit paths are declared BEFORE the router include so they take
# precedence over the router's generated detail routes (e.g. `drivers/compare/`
# must not be captured by the `drivers/<code>/` detail route, and the race
# weekend hub serves as the `races/<id>/` detail view).
urlpatterns = [
    # Standings
    path("seasons/<int:year>/standings/", views.SeasonStandingsView.as_view()),
    path("seasons/<int:year>/standings/progression/", views.SeasonStandingsProgressionView.as_view()),

    # Comparison tools
    path("compare/laps/", views.LapCompareView.as_view()),
    path("compare/telemetry/", views.TelemetryCompareView.as_view()),

    # Strategy
    path("strategy/<int:session_id>/", views.TireStrategyView.as_view()),
    path("strategy/<int:session_id>/pitstops/", views.PitStopComparisonView.as_view()),

    # Drivers
    path("drivers/compare/", views.DriverCompareView.as_view()),
    path("drivers/<str:code>/career/", views.DriverCareerView.as_view()),

    # Race weekend hub (serves as the races/<id>/ detail view)
    path("races/<int:gp_id>/", views.RaceWeekendHubView.as_view()),
    path("races/<int:gp_id>/sessions/<str:session_type>/results/", views.SessionResultsView.as_view()),
    path("races/<int:gp_id>/sessions/<str:session_type>/laps/", views.SessionLapsView.as_view()),

    # Predictions
    path("predictions/<int:gp_id>/", views.RacePacePredictionView.as_view()),

    # Router (list routes + season/driver detail)
    path("", include(router.urls)),
]
