"""Local development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Allow all origins in local dev for convenience
CORS_ALLOW_ALL_ORIGINS = True

# Run Celery tasks eagerly (synchronously) unless a broker is available.
# Comment out to exercise the real worker via docker-compose.
CELERY_TASK_ALWAYS_EAGER = os.environ.get(  # noqa: F405
    "CELERY_TASK_ALWAYS_EAGER", "False"
).lower() == "true"
