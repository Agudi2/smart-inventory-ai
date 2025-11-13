"""Pydantic schemas for barcode-related requests and responses."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BarcodeScanRequest(BaseModel):
    """Schema for barcode scan request."""
    
    barcode: str = Field(..., min_length=1, max_length=100, description="Scanned barcode value")
    

class BarcodeProductInfo(BaseModel):
    """Schema for external product information from barcode API."""
    
    barcode: str = Field(..., description="Barcode value")
    title: Optional[str] = Field(None, description="Product title/name")
    brand: Optional[str] = Field(None, description="Product brand")
    category: Optional[str] = Field(None, description="Product category")
    description: Optional[str] = Field(None, description="Product description")
    images: Optional[list[str]] = Field(default_factory=list, description="Product image URLs")


class BarcodeScanResponse(BaseModel):
    """Schema for barcode scan response."""
    
    found: bool = Field(..., description="Whether product was found in database")
    product_id: Optional[UUID] = Field(None, description="Product ID if found in database")
    product_name: Optional[str] = Field(None, description="Product name if found")
    current_stock: Optional[int] = Field(None, description="Current stock if found")
    external_info: Optional[BarcodeProductInfo] = Field(None, description="External product info if not found in database")


class BarcodeLinkRequest(BaseModel):
    """Schema for linking a barcode to an existing product."""
    
    barcode: str = Field(..., min_length=1, max_length=100, description="Barcode to link")
    product_id: UUID = Field(..., description="Product ID to link barcode to")


class BarcodeLinkResponse(BaseModel):
    """Schema for barcode link response."""
    
    success: bool = Field(..., description="Whether the link was successful")
    message: str = Field(..., description="Response message")
    product_id: UUID = Field(..., description="Product ID")
