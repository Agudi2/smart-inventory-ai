"""Celery tasks package."""

from app.tasks.ml_tasks import (
    train_model_for_product,
    train_all_models,
    generate_prediction,
    batch_generate_predictions
)
from app.tasks.alert_tasks import (
    check_low_stock_alerts,
    check_prediction_alerts,
    check_all_alerts,
    auto_resolve_alerts,
    send_alert_notification
)

__all__ = [
    # ML tasks
    "train_model_for_product",
    "train_all_models",
    "generate_prediction",
    "batch_generate_predictions",
    # Alert tasks
    "check_low_stock_alerts",
    "check_prediction_alerts",
    "check_all_alerts",
    "auto_resolve_alerts",
    "send_alert_notification",
]
