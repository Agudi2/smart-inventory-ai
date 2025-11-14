"""Alert service for business logic and alert management operations."""

import logging
from datetime import datetime, timedelta, date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import AlertNotFoundException, ValidationException
from app.models.alert import Alert
from app.models.product import Product
from app.models.ml_prediction import MLPrediction
from app.schemas.alert import AlertCreate

logger = logging.getLogger(__name__)


class AlertService:
    """Service class for alert-related operations."""
    
    def __init__(self, db: Session):
        """Initialize the alert service with a database session."""
        self.db = db
        self.alert_threshold_days = settings.alert_threshold_days
    
    def get_all_alerts(
        self,
        status: Optional[str] = None,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Alert]:
        """
        Retrieve all alerts with optional filtering.
        
        Args:
            status: Filter by status (active, acknowledged, resolved)
            alert_type: Filter by type (low_stock, predicted_depletion)
            severity: Filter by severity (warning, critical)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of Alert objects with product information loaded
        """
        query = self.db.query(Alert).options(joinedload(Alert.product))
        
        # Apply filters
        if status:
            query = query.filter(Alert.status == status)
        
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        # Order by created_at descending (newest first)
        query = query.order_by(Alert.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    def get_alert_by_id(self, alert_id: UUID) -> Alert:
        """
        Retrieve an alert by its ID.
        
        Args:
            alert_id: UUID of the alert
            
        Returns:
            Alert object with product information loaded
            
        Raises:
            AlertNotFoundException: If alert is not found
        """
        alert = self.db.query(Alert).options(
            joinedload(Alert.product)
        ).filter(Alert.id == alert_id).first()
        
        if not alert:
            raise AlertNotFoundException(f"Alert with ID {alert_id} not found")
        
        return alert
    
    def create_alert(self, alert_data: AlertCreate, send_email: bool = True) -> Alert:
        """
        Create a new alert.
        
        Args:
            alert_data: Alert creation data
            send_email: Whether to send email notification (default: True)
            
        Returns:
            Created Alert object
        """
        # Check if an active alert of the same type already exists for this product
        existing_alert = self.db.query(Alert).filter(
            and_(
                Alert.product_id == alert_data.product_id,
                Alert.alert_type == alert_data.alert_type,
                Alert.status == "active"
            )
        ).first()
        
        # If an active alert exists, don't create a duplicate
        if existing_alert:
            return existing_alert
        
        # Create new alert
        alert = Alert(**alert_data.model_dump())
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        # Send email notification if enabled
        if send_email and settings.email_notifications_enabled:
            try:
                self.send_alert_email(alert)
            except Exception as e:
                logger.error(f"Failed to send email for alert {alert.id}: {str(e)}")
        
        return alert
    
    def acknowledge_alert(self, alert_id: UUID) -> Alert:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: UUID of the alert to acknowledge
            
        Returns:
            Updated Alert object
            
        Raises:
            AlertNotFoundException: If alert is not found
            ValidationException: If alert is already resolved
        """
        alert = self.get_alert_by_id(alert_id)
        
        if alert.status == "resolved":
            raise ValidationException("Cannot acknowledge a resolved alert")
        
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def resolve_alert(self, alert_id: UUID) -> Alert:
        """
        Resolve an alert.
        
        Args:
            alert_id: UUID of the alert to resolve
            
        Returns:
            Updated Alert object
            
        Raises:
            AlertNotFoundException: If alert is not found
        """
        alert = self.get_alert_by_id(alert_id)
        
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        
        # If not already acknowledged, set acknowledged_at as well
        if not alert.acknowledged_at:
            alert.acknowledged_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def check_low_stock_alerts(self) -> List[Alert]:
        """
        Check all products for low stock conditions and create alerts.
        
        Creates alerts when current_stock < reorder_threshold.
        
        Returns:
            List of created or existing active low stock alerts
        """
        alerts_created = []
        
        # Find all products where current_stock < reorder_threshold
        low_stock_products = self.db.query(Product).filter(
            Product.current_stock < Product.reorder_threshold
        ).all()
        
        for product in low_stock_products:
            # Determine severity
            if product.current_stock == 0:
                severity = "critical"
                message = f"Product '{product.name}' is out of stock"
            else:
                severity = "warning"
                message = f"Product '{product.name}' is low on stock ({product.current_stock} units remaining, reorder threshold: {product.reorder_threshold})"
            
            # Check if an active alert already exists
            existing_alert = self.db.query(Alert).filter(
                and_(
                    Alert.product_id == product.id,
                    Alert.alert_type == "low_stock",
                    Alert.status == "active"
                )
            ).first()
            
            if not existing_alert:
                # Create new alert
                alert_data = AlertCreate(
                    product_id=product.id,
                    alert_type="low_stock",
                    severity=severity,
                    message=message
                )
                alert = self.create_alert(alert_data)
                alerts_created.append(alert)
            else:
                # Update existing alert if severity changed
                if existing_alert.severity != severity:
                    existing_alert.severity = severity
                    existing_alert.message = message
                    self.db.commit()
                alerts_created.append(existing_alert)
        
        return alerts_created
    
    def check_prediction_alerts(self, threshold_days: Optional[int] = None) -> List[Alert]:
        """
        Check all products for predicted depletion and create alerts.
        
        Creates alerts when predicted depletion date is within threshold days.
        
        Args:
            threshold_days: Number of days before depletion to trigger alert
                          (defaults to settings.alert_threshold_days)
        
        Returns:
            List of created or existing active prediction alerts
        """
        if threshold_days is None:
            threshold_days = self.alert_threshold_days
        
        alerts_created = []
        threshold_date = date.today() + timedelta(days=threshold_days)
        
        # Find all products with predictions that will deplete within threshold
        predictions = self.db.query(MLPrediction).options(
            joinedload(MLPrediction.product)
        ).filter(
            and_(
                MLPrediction.predicted_depletion_date.isnot(None),
                MLPrediction.predicted_depletion_date <= threshold_date,
                MLPrediction.predicted_depletion_date >= date.today()
            )
        ).order_by(MLPrediction.created_at.desc()).all()
        
        # Group by product_id to get the latest prediction for each product
        seen_products = set()
        
        for prediction in predictions:
            if prediction.product_id in seen_products:
                continue
            
            seen_products.add(prediction.product_id)
            product = prediction.product
            
            # Calculate days until depletion
            days_until_depletion = (prediction.predicted_depletion_date - date.today()).days
            
            # Determine severity
            if days_until_depletion <= 3:
                severity = "critical"
            else:
                severity = "warning"
            
            message = (
                f"Product '{product.name}' is predicted to run out of stock in {days_until_depletion} days "
                f"(on {prediction.predicted_depletion_date.strftime('%Y-%m-%d')}). "
                f"Confidence: {float(prediction.confidence_score) * 100:.1f}%"
            )
            
            # Check if an active alert already exists
            existing_alert = self.db.query(Alert).filter(
                and_(
                    Alert.product_id == product.id,
                    Alert.alert_type == "predicted_depletion",
                    Alert.status == "active"
                )
            ).first()
            
            if not existing_alert:
                # Create new alert
                alert_data = AlertCreate(
                    product_id=product.id,
                    alert_type="predicted_depletion",
                    severity=severity,
                    message=message
                )
                alert = self.create_alert(alert_data)
                alerts_created.append(alert)
            else:
                # Update existing alert if severity or message changed
                if existing_alert.severity != severity or existing_alert.message != message:
                    existing_alert.severity = severity
                    existing_alert.message = message
                    self.db.commit()
                alerts_created.append(existing_alert)
        
        return alerts_created
    
    def auto_resolve_alerts(self) -> int:
        """
        Automatically resolve alerts that are no longer valid.
        
        - Resolves low_stock alerts when stock is above reorder threshold
        - Resolves predicted_depletion alerts when depletion date has passed
        
        Returns:
            Number of alerts auto-resolved
        """
        resolved_count = 0
        
        # Get all active alerts
        active_alerts = self.db.query(Alert).options(
            joinedload(Alert.product)
        ).filter(
            or_(
                Alert.status == "active",
                Alert.status == "acknowledged"
            )
        ).all()
        
        for alert in active_alerts:
            should_resolve = False
            
            if alert.alert_type == "low_stock":
                # Resolve if stock is now above reorder threshold
                if alert.product.current_stock >= alert.product.reorder_threshold:
                    should_resolve = True
            
            elif alert.alert_type == "predicted_depletion":
                # Get the latest prediction for this product
                latest_prediction = self.db.query(MLPrediction).filter(
                    MLPrediction.product_id == alert.product_id
                ).order_by(MLPrediction.created_at.desc()).first()
                
                # Resolve if depletion date has passed or prediction no longer exists
                if not latest_prediction or not latest_prediction.predicted_depletion_date:
                    should_resolve = True
                elif latest_prediction.predicted_depletion_date < date.today():
                    should_resolve = True
                elif latest_prediction.predicted_depletion_date > date.today() + timedelta(days=self.alert_threshold_days):
                    # Depletion date is now beyond threshold
                    should_resolve = True
            
            if should_resolve:
                alert.status = "resolved"
                alert.resolved_at = datetime.utcnow()
                if not alert.acknowledged_at:
                    alert.acknowledged_at = datetime.utcnow()
                resolved_count += 1
        
        if resolved_count > 0:
            self.db.commit()
        
        return resolved_count
    
    def send_alert_email(self, alert: Alert, recipient_emails: Optional[List[str]] = None) -> bool:
        """
        Send email notification for an alert.
        
        Args:
            alert: Alert object to send notification for
            recipient_emails: Optional list of recipient emails (defaults to configured recipients)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.email_notifications_enabled:
            logger.debug("Email notifications are disabled")
            return False
        
        try:
            from app.services.email_service import EmailService
            
            email_service = EmailService()
            return email_service.send_alert_email(alert, recipient_emails)
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}", exc_info=True)
            return False
