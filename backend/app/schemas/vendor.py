from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class VendorBase(BaseModel):
    """Base vendor schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Vendor name")
    contact_email: Optional[EmailStr] = Field(None, description="Vendor contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Vendor contact phone")
    address: Optional[str] = Field(None, description="Vendor address")


class VendorCreate(VendorBase):
    """Schema for creating a new vendor."""
    pass


class VendorUpdate(BaseModel):
    """Schema for updating a vendor."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None


class VendorResponse(VendorBase):
    """Schema for vendor response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VendorPriceBase(BaseModel):
    """Base vendor price schema."""
    unit_price: Decimal = Field(..., gt=0, description="Unit price for the product")
    lead_time_days: int = Field(default=7, ge=0, description="Lead time in days")
    minimum_order_quantity: int = Field(default=1, ge=1, description="Minimum order quantity")


class VendorPriceCreate(VendorPriceBase):
    """Schema for creating a vendor price."""
    product_id: UUID = Field(..., description="Product ID")


class VendorPriceUpdate(BaseModel):
    """Schema for updating a vendor price."""
    unit_price: Optional[Decimal] = Field(None, gt=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    minimum_order_quantity: Optional[int] = Field(None, ge=1)


class VendorPriceResponse(VendorPriceBase):
    """Schema for vendor price response."""
    id: UUID
    vendor_id: UUID
    product_id: UUID
    last_updated: datetime
    is_recommended: bool = Field(default=False, description="Whether this is the recommended vendor")
    
    class Config:
        from_attributes = True


class ProductVendorResponse(VendorPriceResponse):
    """Schema for vendor information in product context."""
    vendor_name: str = Field(..., description="Vendor name")
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    
    class Config:
        from_attributes = True


class VendorWithPricesResponse(VendorResponse):
    """Schema for vendor with associated product prices."""
    product_count: int = Field(default=0, description="Number of products from this vendor")
    
    class Config:
        from_attributes = True
