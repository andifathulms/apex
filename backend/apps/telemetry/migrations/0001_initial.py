import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("timing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Telemetry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("distance", models.FloatField(help_text="Meters from lap start")),
                ("time_offset", models.FloatField(help_text="Seconds from lap start")),
                ("time_offset_ms", models.IntegerField(default=0, help_text="Milliseconds from lap start (hypertable partition key)")),
                ("speed_kmh", models.FloatField(blank=True, null=True)),
                ("throttle_pct", models.FloatField(blank=True, null=True)),
                ("brake", models.BooleanField(default=False)),
                ("gear", models.SmallIntegerField(blank=True, null=True)),
                ("rpm", models.FloatField(blank=True, null=True)),
                ("drs", models.BooleanField(default=False)),
                ("x_position", models.FloatField(blank=True, null=True)),
                ("y_position", models.FloatField(blank=True, null=True)),
                ("lap", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telemetry", to="timing.lap")),
            ],
            options={
                "verbose_name_plural": "Telemetry samples",
                "ordering": ["lap", "distance"],
            },
        ),
        migrations.AddIndex(
            model_name="telemetry",
            index=models.Index(fields=["lap", "distance"], name="telemetry_lap_distance_idx"),
        ),
        # --- TimescaleDB hypertable setup ---
        # A hypertable requires the partition column in every unique index, and
        # the dimension must be integer/timestamp/date (not double precision).
        # We partition on `time_offset_ms` (integer within-lap milliseconds) and
        # swap Django's default `id` PK for a composite (id, time_offset_ms) PK
        # so the partition column is covered. Chunk interval 60000 ms = 60s.
        # Queries are always scoped to a single lap_id (btree index below).
        migrations.RunSQL(
            sql=(
                "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE; "
                "ALTER TABLE telemetry_telemetry DROP CONSTRAINT telemetry_telemetry_pkey; "
                "ALTER TABLE telemetry_telemetry ADD PRIMARY KEY (id, time_offset_ms); "
                "SELECT create_hypertable('telemetry_telemetry', 'time_offset_ms', "
                "chunk_time_interval => 60000, if_not_exists => TRUE, migrate_data => TRUE); "
                "CREATE INDEX IF NOT EXISTS telemetry_lap_id_btree "
                "ON telemetry_telemetry (lap_id);"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS telemetry_lap_id_btree; "
                "ALTER TABLE telemetry_telemetry DROP CONSTRAINT telemetry_telemetry_pkey; "
                "ALTER TABLE telemetry_telemetry ADD PRIMARY KEY (id);"
            ),
        ),
    ]
