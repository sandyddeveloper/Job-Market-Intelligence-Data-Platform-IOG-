---
title: Job Market Intelligence
emoji: 💼
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Job Market Intelligence Data Platform

Advanced Data Platform for Job Market Analytics, Talent Intelligence, and Resume Parsing.

## Local Development
Run the development server locally:
```bash
python manage.py runserver
```

## Running Tasks
Ensure Redis is running, then start the Celery worker:
```bash
celery -A Settings worker -l info
```
