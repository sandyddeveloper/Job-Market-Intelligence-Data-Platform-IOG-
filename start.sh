#!/bin/bash

# Start Redis in the background
redis-server --daemonize yes

# Export default environment variables if not already set by host
export SECRET_KEY="${SECRET_KEY:-prod-secret-key-huggingface-spaces}"
export DEBUG="${DEBUG:-False}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-*}"
export DATABASE_ENGINE="${DATABASE_ENGINE:-django.db.backends.sqlite3}"
export DATABASE_NAME="${DATABASE_NAME:-db.sqlite3}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/0}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}"


# Apply database migrations
python manage.py migrate --noinput

# Collect static files for production
python manage.py collectstatic --noinput

# Start Celery worker and scheduler (beat) processes in the background
celery -A Settings worker --loglevel=info &
celery -A Settings beat --loglevel=info --pidfile=/tmp/celerybeat.pid &

# Start Django Web Server via Gunicorn on Hugging Face default port 7860
gunicorn Settings.wsgi:application --bind 0.0.0.0:7860
