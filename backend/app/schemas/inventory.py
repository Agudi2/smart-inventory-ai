"""Pydantic schemas for inventory transaction requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class StockAdjustment(BaseModel):
    """Schema for adjusting product stock."""
    
    product_id: UUID = Field(..., description="UUID of the product")
    quantity: int = Field(..., description="Quantity to adjust (positive for addition, negative for removal)")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for stock adjustment")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Ensure quantity is not zero."""
        if v == 0:
            raise ValueError("Quantity cannot be zero")
        return v
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: Optional[str]) -> Optional[str]:
        """Clean reason string if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class InventoryTransactionResponse(BaseModel):
    """Schema for inventory transaction response."""
    
    id: UUID
    product_id: UUID
    transaction_type: str = Field(..., description="Type: addition, removal, or adjustment")
    quantity: int
    previous_stock: int
    new_stock: int
    reason: Optional[str]
    user_id: Optional[UUID]
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class StockMovementResponse(BaseModel):
    """Schema for stock movement with product details."""
    
    id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    transaction_type: str
    quantity: int
    previous_stock: int
    new_stock: int
    reason: Optional[str]
    user_id: Optional[UUID]
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }
