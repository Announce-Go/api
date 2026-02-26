#!/bin/bash
set -e

# Celery Worker (백그라운드)
celery -A app.tasks.celery_app worker --concurrency=1 -l info &

# Celery Beat (백그라운드)
celery -A app.tasks.celery_app beat -l info &

# FastAPI (포그라운드)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
