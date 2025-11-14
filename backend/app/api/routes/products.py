"""Product API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.vendor import ProductVendorResponse
from app.services.product_service import ProductService
from app.services.vendor_service import VendorService


router = APIRouter(prefix="/products", tags=["products"])


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Dependency to get ProductService instance."""
    return ProductService(db)


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List all products",
    description="Retrieve all products with optional filtering and pagination.",
    responses={
        200: {
            "description": "List of products retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "sku": "WDG-001",
                            "name": "Widget A",
                            "category": "Electronics",
                            "current_stock": 150,
                            "reorder_threshold": 20,
                            "barcode": "012345678905",
                            "unit_cost": 12.99,
                            "stock_status": "sufficient",
                            "predicted_depletion_date": None,
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-15T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name, SKU, or category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
) -> List[ProductResponse]:
    """
    Retrieve all products with optional filtering and pagination.
    
    Returns a list of all products in the inventory system with their current
    stock levels, status indicators, and optional ML predictions.
    
    **Query Parameters:**
    - **category**: Filter products by category (e.g., "Electronics", "Food")
    - **search**: Search for products by name, SKU, or category (case-insensitive)
    - **skip**: Number of records to skip (for pagination, default: 0)
    - **limit**: Maximum number of records to return (1-1000, default: 100)
    
    **Stock Status Values:**
    - `sufficient`: Stock level is above reorder threshold
    - `low`: Stock level is at or below reorder threshold but above zero
    - `critical`: Stock level is zero or negative
    
    **Returns:**
    - List of products with complete information
    - Stock status calculated based on current stock vs reorder threshold
    - Predicted depletion date (if ML prediction available)
    
    **Use Cases:**
    - Display inventory dashboard
    - Product catalog browsing
    - Stock level monitoring
    - Category-based inventory views
    """
    products = product_service.get_all_products(
        category=category,
        search=search,
        skip=skip,
        limit=limit
    )
    
    # Convert to response models with stock status
    response_products = []
    for product in products:
        product_dict = {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "current_stock": product.current_stock,
            "reorder_threshold": product.reorder_threshold,
            "barcode": product.barcode,
            "unit_cost": product.unit_cost,
            "stock_status": product_service.calculate_stock_status(product),
            "predicted_depletion_date": None,  # Will be populated by ML service in future task
            "created_at": product.created_at,
            "updated_at": product.updated_at
        }
        response_products.append(ProductResponse(**product_dict))
    
    return response_products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
) -> ProductResponse:
    """
    Retrieve a specific product by ID.
    
    - **product_id**: UUID of the product to retrieve
    """
    product = product_service.get_product_by_id(product_id)
    
    # Convert to response model with stock status
    product_dict = {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "current_stock": product.current_stock,
        "reorder_threshold": product.reorder_threshold,
        "barcode": product.barcode,
        "unit_cost": product.unit_cost,
        "stock_status": product_service.calculate_stock_status(product),
        "predicted_depletion_date": None,  # Will be populated by ML service in future task
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
    
    return ProductResponse(**product_dict)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Add a new product to the inventory system.",
    responses={
        201: {
            "description": "Product created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "sku": "WDG-001",
                        "name": "Widget A",
                        "category": "Electronics",
                        "current_stock": 100,
                        "reorder_threshold": 20,
                        "barcode": "012345678905",
                        "unit_cost": 12.99,
                        "stock_status": "sufficient",
                        "predicted_depletion_date": None,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid product data or duplicate SKU/barcode"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"}
    }
)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
) -> ProductResponse:
    """
    Create a new product in the inventory system.
    
    **Request Body:**
    - **sku**: Stock Keeping Unit - unique identifier (required)
    - **name**: Product name (required)
    - **category**: Product category (required)
    - **current_stock**: Initial stock quantity (required, must be >= 0)
    - **reorder_threshold**: Minimum stock level before reorder alert (required, must be >= 0)
    - **barcode**: Optional barcode (must be unique if provided)
    - **unit_cost**: Optional cost per unit in decimal format
    
    **Validation:**
    - SKU must be unique across all products
    - Barcode must be unique if provided
    - Stock and threshold must be non-negative
    
    **Returns:**
    - Created product with generated UUID
    - Initial stock status calculated
    - Timestamps for creation
    
    **Example Request:**
    ```json
    {
        "sku": "WDG-001",
        "name": "Widget A",
        "category": "Electronics",
        "current_stock": 100,
        "reorder_threshold": 20,
        "barcode": "012345678905",
        "unit_cost": 12.99
    }
    ```
    """
    product = product_service.create_product(product_data)
    
    # Convert to response model with stock status
    product_dict = {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "current_stock": product.current_stock,
        "reorder_threshold": product.reorder_threshold,
        "barcode": product.barcode,
        "unit_cost": product.unit_cost,
        "stock_status": product_service.calculate_stock_status(product),
        "predicted_depletion_date": None,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
    
    return ProductResponse(**product_dict)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
) -> ProductResponse:
    """
    Update an existing product.
    
    - **product_id**: UUID of the product to update
    - All fields are optional; only provided fields will be updated
    """
    product = product_service.update_product(product_id, product_data)
    
    # Convert to response model with stock status
    product_dict = {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "current_stock": product.current_stock,
        "reorder_threshold": product.reorder_threshold,
        "barcode": product.barcode,
        "unit_cost": product.unit_cost,
        "stock_status": product_service.calculate_stock_status(product),
        "predicted_depletion_date": None,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
    
    return ProductResponse(**product_dict)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
) -> None:
    """
    Delete a product.
    
    - **product_id**: UUID of the product to delete
    """
    product_service.delete_product(product_id)
    return None


@router.get("/{product_id}/vendors", response_model=List[ProductVendorResponse])
async def get_product_vendors(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ProductVendorResponse]:
    """
    Get all vendors for a specific product with price comparison.
    
    Returns a list of vendors sorted by price (lowest first).
    The vendor with the lowest price is marked as recommended.
    
    - **product_id**: UUID of the product
    """
    vendor_service = VendorService(db)
    return vendor_service.get_vendors_for_product(product_id)
