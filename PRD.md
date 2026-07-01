# PRD — Apex (F1 Analytics Platform)

> A fan-facing Formula 1 analytics platform built on official F1 timing data.
> Turns millisecond-level telemetry into visual stories — lap comparisons, tire
> strategy breakdowns, and corner-by-corner speed traces that broadcast graphics
> never show you.

---

## Vision

F1 broadcasts show you the result. Apex shows you *why*. Using the same timing
and telemetry data the teams themselves see, this platform lets fans explore
race weekends at a depth normally reserved for strategists — lap-by-lap pace,
tire degradation curves, and side-by-side speed traces through any corner.

---

## Target Users

| User | Need |
|---|---|
| F1 fans (casual to hardcore) | Deeper understanding of what happened and why |
| Fantasy F1 players | Pace and strategy data to inform picks |
| Content creators | Shareable visual clips (telemetry overlays, tire charts) |
| Strategy/data enthusiasts | Raw exploration tools, comparison features |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Data Processing | FastF1 (Python) + pandas |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 16 + TimescaleDB (telemetry is heavily time-series) |
| Frontend | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| Charts | Recharts (standard charts) + D3.js (telemetry traces, track maps) |
| Container | Docker + Docker Compose |
| Deployment | GCP VM + Nginx |

---

## Data Sources

### Primary — FastF1 (Python library)
Open-source wrapper around F1's official live timing API. Free, no key required.
Gives access to F1 lap timing, car telemetry and position, tyre data, weather data, the event schedule and session results.

```python
import fastf1
fastf1.Cache.enable_cache('cache/')   # mandatory — sessions are 50-100MB

session = fastf1.get_session(2025, 'Monaco', 'R')
session.load(telemetry=True, weather=True, messages=True)

laps = session.laps
driver_laps = laps.pick_drivers('VER')
fastest = driver_laps.pick_fastest()
telemetry = fastest.get_telemetry()   # Speed, Throttle, Brake, Gear, RPM, X, Y, DRS
```
**Requires Python 3.10+.** Run FastF1 ingestion as a separate worker/service from
the main Django app if Django environment uses a different Python version.

### Secondary — OpenF1 API
Free REST API, live + historical timing data, useful for near-real-time data
during race weekends without needing to wait for FastF1's session file availability.

```
GET https://api.openf1.org/v1/meetings?year=2026
GET https://api.openf1.org/v1/sessions?year=2026&country_name=Singapore
GET https://api.openf1.org/v1/laps?session_key=latest&driver_number=1
GET https://api.openf1.org/v1/car_data?driver_number=1&session_key=latest
```
Note: team radio coverage has decreased significantly starting in 2026, with most events providing no radio data — do not depend on radio data for core features.

### Tertiary — Jolpica-F1
FastF1 calculates preliminary race and sprint results from timing data when no official results data is available from Jolpica-F1 — Jolpica-F1 is the modern community-run successor to the now-archived Ergast API, used for historical results, standings, and season schema back to 1950.

```
GET https://api.jolpi.ca/ergast/f1/2024/drivers.json
GET https://api.jolpi.ca/ergast/f1/2024/constructorStandings.json
GET https://api.jolpi.ca/ergast/f1/2024/5/results.json   # round 5 results
```

---

## Core Features

### 1. Race Weekend Hub
Landing page for each Grand Prix. All sessions (FP1/FP2/FP3, Qualifying, Sprint
if applicable, Race) in one view.

**Components:**
- Session selector tabs
- Results table per session (position, driver, time/gap, tire compound used)
- Weather summary (air temp, track temp, conditions) for the session
- Track layout map (from FastF1 position data, rendered as SVG path)
- Fastest lap callout

### 2. Lap Time Comparison Tool
Pick any two drivers in the same session — overlay lap times and sector deltas.

**Components:**
- Line chart: lap time per lap, both drivers overlaid
- Sector delta bar chart: where did each driver gain/lose time (S1/S2/S3)
- Cumulative gap chart: running time difference over the race distance
- Pit stop markers overlaid on the lap time chart

### 3. Tire Strategy Visualizer
Full strategy breakdown for a race — every driver's stint history.

**Components:**
- Horizontal stint bar per driver: compound (color-coded: soft=red, medium=yellow,
  hard=white, intermediate=green, wet=blue), stint length, lap range
- Tire degradation curve: lap time trend within each stint (shows wear pattern)
- Pit stop duration comparison (who had the fastest stops)
- "What if" stint length comparator (educational — show how 2-stop vs 3-stop
  strategies played out for similar drivers)

### 4. Telemetry Deep Dive
The signature feature. Pick a specific lap (or fastest lap) for two drivers,
overlay their full telemetry trace through the lap.

**Components:**
- Speed trace: both drivers' speed (km/h) plotted against track distance
- Throttle/brake trace: stacked below speed, shows braking points and throttle
  application
- Gear shift markers
- Mini-map: track outline with color-coded speed (using X/Y position data),
  click any point on the map to jump to that point in the telemetry trace
- Delta time trace: cumulative time gained/lost at every point on track —
  this is the "where exactly did they gain time" visualization

### 5. Season Standings & Trends
Not just final standings — the story of the season.

**Components:**
- Points progression chart: cumulative points per driver, race by race
- Position change visualization: who gained/lost championship position when
- Constructor standings with the same race-by-race breakdown
- "Form guide": rolling average finishing position, last 5 races

### 6. Historical Driver/Team Comparison
Compare any two drivers across different eras using normalized stats.

**Components:**
- Win rate, podium rate, pole position rate, DNF rate (career or season-bound)
- Average qualifying position vs average race finish (overtaking tendency proxy)
- Points per race entered
- Head-to-head: when both drivers were teammates or same-era rivals, direct
  qualifying/race comparison

### 7. Predicted Race Pace Model
Lightweight prediction using FP2/FP3 long-run data (race-simulation stints).

**Components:**
- Estimated race pace per team based on long-run average lap time during
  practice, fuel-corrected
- Simple ranking: "predicted competitive order" before the race, shown as
  a pre-race card, evaluated post-race for accuracy tracking

---

## Database Models

### Season
```
id, year, race_count, is_current
```

### GrandPrix
```
id, season FK, round_number, name, official_name,
circuit_name, circuit_country, circuit_location,
date_start, date_end, external_meeting_key (OpenF1 meeting_key)
```

### Session
```
id, grand_prix FK,
session_type (FP1 | FP2 | FP3 | Q | SQ | S | R),
date, external_session_key (OpenF1 session_key),
weather_summary (JSONField),
is_loaded (bool — has FastF1 data been ingested)
```

### Driver
```
id, driver_number, code (e.g. 'VER'), full_name,
nationality, date_of_birth, external_driver_id (Jolpica driver ref)
```

### Team
```
id, name, nationality, color_hex, season FK
```

### DriverSessionEntry
```
id, session FK, driver FK, team FK,
grid_position, finish_position, status (Finished | DNF | DSQ | etc.),
points, fastest_lap_time, fastest_lap_number
```

### Lap
```
id, session FK, driver FK,
lap_number, lap_time (duration), sector1_time, sector2_time, sector3_time,
compound (SOFT | MEDIUM | HARD | INTERMEDIATE | WET),
tyre_life (int — laps on this set), stint_number,
is_personal_best (bool), pit_in (bool), pit_out (bool),
track_status (clear | yellow | sc | vsc | red)
```

### Telemetry
```
id, lap FK,
distance (float, meters from lap start),
time_offset (float, seconds from lap start),
speed_kmh, throttle_pct, brake (bool), gear, rpm, drs (bool),
x_position, y_position
```
*Stored as TimescaleDB hypertable on a synthetic time axis — telemetry rows
are numerous (hundreds per lap), only ingest for laps users actually request
(fastest lap, or explicitly compared laps) rather than every lap of every driver.*

### PitStop
```
id, session FK, driver FK,
lap_number, duration_seconds, compound_in
```

### SeasonStanding (cached, race-by-race snapshot)
```
id, season FK, after_round,
driver FK, team FK, points, position
```

### RacePacePrediction
```
id, grand_prix FK, team FK,
predicted_pace_rank (int), avg_long_run_pace (float, fuel-corrected),
created_at, actual_race_rank (int, nullable, filled post-race)
```

---

## Ingestion Architecture

### FastF1 Ingestion Service
Because FastF1 requires Python 3.10+ and is dependency-heavy (pandas-based),
run it as a **separate Celery worker/service** with its own requirements.txt,
communicating with the main Django app via the shared PostgreSQL database
(not via Django ORM directly — use raw psycopg2 or a thin internal API).

```
Celery Beat Schedule:
  - check_for_new_sessions: every 30 min during a race weekend (Thu-Sun)
      → poll OpenF1 /sessions endpoint for the current meeting
      → if a session has ended and is_loaded=False → trigger ingestion

  - ingest_session_data(session_id): triggered, not scheduled
      → fastf1.get_session(year, gp_name, session_type)
      → session.load(telemetry=False)   # laps/results only — fast
      → store Lap, DriverSessionEntry, PitStop rows
      → mark session.is_loaded = True

  - ingest_telemetry_on_demand(lap_id): triggered by user request via API
      → only called when a user actually opens the Telemetry Deep Dive
        for a specific lap — NOT bulk-ingested for every lap
      → cache result in Telemetry table so repeat requests are instant

  - sync_standings: after each race session completes
      → pull Jolpica-F1 standings, store SeasonStanding snapshot

  - compute_race_pace_prediction: after FP2 of each weekend
      → analyze long-run stints from FP2/FP3, fuel-correct, rank teams
```

### Why On-Demand Telemetry Ingestion
Full telemetry for every lap of every driver in a race is enormous (a single
session can be 50-100MB raw). Ingesting only when requested keeps storage
sane while still delivering instant results on repeat views via caching.

```python
@shared_task
def ingest_telemetry_on_demand(session_id: int, driver_code: str, lap_number: int):
    cache_key = f"telemetry:{session_id}:{driver_code}:{lap_number}"
    if Telemetry.objects.filter(lap__session_id=session_id,
                                  lap__driver__code=driver_code,
                                  lap__lap_number=lap_number).exists():
        return  # already cached

    session = fastf1.get_session(*resolve_session_args(session_id))
    session.load(telemetry=True)
    lap = session.laps.pick_drivers(driver_code).pick_laps([lap_number]).iloc[0]
    tel = lap.get_telemetry()
    bulk_create_telemetry_rows(lap_id=..., dataframe=tel)
```

---

## DRF API Endpoints

```
GET /api/seasons/{year}/                       → season overview
GET /api/seasons/{year}/standings/              → driver + constructor standings
GET /api/seasons/{year}/standings/progression/  → race-by-race points chart data

GET /api/races/{gp_id}/                         → weekend hub data
GET /api/races/{gp_id}/sessions/{type}/results/ → session results
GET /api/races/{gp_id}/sessions/{type}/laps/    → all lap data for session

GET /api/compare/laps/?session={}&drivers={}    → lap time + sector comparison
GET /api/compare/telemetry/?session={}&driver1={}&lap1={}&driver2={}&lap2={}
                                                 → triggers on-demand ingestion if needed

GET /api/strategy/{session_id}/                 → full tire strategy breakdown
GET /api/strategy/{session_id}/pitstops/        → pit stop comparison

GET /api/drivers/{code}/career/                 → historical career stats
GET /api/drivers/compare/?a={code}&b={code}     → cross-era comparison

GET /api/predictions/{gp_id}/                   → race pace prediction
```

---

## Frontend Pages (Next.js App Router)

```
/                              → Home: current/latest weekend hub, season standings snippet
/race/[year]/[round]           → Race Weekend Hub
/race/[year]/[round]/compare   → Lap Time Comparison Tool
/race/[year]/[round]/telemetry → Telemetry Deep Dive
/race/[year]/[round]/strategy  → Tire Strategy Visualizer
/standings/[year]               → Season Standings & Trends
/drivers/[code]                 → Driver career page
/drivers/compare                → Historical Driver Comparison tool
```

### Telemetry Deep Dive Layout (signature page)
```
┌─────────────────────────────────────────────┐
│  [Driver A: VER ▼]   vs   [Driver B: HAM ▼]  │
│  [Lap selector: Fastest | Lap #]             │
├──────────────────────┬────────────────────────┤
│                      │                        │
│   Speed Trace Chart   │     Track Map          │
│   (D3 line, dual)     │  (color-coded by speed,│
│                      │   click to scrub)       │
├──────────────────────┴────────────────────────┤
│   Throttle / Brake Trace (stacked)             │
├─────────────────────────────────────────────┤
│   Delta Time Trace ("where time was gained")   │
└─────────────────────────────────────────────┘
```

---

## Design System — "Telemetry"

**Philosophy:** Cockpit HUD meets editorial sports site. Should feel fast,
precise, slightly technical — like you're looking at real engineering data,
not a fan blog. High contrast for chart readability above all else.

**Color Palette**
```
--track-black:     #0A0A0C    (background)
--surface:         #15151A    (cards)
--surface-raised:  #1E1E24    (elevated panels)
--border:          #2A2A32

--apex-red:        #E10600    (primary accent — F1's own red, CTAs, highlights)
--drs-green:       #00D2A0    (DRS active, positive deltas, fastest sector)
--purple-sector:   #C724B1    (fastest overall lap/sector — matches broadcast convention)
--yellow-flag:     #FFD500    (caution/flag states)

--text-primary:    #F5F5F7
--text-secondary:  #9A9AA5
--text-muted:      #56565F

--tire-soft:       #FF3333
--tire-medium:     #FFD500
--tire-hard:       #F5F5F5
--tire-intermediate: #43B02A
--tire-wet:        #0067B1
```

**Typography**
- Display/Lap times: `DM Mono` — precision matters, monospace for time alignment
- Headlines: `Inter` 600–700
- Body: `Inter` 400

**Signature Element:** The Telemetry Deep Dive speed trace — dual-driver overlay
with a synchronized vertical scrub line. Hovering anywhere on the chart shows
both drivers' speed/throttle/brake at that exact point, plus updates the track
map marker position simultaneously. This interaction is the entire value
proposition of the app — invest the most design/build effort here.

**Tire compound colors** follow official F1 broadcast convention exactly
(red/yellow/white/green/blue) — fans already know this color language, don't
reinvent it.

---

## Phase Plan

### Phase 1 — Foundation + Race Weekend Hub (Week 1–3)
- [ ] Django project, all models, TimescaleDB for Telemetry
- [ ] Separate FastF1 ingestion service (Python 3.10+ container)
- [ ] Jolpica-F1 sync for historical seasons + standings
- [ ] Session results ingestion (laps, no telemetry yet)
- [ ] Race Weekend Hub page

### Phase 2 — Comparison Tools (Week 4–5)
- [ ] Lap Time Comparison endpoint + UI
- [ ] Tire Strategy Visualizer endpoint + UI
- [ ] Pit stop comparison data

### Phase 3 — Telemetry Deep Dive (Week 6–8)
- [ ] On-demand telemetry ingestion task
- [ ] Telemetry comparison endpoint
- [ ] D3 speed trace + synchronized track map (the signature feature — budget
      the most time here)
- [ ] Delta time trace calculation and visualization

### Phase 4 — Season & History (Week 9–10)
- [ ] Season Standings & Trends page with progression chart
- [ ] Driver career stats aggregation
- [ ] Historical Driver Comparison tool
- [ ] Race Pace Prediction model (FP2/FP3 long-run analysis)

### Phase 5 — Polish (Week 11)
- [ ] Mobile responsive (telemetry charts are the hard part on small screens —
      consider simplified mobile view)
- [ ] SEO: per-race and per-driver metadata
- [ ] Performance: ensure telemetry queries are fast via TimescaleDB indexing
- [ ] "Unofficial / fan project" disclaimer per FastF1's own usage terms

---

## Data Quality & Legal Notes

- FastF1 and this platform are **unofficial fan projects**, not associated with
  Formula 1 companies — display this disclaimer in the footer, consistent with
  FastF1's own stated terms
- Do not use official F1 logos, team logos, or trademarked imagery — use
  team colors and generic representations only
- Telemetry data accuracy depends on F1's live timing service — note "data
  may be incomplete for some sessions" where applicable
- Radio/team radio data is unreliable since 2026 — do not build features that
  depend on it being present

---

## Out of Scope (v1)
- Live race-day real-time dashboard (FastF1 data is post-session, not live-live;
  OpenF1 has some live capability but is secondary priority)
- Fantasy F1 integration
- Betting odds
- User accounts / saved comparisons
- Mobile app (web responsive only)
- Pre-2018 seasons (telemetry data quality drops significantly before this)
