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


@router.get(
    "",
    response_model=List[VendorWithPricesResponse],
    summary="List all vendors",
    description="Retrieve all vendors with pagination and product count.",
    responses={
        200: {
            "description": "List of vendors retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Acme Supplies",
                            "contact_email": "sales@acme.com",
                            "contact_phone": "+1-555-0100",
                            "address": "123 Main St, City, State 12345",
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-15T10:30:00Z",
                            "product_count": 25
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def get_vendors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all vendors with pagination.
    
    Returns a paginated list of all vendors in the system, including
    the number of products each vendor supplies.
    
    **Query Parameters:**
    - **skip**: Number of records to skip (for pagination, default: 0)
    - **limit**: Maximum number of records to return (1-1000, default: 100)
    
    **Returns:**
    - List of vendors with contact information
    - Product count for each vendor
    - Creation and update timestamps
    
    **Use Cases:**
    - Display vendor directory
    - Vendor management dashboard
    - Supplier selection for new products
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


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new vendor",
    description="Add a new vendor/supplier to the system.",
    responses={
        201: {
            "description": "Vendor created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Acme Supplies",
                        "contact_email": "sales@acme.com",
                        "contact_phone": "+1-555-0100",
                        "address": "123 Main St, City, State 12345",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid vendor data"},
        401: {"description": "Not authenticated"}
    }
)
def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new vendor/supplier.
    
    Add a new vendor to the system for product sourcing and price comparison.
    After creating a vendor, you can add product prices using the vendor prices endpoints.
    
    **Request Body:**
    - **name**: Vendor name (required)
    - **contact_email**: Email address for vendor contact (optional)
    - **contact_phone**: Phone number for vendor contact (optional)
    - **address**: Physical address of vendor (optional)
    
    **Returns:**
    - Created vendor with generated UUID
    - Timestamps for creation and last update
    
    **Example Request:**
    ```json
    {
        "name": "Acme Supplies",
        "contact_email": "sales@acme.com",
        "contact_phone": "+1-555-0100",
        "address": "123 Main St, City, State 12345"
    }
    ```
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


@router.post(
    "/{vendor_id}/prices",
    response_model=VendorPriceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add vendor price for product",
    description="Add or update pricing information for a product from this vendor.",
    responses={
        201: {
            "description": "Vendor price added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "vendor_id": "123e4567-e89b-12d3-a456-426614174001",
                        "product_id": "123e4567-e89b-12d3-a456-426614174002",
                        "unit_price": 12.99,
                        "lead_time_days": 7,
                        "minimum_order_quantity": 10,
                        "last_updated": "2024-01-15T10:30:00Z",
                        "is_recommended": False
                    }
                }
            }
        },
        400: {"description": "Invalid price data"},
        401: {"description": "Not authenticated"},
        404: {"description": "Vendor or product not found"}
    }
)
def add_vendor_price(
    vendor_id: UUID,
    price_data: VendorPriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add or update vendor pricing for a product.
    
    This endpoint allows you to set or update the price a vendor charges for
    a specific product. If a price already exists for this vendor-product
    combination, it will be updated with the new information.
    
    **Path Parameters:**
    - **vendor_id**: UUID of the vendor
    
    **Request Body:**
    - **product_id**: UUID of the product (required)
    - **unit_price**: Price per unit in decimal format (required)
    - **lead_time_days**: Number of days for delivery (optional, default: 7)
    - **minimum_order_quantity**: Minimum order quantity (optional, default: 1)
    
    **Returns:**
    - Complete vendor price record with timestamps
    - is_recommended flag (calculated based on price comparison)
    
    **Use Cases:**
    - Adding new vendor pricing during product setup
    - Updating prices when vendors change their rates
    - Comparing multiple vendor options for restocking
    
    **Example Request:**
    ```json
    {
        "product_id": "123e4567-e89b-12d3-a456-426614174002",
        "unit_price": 12.99,
        "lead_time_days": 7,
        "minimum_order_quantity": 10
    }
    ```
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
