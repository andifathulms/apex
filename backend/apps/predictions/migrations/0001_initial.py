import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("seasons", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RacePacePrediction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("predicted_pace_rank", models.PositiveIntegerField()),
                ("avg_long_run_pace", models.FloatField(help_text="Fuel-corrected mean long-run lap time (seconds)")),
                ("actual_race_rank", models.PositiveIntegerField(blank=True, null=True)),
                ("grand_prix", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="predictions", to="seasons.grandprix")),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="predictions", to="seasons.team")),
            ],
            options={
                "ordering": ["grand_prix", "predicted_pace_rank"],
                "unique_together": {("grand_prix", "team")},
            },
        ),
    ]
