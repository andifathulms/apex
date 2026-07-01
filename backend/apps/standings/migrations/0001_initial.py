import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("seasons", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SeasonStanding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("after_round", models.PositiveIntegerField()),
                ("points", models.FloatField(default=0)),
                ("position", models.PositiveIntegerField(blank=True, null=True)),
                ("driver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="standings", to="seasons.driver")),
                ("season", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="standings", to="seasons.season")),
                ("team", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="standings", to="seasons.team")),
            ],
            options={
                "ordering": ["season", "after_round", "position"],
            },
        ),
        migrations.AddIndex(
            model_name="seasonstanding",
            index=models.Index(fields=["season", "after_round"], name="standings_season_round_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="seasonstanding",
            unique_together={("season", "after_round", "driver")},
        ),
    ]
