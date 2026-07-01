# Apex — F1 Analytics Platform

A fan-facing Formula 1 analytics platform built on official F1 timing data.
Turns millisecond-level telemetry into visual stories — lap comparisons, tire
strategy breakdowns, and corner-by-corner speed traces that broadcast graphics
never show you.

> **Unofficial fan project.** Not associated with Formula 1 companies. Built on
> [FastF1](https://github.com/theOehrly/Fast-F1). No official F1 logos or
> trademarked imagery are used.

## Architecture

| Layer | Technology |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Data Processing | FastF1 (Python) + pandas |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 16 + TimescaleDB |
| Frontend | Next.js 14 (App Router) + Tailwind |
| Charts | Recharts + D3.js |
| Container | Docker + Docker Compose |

The **FastF1 ingestion service** runs as a fully separate container (Python
3.10+) that talks to the shared PostgreSQL database directly via psycopg2 — it
does not import Django models.

```
apex/
├── backend/            # Django app — DRF, serves the API
├── ingestion-service/  # Separate FastF1 pipeline (psycopg2, no Django ORM)
├── frontend/           # Next.js 14 App Router
├── nginx/              # Reverse proxy config
└── docker-compose.yml
```

## Data Sources

- **FastF1** — official F1 timing/telemetry (primary, free, no key)
- **OpenF1** — near-real-time session status polling (secondary)
- **Jolpica-F1** — historical results/standings, Ergast successor (tertiary)

## Getting Started

```bash
cp .env.example .env
docker-compose up --build
```

Services:
- Frontend → http://localhost:3000
- API → http://localhost:8000/api/

## Documentation

- [PRD.md](PRD.md) — product requirements
- [CLAUDE.md](CLAUDE.md) — build conventions and order
