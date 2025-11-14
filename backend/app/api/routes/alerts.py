"""Alert API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.alert import (
    AlertResponse,
    AlertAcknowledge,
    AlertResolve,
    AlertSettingsResponse,
    AlertSettingsUpdate
)
from app.services.alert_service import AlertService


router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    """Dependency to get AlertService instance."""
    return AlertService(db)


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status: active, acknowledged, resolved"),
    alert_type: Optional[str] = Query(None, description="Filter by type: low_stock, predicted_depletion"),
    severity: Optional[str] = Query(None, description="Filter by severity: warning, critical"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
) -> List[AlertResponse]:
    """
    Retrieve all alerts with optional filtering.
    
    - **status**: Filter alerts by status (active, acknowledged, resolved)
    - **alert_type**: Filter alerts by type (low_stock, predicted_depletion)
    - **severity**: Filter alerts by severity (warning, critical)
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    alerts = alert_service.get_all_alerts(
        status=status,
        alert_type=alert_type,
        severity=severity,
        skip=skip,
        limit=limit
    )
    
    # Convert to response models with product information
    response_alerts = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "product_id": alert.product_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "status": alert.status,
            "created_at": alert.created_at,
            "acknowledged_at": alert.acknowledged_at,
            "resolved_at": alert.resolved_at,
            "product_name": alert.product.name if alert.product else None,
            "product_sku": alert.product.sku if alert.product else None,
            "current_stock": alert.product.current_stock if alert.product else None,
        }
        response_alerts.append(AlertResponse(**alert_dict))
    
    return response_alerts


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
) -> AlertResponse:
    """
    Acknowledge an alert.
    
    Changes the alert status from 'active' to 'acknowledged'.
    
    - **alert_id**: UUID of the alert to acknowledge
    """
    alert = alert_service.acknowledge_alert(alert_id)
    
    # Convert to response model with product information
    alert_dict = {
        "id": alert.id,
        "product_id": alert.product_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "status": alert.status,
        "created_at": alert.created_at,
        "acknowledged_at": alert.acknowledged_at,
        "resolved_at": alert.resolved_at,
        "product_name": alert.product.name if alert.product else None,
        "product_sku": alert.product.sku if alert.product else None,
        "current_stock": alert.product.current_stock if alert.product else None,
    }
    
    return AlertResponse(**alert_dict)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
) -> AlertResponse:
    """
    Resolve an alert.
    
    Changes the alert status to 'resolved' and sets the resolved timestamp.
    
    - **alert_id**: UUID of the alert to resolve
    """
    alert = alert_service.resolve_alert(alert_id)
    
    # Convert to response model with product information
    alert_dict = {
        "id": alert.id,
        "product_id": alert.product_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "status": alert.status,
        "created_at": alert.created_at,
        "acknowledged_at": alert.acknowledged_at,
        "resolved_at": alert.resolved_at,
        "product_name": alert.product.name if alert.product else None,
        "product_sku": alert.product.sku if alert.product else None,
        "current_stock": alert.product.current_stock if alert.product else None,
    }
    
    return AlertResponse(**alert_dict)


@router.get("/settings", response_model=AlertSettingsResponse)
async def get_alert_settings(
    current_user: User = Depends(get_current_user)
) -> AlertSettingsResponse:
    """
    Get current alert settings.
    
    Returns the configuration for alert generation including:
    - Alert threshold days (days before predicted depletion to trigger alert)
    - Low stock alerts enabled/disabled
    - Predicted depletion alerts enabled/disabled
    """
    return AlertSettingsResponse(
        alert_threshold_days=settings.alert_threshold_days,
        low_stock_enabled=True,  # These could be stored in database in future
        predicted_depletion_enabled=True
    )


@router.put("/settings", response_model=AlertSettingsResponse)
async def update_alert_settings(
    settings_update: AlertSettingsUpdate,
    current_user: User = Depends(get_current_user)
) -> AlertSettingsResponse:
    """
    Update alert settings.
    
    Note: In this implementation, settings are stored in environment variables.
    This endpoint returns the current settings. In a production system,
    these settings would be stored in the database per user or organization.
    
    - **alert_threshold_days**: Days before predicted depletion to trigger alert (1-90)
    - **low_stock_enabled**: Enable or disable low stock alerts
    - **predicted_depletion_enabled**: Enable or disable predicted depletion alerts
    """
    # In a production system, you would update settings in the database here
    # For now, we just return the current settings from config
    
    # If alert_threshold_days is provided, update the settings object
    # Note: This will only persist for the current session
    if settings_update.alert_threshold_days is not None:
        settings.alert_threshold_days = settings_update.alert_threshold_days
    
    return AlertSettingsResponse(
        alert_threshold_days=settings.alert_threshold_days,
        low_stock_enabled=settings_update.low_stock_enabled if settings_update.low_stock_enabled is not None else True,
        predicted_depletion_enabled=settings_update.predicted_depletion_enabled if settings_update.predicted_depletion_enabled is not None else True
    )
