from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.vendor_service import VendorService
from app.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorResponse,
    VendorPriceCreate,
    VendorPriceResponse,
    VendorPriceUpdate,
    ProductVendorResponse,
    VendorWithPricesResponse
)

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("", response_model=List[VendorWithPricesResponse])
def get_vendors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all vendors with pagination.
    
    Returns a list of all vendors in the system.
    """
    service = VendorService(db)
    vendors = service.get_all_vendors(skip=skip, limit=limit)
    
    # Add product count to each vendor
    result = []
    for vendor in vendors:
        product_count = service.get_vendor_product_count(vendor.id)
        vendor_dict = {
            "id": vendor.id,
            "name": vendor.name,
            "contact_email": vendor.contact_email,
            "contact_phone": vendor.contact_phone,
            "address": vendor.address,
            "created_at": vendor.created_at,
            "updated_at": vendor.updated_at,
            "product_count": product_count
        }
        result.append(VendorWithPricesResponse(**vendor_dict))
    
    return result


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific vendor by ID.
    """
    service = VendorService(db)
    return service.get_vendor_by_id(vendor_id)


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new vendor.
    
    Requires authentication.
    """
    service = VendorService(db)
    return service.create_vendor(vendor_data)


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: UUID,
    vendor_data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update vendor information.
    
    Requires authentication.
    """
    service = VendorService(db)
    return service.update_vendor(vendor_id, vendor_data)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a vendor.
    
    Requires authentication. This will also delete all associated vendor prices.
    """
    service = VendorService(db)
    service.delete_vendor(vendor_id)
    return None


@router.post("/{vendor_id}/prices", response_model=VendorPriceResponse, status_code=status.HTTP_201_CREATED)
def add_vendor_price(
    vendor_id: UUID,
    price_data: VendorPriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add or update a vendor price for a product.
    
    If a price already exists for this vendor-product combination, it will be updated.
    Otherwise, a new price record will be created.
    """
    service = VendorService(db)
    vendor_price = service.add_vendor_price(vendor_id, price_data)
    
    return VendorPriceResponse(
        id=vendor_price.id,
        vendor_id=vendor_price.vendor_id,
        product_id=vendor_price.product_id,
        unit_price=vendor_price.unit_price,
        lead_time_days=vendor_price.lead_time_days,
        minimum_order_quantity=vendor_price.minimum_order_quantity,
        last_updated=vendor_price.last_updated,
        is_recommended=False
    )


@router.put("/{vendor_id}/prices/{product_id}", response_model=VendorPriceResponse)
def update_vendor_price(
    vendor_id: UUID,
    product_id: UUID,
    price_data: VendorPriceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing vendor price.
    """
    service = VendorService(db)
    vendor_price = service.update_vendor_price(vendor_id, product_id, price_data)
    
    return VendorPriceResponse(
        id=vendor_price.id,
        vendor_id=vendor_price.vendor_id,
        product_id=vendor_price.product_id,
        unit_price=vendor_price.unit_price,
        lead_time_days=vendor_price.lead_time_days,
        minimum_order_quantity=vendor_price.minimum_order_quantity,
        last_updated=vendor_price.last_updated,
        is_recommended=False
    )
