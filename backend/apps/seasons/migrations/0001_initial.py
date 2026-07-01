import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Season",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("year", models.PositiveIntegerField(unique=True)),
                ("race_count", models.PositiveIntegerField(default=0)),
                ("is_current", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-year"]},
        ),
        migrations.CreateModel(
            name="Driver",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("driver_number", models.PositiveIntegerField(blank=True, null=True)),
                ("code", models.CharField(db_index=True, max_length=5)),
                ("full_name", models.CharField(max_length=120)),
                ("nationality", models.CharField(blank=True, max_length=60)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("external_driver_id", models.CharField(blank=True, db_index=True, max_length=80)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Team",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("nationality", models.CharField(blank=True, max_length=60)),
                ("color_hex", models.CharField(default="#FFFFFF", max_length=7)),
                ("season", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="teams", to="seasons.season")),
            ],
            options={"ordering": ["name"], "unique_together": {("name", "season")}},
        ),
        migrations.CreateModel(
            name="GrandPrix",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("round_number", models.PositiveIntegerField()),
                ("name", models.CharField(max_length=120)),
                ("official_name", models.CharField(blank=True, max_length=200)),
                ("circuit_name", models.CharField(blank=True, max_length=160)),
                ("circuit_country", models.CharField(blank=True, max_length=80)),
                ("circuit_location", models.CharField(blank=True, max_length=120)),
                ("date_start", models.DateField(blank=True, null=True)),
                ("date_end", models.DateField(blank=True, null=True)),
                ("external_meeting_key", models.CharField(blank=True, db_index=True, max_length=40)),
                ("season", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grands_prix", to="seasons.season")),
            ],
            options={
                "verbose_name_plural": "Grands Prix",
                "ordering": ["season__year", "round_number"],
                "unique_together": {("season", "round_number")},
            },
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session_type", models.CharField(choices=[("FP1", "Practice 1"), ("FP2", "Practice 2"), ("FP3", "Practice 3"), ("Q", "Qualifying"), ("SQ", "Sprint Qualifying"), ("S", "Sprint"), ("R", "Race")], max_length=3)),
                ("date", models.DateTimeField(blank=True, null=True)),
                ("external_session_key", models.CharField(blank=True, db_index=True, max_length=40)),
                ("weather_summary", models.JSONField(blank=True, default=dict)),
                ("is_loaded", models.BooleanField(default=False)),
                ("grand_prix", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to="seasons.grandprix")),
            ],
            options={
                "ordering": ["grand_prix", "date"],
                "unique_together": {("grand_prix", "session_type")},
            },
        ),
    ]
