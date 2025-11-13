"""Pydantic schemas for product-related requests and responses."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    """Base product schema with common fields."""
    
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    current_stock: int = Field(..., ge=0, description="Current stock quantity")
    reorder_threshold: int = Field(..., ge=0, description="Minimum stock level before reorder")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Cost per unit")
    
    @field_validator('sku', 'name', 'category')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure string fields are not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('barcode')
    @classmethod
    def validate_barcode(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean barcode if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    current_stock: Optional[int] = Field(None, ge=0)
    reorder_threshold: Optional[int] = Field(None, ge=0)
    barcode: Optional[str] = Field(None, max_length=100)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    
    @field_validator('name', 'category')
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure string fields are not empty or whitespace only."""
        if v is not None:
            if not v.strip():
                raise ValueError("Field cannot be empty or whitespace only")
            return v.strip()
        return v
    
    @field_validator('barcode')
    @classmethod
    def validate_barcode(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean barcode if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class ProductResponse(ProductBase):
    """Schema for product response with additional computed fields."""
    
    id: UUID
    stock_status: str = Field(..., description="Stock status: sufficient, low, or critical")
    predicted_depletion_date: Optional[datetime] = Field(None, description="Predicted date when stock will run out")
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }
