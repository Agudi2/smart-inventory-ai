"""Celery tasks for alert checking and notifications."""

import logging
from typing import Dict, Any, Optional

from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session management."""
    
    _db: Session = None
    
    @property
    def db(self) -> Session:
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Clean up database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.alert_tasks.check_low_stock_alerts",
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def check_low_stock_alerts(self) -> Dict[str, Any]:
    """
    Check all products for low stock conditions and create alerts.
    
    Returns:
        Dictionary with summary of alerts created
    """
    try:
        logger.info("Starting low stock alert check")
        
        # Initialize alert service
        alert_service = AlertService(self.db)
        
        # Check for low stock alerts
        alerts = alert_service.check_low_stock_alerts()
        
        result = {
            "success": True,
            "alerts_created": len(alerts),
            "alert_ids": [str(alert.id) for alert in alerts],
            "message": f"Created or updated {len(alerts)} low stock alerts"
        }
        
        logger.info(f"Low stock alert check completed: {len(alerts)} alerts")
        return result
        
    except Exception as e:
        logger.error(f"Error checking low stock alerts: {str(e)}", exc_info=True)
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying low stock alert check (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e),
            "message": f"Low stock alert check failed after {self.max_retries} retries"
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.alert_tasks.check_prediction_alerts",
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def check_prediction_alerts(self, threshold_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Check all products for predicted depletion and create alerts.
    
    Args:
        threshold_days: Number of days before depletion to trigger alert
    
    Returns:
        Dictionary with summary of alerts created
    """
    try:
        logger.info("Starting prediction alert check")
        
        # Initialize alert service
        alert_service = AlertService(self.db)
        
        # Check for prediction alerts
        alerts = alert_service.check_prediction_alerts(threshold_days=threshold_days)
        
        result = {
            "success": True,
            "alerts_created": len(alerts),
            "alert_ids": [str(alert.id) for alert in alerts],
            "threshold_days": threshold_days or alert_service.alert_threshold_days,
            "message": f"Created or updated {len(alerts)} prediction alerts"
        }
        
        logger.info(f"Prediction alert check completed: {len(alerts)} alerts")
        return result
        
    except Exception as e:
        logger.error(f"Error checking prediction alerts: {str(e)}", exc_info=True)
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying prediction alert check (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e),
            "message": f"Prediction alert check failed after {self.max_retries} retries"
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.alert_tasks.check_all_alerts"
)
def check_all_alerts(self, threshold_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Check all alert types (low stock and predictions).
    
    This is the main scheduled task that runs hourly.
    
    Args:
        threshold_days: Number of days before depletion to trigger alert
    
    Returns:
        Dictionary with summary of all alerts created
    """
    try:
        logger.info("Starting comprehensive alert check")
        
        # Initialize alert service
        alert_service = AlertService(self.db)
        
        # Check low stock alerts
        low_stock_alerts = alert_service.check_low_stock_alerts()
        logger.info(f"Low stock alerts: {len(low_stock_alerts)}")
        
        # Check prediction alerts
        prediction_alerts = alert_service.check_prediction_alerts(threshold_days=threshold_days)
        logger.info(f"Prediction alerts: {len(prediction_alerts)}")
        
        result = {
            "success": True,
            "low_stock_alerts": len(low_stock_alerts),
            "prediction_alerts": len(prediction_alerts),
            "total_alerts": len(low_stock_alerts) + len(prediction_alerts),
            "threshold_days": threshold_days or alert_service.alert_threshold_days,
            "message": f"Alert check completed: {len(low_stock_alerts)} low stock, {len(prediction_alerts)} predictions"
        }
        
        logger.info(
            f"Comprehensive alert check completed. "
            f"Total alerts: {result['total_alerts']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in comprehensive alert check: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Comprehensive alert check failed"
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.alert_tasks.auto_resolve_alerts",
    max_retries=2,
    default_retry_delay=300  # 5 minutes
)
def auto_resolve_alerts(self) -> Dict[str, Any]:
    """
    Automatically resolve alerts that are no longer valid.
    
    Returns:
        Dictionary with summary of alerts resolved
    """
    try:
        logger.info("Starting auto-resolve alerts task")
        
        # Initialize alert service
        alert_service = AlertService(self.db)
        
        # Auto-resolve alerts
        resolved_count = alert_service.auto_resolve_alerts()
        
        result = {
            "success": True,
            "alerts_resolved": resolved_count,
            "message": f"Auto-resolved {resolved_count} alerts"
        }
        
        logger.info(f"Auto-resolve completed: {resolved_count} alerts resolved")
        return result
        
    except Exception as e:
        logger.error(f"Error auto-resolving alerts: {str(e)}", exc_info=True)
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying auto-resolve (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e),
            "message": f"Auto-resolve failed after {self.max_retries} retries"
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.alert_tasks.send_alert_notification",
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def send_alert_notification(self, alert_id: str) -> Dict[str, Any]:
    """
    Send email notification for a specific alert.
    
    This task is designed for future email notification implementation.
    
    Args:
        alert_id: UUID string of the alert
    
    Returns:
        Dictionary with notification status
    """
    try:
        logger.info(f"Sending notification for alert {alert_id}")
        
        # Initialize alert service
        alert_service = AlertService(self.db)
        
        # Get alert details
        from uuid import UUID
        alert = alert_service.get_alert_by_id(UUID(alert_id))
        
        # TODO: Implement email sending logic here
        # For now, just log the alert
        logger.info(
            f"Alert notification: {alert.alert_type} - {alert.severity} - "
            f"Product: {alert.product.name} - {alert.message}"
        )
        
        result = {
            "success": True,
            "alert_id": alert_id,
            "message": "Notification logged (email sending not yet implemented)"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending alert notification: {str(e)}", exc_info=True)
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying notification send (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "alert_id": alert_id,
            "error": str(e),
            "message": f"Notification failed after {self.max_retries} retries"
        }
