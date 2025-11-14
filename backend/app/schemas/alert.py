"""Pydantic schemas for alert-related requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    """Base alert schema with common fields."""
    
    product_id: UUID = Field(..., description="UUID of the product")
    alert_type: str = Field(..., description="Type of alert: low_stock or predicted_depletion")
    severity: str = Field(..., description="Severity level: warning or critical")
    message: str = Field(..., description="Alert message")


class AlertCreate(AlertBase):
    """Schema for creating a new alert."""
    pass


class AlertResponse(AlertBase):
    """Schema for alert response."""
    
    id: UUID
    status: str = Field(..., description="Alert status: active, acknowledged, or resolved")
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Include product information for convenience
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    current_stock: Optional[int] = None
    
    model_config = {
        "from_attributes": True
    }


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""
    pass


class AlertResolve(BaseModel):
    """Schema for resolving an alert."""
    pass


class AlertSettingsResponse(BaseModel):
    """Schema for alert settings response."""
    
    alert_threshold_days: int = Field(..., description="Days before predicted depletion to trigger alert")
    low_stock_enabled: bool = Field(default=True, description="Enable low stock alerts")
    predicted_depletion_enabled: bool = Field(default=True, description="Enable predicted depletion alerts")
    email_notifications_enabled: bool = Field(default=False, description="Enable email notifications for alerts")
    alert_recipient_emails: list[str] = Field(default=[], description="List of email addresses to receive alert notifications")


class AlertSettingsUpdate(BaseModel):
    """Schema for updating alert settings."""
    
    alert_threshold_days: Optional[int] = Field(None, ge=1, le=90, description="Days before predicted depletion to trigger alert")
    low_stock_enabled: Optional[bool] = Field(None, description="Enable low stock alerts")
    predicted_depletion_enabled: Optional[bool] = Field(None, description="Enable predicted depletion alerts")
    email_notifications_enabled: Optional[bool] = Field(None, description="Enable email notifications for alerts")
    alert_recipient_emails: Optional[list[str]] = Field(None, description="List of email addresses to receive alert notifications")
