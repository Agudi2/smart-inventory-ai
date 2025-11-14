"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "smart_inventory",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.ml_tasks", "app.tasks.alert_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # 1 hour
)

# Configure Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # ML model training - runs weekly on Sunday at 2 AM
    "train-ml-models-weekly": {
        "task": "app.tasks.ml_tasks.train_all_models",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday at 2 AM
        "options": {
            "expires": 3600 * 6,  # Task expires after 6 hours
        }
    },
    # Alert checking - runs every hour
    "check-alerts-hourly": {
        "task": "app.tasks.alert_tasks.check_all_alerts",
        "schedule": crontab(minute=0),  # Every hour at minute 0
        "options": {
            "expires": 3600,  # Task expires after 1 hour
        }
    },
    # Auto-resolve alerts - runs every 6 hours
    "auto-resolve-alerts": {
        "task": "app.tasks.alert_tasks.auto_resolve_alerts",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "options": {
            "expires": 3600,  # Task expires after 1 hour
        }
    },
}

# Task routing configuration (optional, for future scaling)
celery_app.conf.task_routes = {
    "app.tasks.ml_tasks.*": {"queue": "ml_queue"},
    "app.tasks.alert_tasks.*": {"queue": "alerts_queue"},
}
