# CLAUDE.md — Apex (F1 Analytics Platform)

## What You Are Building

Apex is a fan-facing Formula 1 analytics platform. It ingests official F1 timing
and telemetry data via FastF1 (Python library), historical results via Jolpica-F1,
and near-real-time session data via OpenF1. The signature feature is the Telemetry
Deep Dive — synchronized speed/throttle/brake traces between two drivers overlaid
on a live track map.

Read PRD.md first. This file contains build conventions and exact build order.

---

## Critical Architecture Note: Two Python Environments

FastF1 requires **Python 3.10+** and is dependency-heavy (pandas, numpy). The
main Django app may use a different Python version. **Run FastF1 ingestion as
a fully separate service** with its own Dockerfile and requirements.txt. It
communicates with the main database directly via SQLAlchemy/psycopg2 — it does
NOT import Django models. Treat it as a standalone data pipeline, not a Django app.

```
apex/
├── backend/                  # Django app — Python 3.12, DRF, serves frontend
├── ingestion-service/        # Separate service — Python 3.10+, FastF1 only
│   ├── ingest/
│   │   ├── sessions.py       # session/lap ingestion
│   │   ├── telemetry.py      # on-demand telemetry ingestion
│   │   └── db.py             # raw psycopg2 connection to shared DB
│   ├── requirements.txt      # fastf1, pandas, psycopg2-binary
│   └── Dockerfile
├── frontend/                 # Next.js
├── docker-compose.yml
└── nginx/apex.conf
```

---

## Repository Structure (Django side)

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── celery.py
│   └── urls.py
├── apps/
│   ├── seasons/          # Season, GrandPrix, Session, Driver, Team models
│   ├── timing/           # Lap, PitStop, DriverSessionEntry models
│   ├── telemetry/        # Telemetry model (TimescaleDB hypertable)
│   ├── standings/        # SeasonStanding, sync from Jolpica-F1
│   ├── predictions/      # RacePacePrediction
│   └── api/               # All DRF viewsets
├── manage.py
└── requirements.txt
```

---

## Environment Variables

```env
# Django
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=
DATABASE_URL=postgresql://apex:password@db:5432/apex
REDIS_URL=redis://redis:6379/0

# No API keys needed — FastF1, OpenF1, and Jolpica-F1 are all open/free

# Ingestion service shares the same DATABASE_URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Django Conventions

- Django 5 + DRF 3.15+
- Split settings: `base.py`, `local.py`, `production.py`
- TimescaleDB hypertable required for `Telemetry` model — it is the
  highest-volume table in the system by far

### Base Model
```python
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

### Telemetry Hypertable Migration
```python
migrations.RunSQL(
    "SELECT create_hypertable('telemetry_telemetry', 'time_offset', "
    "if_not_exists => TRUE, migrate_data => TRUE);",
    reverse_sql="SELECT 1;"
)
```
Note: hypertable partitioning column here is `time_offset` (within-lap time),
not a calendar timestamp — this is non-standard TimescaleDB usage but appropriate
since queries are always scoped to a single lap_id anyway. Add a btree index on
`lap_id` as the primary filter.

---

## FastF1 Ingestion Service Conventions

### Setup
```python
# ingestion-service/ingest/__init__.py
import fastf1
import os

fastf1.Cache.enable_cache(os.environ.get('FASTF1_CACHE_DIR', '/data/fastf1-cache'))
```
**Cache is mandatory** — session data is 50-100MB and FastF1 re-downloads
without it. Mount a persistent volume for the cache directory in Docker.

### Session Identifiers
```python
SESSION_TYPES = ['FP1', 'FP2', 'FP3', 'Q', 'SQ', 'S', 'R']
# FP1/FP2/FP3 = practice, Q = qualifying, SQ = sprint qualifying,
# S = sprint, R = race
```

### Lap-Level Ingestion (fast, always done)
```python
def ingest_session_laps(year: int, gp_name: str, session_type: str):
    session = fastf1.get_session(year, gp_name, session_type)
    session.load(telemetry=False, weather=True, messages=False)  # fast path

    for _, lap in session.laps.iterrows():
        upsert_lap_row(
            session_key=resolve_session_key(year, gp_name, session_type),
            driver_code=lap['Driver'],
            lap_number=lap['LapNumber'],
            lap_time=lap['LapTime'],
            sector1=lap['Sector1Time'],
            sector2=lap['Sector2Time'],
            sector3=lap['Sector3Time'],
            compound=lap['Compound'],
            tyre_life=lap['TyreLife'],
            stint=lap['Stint'],
            pit_in=not pd.isna(lap['PitInTime']),
            pit_out=not pd.isna(lap['PitOutTime']),
            track_status=lap['TrackStatus'],
        )
```

### Telemetry Ingestion (slow, on-demand only)
```python
def ingest_lap_telemetry(year: int, gp_name: str, session_type: str,
                          driver_code: str, lap_number: int):
    """
    Called only when a user requests this specific lap's telemetry via API.
    Never bulk-ingest telemetry for all laps — storage and load time cost
    is too high for data that may never be viewed.
    """
    session = fastf1.get_session(year, gp_name, session_type)
    session.load(telemetry=True)

    lap = session.laps.pick_drivers(driver_code).pick_laps([lap_number]).iloc[0]
    tel = lap.get_telemetry()  # DataFrame: Speed, Throttle, Brake, Gear, RPM, X, Y, Distance

    rows = [
        {
            'distance': row['Distance'],
            'time_offset': row['Time'].total_seconds(),
            'speed_kmh': row['Speed'],
            'throttle_pct': row['Throttle'],
            'brake': bool(row['Brake']),
            'gear': row['nGear'],
            'rpm': row['RPM'],
            'drs': row['DRS'] in (10, 12, 14),  # FastF1 DRS value convention
            'x_position': row['X'],
            'y_position': row['Y'],
        }
        for _, row in tel.iterrows()
    ]
    bulk_insert_telemetry(lap_id=resolve_lap_id(...), rows=rows)
```

### DRS Value Interpretation
FastF1's DRS column uses numeric codes — values 10, 12, 14 indicate DRS is
active/open; other values indicate closed/unavailable. Always check against
this set, never treat DRS as a simple boolean from the raw value.

### Picking Methods Reference (FastF1 API surface Claude Code will use repeatedly)
```python
laps.pick_drivers('VER')           # filter by driver code
laps.pick_drivers(['VER', 'HAM'])  # multiple drivers
laps.pick_fastest()                 # fastest lap in a Laps object
laps.pick_quicklaps()               # exclude slow/outlier laps (in-laps, etc.)
laps.pick_laps([5, 6, 7])           # specific lap numbers
```

---

## OpenF1 Ingestion Conventions

Used for near-real-time polling during race weekends (checking if a session
has started/ended) before triggering the heavier FastF1 ingestion.

```python
OPENF1_BASE = "https://api.openf1.org/v1"

def get_current_meeting(year: int):
    resp = requests.get(f"{OPENF1_BASE}/meetings", params={"year": year})
    return resp.json()

def get_session_status(session_key: int):
    resp = requests.get(f"{OPENF1_BASE}/sessions", params={"session_key": session_key})
    return resp.json()
```
Note: do not rely on OpenF1 team radio data — coverage has dropped significantly
since 2026 and most events provide none. Do not build any feature with a hard
dependency on radio availability.

---

## Jolpica-F1 Ingestion Conventions

Replacement for the now-archived Ergast API. Same response schema as Ergast.

```python
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

def sync_season_standings(year: int):
    drivers = requests.get(f"{JOLPICA_BASE}/{year}/driverStandings.json").json()
    constructors = requests.get(f"{JOLPICA_BASE}/{year}/constructorStandings.json").json()
    # response shape matches legacy Ergast — nested under MRData.StandingsTable
```

Use Jolpica-F1 for: historical season data, official results when FastF1 data
is incomplete for older seasons, and standings progression.

---

## DRF Conventions

- All list endpoints: `PageNumberPagination`, page_size=20
- No authentication required (public read-only)
- Telemetry comparison endpoint must trigger ingestion task synchronously if
  data isn't cached yet, with a reasonable timeout — show a loading state on
  frontend rather than a hard error

```python
# apps/api/views.py
class TelemetryCompareView(APIView):
    def get(self, request):
        params = parse_telemetry_compare_params(request)
        for driver, lap_num in [(params.driver1, params.lap1), (params.driver2, params.lap2)]:
            if not Telemetry.objects.filter(
                lap__session=params.session, lap__driver__code=driver,
                lap__lap_number=lap_num
            ).exists():
                # Trigger ingestion, wait briefly, or return 202 + poll endpoint
                trigger_telemetry_ingestion.delay(params.session.id, driver, lap_num)
                return Response({"status": "ingesting"}, status=202)
        return Response(build_comparison_payload(params))
```

---

## Frontend Conventions

- Next.js 14 App Router, TypeScript
- D3.js for the Telemetry Deep Dive — this is the one page where raw D3 (not
  Recharts) is justified, due to the synchronized scrub interaction requirement
- Recharts for all standard charts (standings progression, lap time comparison)
- Tire compound colors must match official F1 convention exactly — see design tokens

### Tire Compound Token Mapping (mandatory, do not deviate)
```ts
// lib/constants.ts
export const TIRE_COLORS = {
  SOFT: '#FF3333',
  MEDIUM: '#FFD500',
  HARD: '#F5F5F5',
  INTERMEDIATE: '#43B02A',
  WET: '#0067B1',
} as const
```

### Telemetry Deep Dive — Synchronized Scrub Pattern
```tsx
// The core interaction: hovering the speed trace updates:
//   1. A vertical line on speed trace
//   2. A vertical line on throttle/brake trace (same x position)
//   3. A marker position on the track map (same distance value)
//   4. A readout panel showing both drivers' values at that point
// All four must update on the SAME mouse event — use a shared hover state
// lifted to the parent TelemetryDeepDive component, passed down to children.

const [scrubDistance, setScrubDistance] = useState<number | null>(null)
// Pass scrubDistance + setScrubDistance to SpeedTrace, ThrottleBrakeTrace, TrackMap
```

### Component Naming
```
components/
├── race/
│   ├── RaceWeekendHub.tsx
│   ├── SessionResultsTable.tsx
│   └── TrackLayoutMap.tsx
├── compare/
│   ├── LapTimeComparison.tsx
│   ├── SectorDeltaChart.tsx
│   └── CumulativeGapChart.tsx
├── strategy/
│   ├── TireStrategyVisualizer.tsx
│   ├── StintBar.tsx
│   ├── DegradationCurve.tsx
│   └── PitStopComparison.tsx
├── telemetry/
│   ├── TelemetryDeepDive.tsx      # parent, owns scrub state
│   ├── SpeedTrace.tsx              # D3
│   ├── ThrottleBrakeTrace.tsx      # D3
│   ├── TrackMap.tsx                # D3, color-coded by speed
│   └── DeltaTimeTrace.tsx          # D3
├── standings/
│   ├── PointsProgressionChart.tsx
│   ├── StandingsTable.tsx
│   └── FormGuide.tsx
├── drivers/
│   ├── DriverCareerStats.tsx
│   └── DriverCompareTool.tsx
└── ui/
    ├── TireCompoundBadge.tsx
    ├── LapTimeDisplay.tsx          # DM Mono formatted M:SS.mmm
    └── TeamColorBar.tsx
```

---

## Docker Compose (Local)

```yaml
services:
  db:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: apex
      POSTGRES_USER: apex
      POSTGRES_PASSWORD: password
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes: ["./backend:/app"]
    env_file: .env
    depends_on: [db, redis]
    ports: ["8000:8000"]

  celery:
    build: ./backend
    command: celery -A config worker -l info
    volumes: ["./backend:/app"]
    env_file: .env
    depends_on: [db, redis]

  celery-beat:
    build: ./backend
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file: .env
    depends_on: [db, redis]

  ingestion-service:
    build: ./ingestion-service
    volumes:
      - ./ingestion-service:/app
      - fastf1-cache:/data/fastf1-cache
    env_file: .env
    depends_on: [db]

  frontend:
    build: ./frontend
    command: npm run dev
    volumes: ["./frontend:/app"]
    env_file: .env
    ports: ["3000:3000"]

volumes:
  pgdata:
  fastf1-cache:
```

---

## Build Order

### Step 1 — Django Foundation
1. Scaffold Django with split settings, TimescaleDB extension enabled
2. Create all apps and models
3. Migrations including Telemetry hypertable
4. Admin registration for all models
5. Verify migrate runs clean

### Step 2 — Ingestion Service Scaffold
1. Create separate `ingestion-service/` with Python 3.10+ Dockerfile
2. Install FastF1, configure cache directory with persistent volume
3. Write raw DB connection layer (psycopg2, not Django ORM)
4. Test: `fastf1.get_session(2024, 'Monaco', 'R')` loads successfully in container

### Step 3 — Historical Backfill
1. Jolpica-F1 sync: seasons, drivers, teams, standings (2018–present, per
   PRD's "telemetry quality drops before 2018" note)
2. FastF1 lap-level ingestion (no telemetry) for all sessions, 2018–present
3. Verify: `Lap.objects.count()` reflects realistic volume (~50k+ rows)

### Step 4 — Race Weekend Hub + Comparison Tools
1. Build session results, weekend hub endpoint
2. Build Lap Time Comparison endpoint
3. Build Tire Strategy endpoint
4. Frontend: Race Weekend Hub page, Comparison tool, Strategy visualizer

### Step 5 — Telemetry Deep Dive (signature feature — budget the most time)
1. On-demand telemetry ingestion task with 202-then-poll pattern
2. Telemetry comparison endpoint
3. Build D3 SpeedTrace + ThrottleBrakeTrace + TrackMap with synchronized scrub
4. Build DeltaTimeTrace calculation (cumulative time difference along track distance)

### Step 6 — Standings, History, Predictions
1. Points progression endpoint + chart
2. Driver career stats + comparison tool
3. Race pace prediction model (FP2/FP3 long-run analysis)

### Step 7 — Live Polling + Polish
1. OpenF1 polling for session status during race weekends
2. Auto-trigger lap ingestion when a session completes
3. Mobile responsive pass (simplify Telemetry Deep Dive for small screens)
4. Add "unofficial fan project" disclaimer per FastF1 terms

---

## Key Decisions (Do Not Change)

- **FastF1 ingestion runs in a separate service**, never inside the Django process directly
- **Telemetry is on-demand only** — never bulk-ingest every lap's telemetry
- **TimescaleDB hypertable required** for Telemetry table
- **Tire compound colors follow official F1 convention** — do not redesign this palette
- **No official F1 branding/logos** — fan project disclaimer required, team colors only
- **Pre-2018 seasons out of scope for telemetry features** — data quality insufficient
- **Do not build features dependent on team radio data** — coverage unreliable since 2026

---

## Definition of Done (Phase 1–3)

- [ ] Ingestion service successfully loads a real FastF1 session in its container
- [ ] Jolpica-F1 sync populates seasons/drivers/standings 2018–present
- [ ] Lap-level data ingested for at least one full season
- [ ] `/api/races/{gp_id}/` returns full weekend hub data
- [ ] `/api/compare/laps/` returns valid two-driver comparison
- [ ] On-demand telemetry ingestion works end-to-end (202 → poll → 200 with data)
- [ ] Telemetry Deep Dive renders with working synchronized scrub across all
      four visual elements (speed, throttle/brake, map, delta)
- [ ] `docker-compose up` brings up all 6 services cleanly from fresh clone
