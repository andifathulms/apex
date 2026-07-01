# FastF1 requires Python 3.10+ and is dependency-heavy (pandas/numpy).
# Kept as a fully separate image from the Django backend by design.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FASTF1_CACHE_DIR=/data/fastf1-cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistent FastF1 cache volume mounted here (see docker-compose)
RUN mkdir -p /data/fastf1-cache

# Runs the Celery worker that consumes ingestion tasks
CMD ["celery", "-A", "ingest.worker", "worker", "-l", "info"]
