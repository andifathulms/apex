import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("seasons", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverSessionEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("grid_position", models.PositiveIntegerField(blank=True, null=True)),
                ("finish_position", models.PositiveIntegerField(blank=True, null=True)),
                ("status", models.CharField(choices=[("Finished", "Finished"), ("DNF", "Did Not Finish"), ("DSQ", "Disqualified"), ("DNS", "Did Not Start")], default="Finished", max_length=12)),
                ("points", models.FloatField(default=0)),
                ("fastest_lap_time", models.DurationField(blank=True, null=True)),
                ("fastest_lap_number", models.PositiveIntegerField(blank=True, null=True)),
                ("driver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="session_entries", to="seasons.driver")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="entries", to="seasons.session")),
                ("team", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="session_entries", to="seasons.team")),
            ],
            options={
                "verbose_name_plural": "Driver session entries",
                "ordering": ["session", "finish_position"],
                "unique_together": {("session", "driver")},
            },
        ),
        migrations.CreateModel(
            name="Lap",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lap_number", models.PositiveIntegerField()),
                ("lap_time", models.DurationField(blank=True, null=True)),
                ("sector1_time", models.DurationField(blank=True, null=True)),
                ("sector2_time", models.DurationField(blank=True, null=True)),
                ("sector3_time", models.DurationField(blank=True, null=True)),
                ("compound", models.CharField(blank=True, choices=[("SOFT", "Soft"), ("MEDIUM", "Medium"), ("HARD", "Hard"), ("INTERMEDIATE", "Intermediate"), ("WET", "Wet")], max_length=12)),
                ("tyre_life", models.PositiveIntegerField(blank=True, null=True)),
                ("stint_number", models.PositiveIntegerField(blank=True, null=True)),
                ("is_personal_best", models.BooleanField(default=False)),
                ("pit_in", models.BooleanField(default=False)),
                ("pit_out", models.BooleanField(default=False)),
                ("track_status", models.CharField(choices=[("clear", "Clear"), ("yellow", "Yellow flag"), ("sc", "Safety car"), ("vsc", "Virtual safety car"), ("red", "Red flag")], default="clear", max_length=8)),
                ("driver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="laps", to="seasons.driver")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="laps", to="seasons.session")),
            ],
            options={
                "ordering": ["session", "driver", "lap_number"],
            },
        ),
        migrations.CreateModel(
            name="PitStop",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lap_number", models.PositiveIntegerField()),
                ("duration_seconds", models.FloatField(blank=True, null=True)),
                ("compound_in", models.CharField(blank=True, choices=[("SOFT", "Soft"), ("MEDIUM", "Medium"), ("HARD", "Hard"), ("INTERMEDIATE", "Intermediate"), ("WET", "Wet")], max_length=12)),
                ("driver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pit_stops", to="seasons.driver")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pit_stops", to="seasons.session")),
            ],
            options={
                "ordering": ["session", "driver", "lap_number"],
            },
        ),
        migrations.AddIndex(
            model_name="lap",
            index=models.Index(fields=["session", "driver"], name="timing_lap_session_driver_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="lap",
            unique_together={("session", "driver", "lap_number")},
        ),
    ]
