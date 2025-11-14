"""API routes for inventory transaction management."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.inventory import (
    StockAdjustment,
    InventoryTransactionResponse,
    StockMovementResponse
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post(
    "/adjust",
    response_model=InventoryTransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Adjust product stock",
    description="Adjust stock level for a product and record the transaction. "
                "Positive quantity adds stock, negative removes stock.",
    responses={
        200: {
            "description": "Stock adjusted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "product_id": "123e4567-e89b-12d3-a456-426614174001",
                        "transaction_type": "adjustment",
                        "quantity": 50,
                        "previous_stock": 100,
                        "new_stock": 150,
                        "reason": "Received shipment from vendor",
                        "user_id": "123e4567-e89b-12d3-a456-426614174002",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid request or insufficient stock"},
        401: {"description": "Not authenticated"},
        404: {"description": "Product not found"}
    }
)
async def adjust_stock(
    adjustment: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adjust product stock level and record the transaction.
    
    This endpoint allows you to add or remove stock from a product. The adjustment
    is recorded as an inventory transaction with full audit trail including the user
    who made the change, timestamp, and reason.
    
    **Request Body:**
    - **product_id**: UUID of the product to adjust
    - **quantity**: Amount to adjust (positive for addition, negative for removal)
    - **reason**: Optional reason for the adjustment (e.g., "Received shipment", "Damaged goods")
    
    **Validation:**
    - Quantity cannot result in negative stock levels
    - Product must exist in the database
    
    **Returns:**
    - Complete transaction record including previous and new stock levels
    - Transaction type, timestamp, and user information
    
    **Example Request:**
    ```json
    {
        "product_id": "123e4567-e89b-12d3-a456-426614174001",
        "quantity": 50,
        "reason": "Received shipment from vendor"
    }
    ```
    """
    service = InventoryService(db)
    transaction = service.adjust_stock(adjustment, user_id=current_user.id)
    return transaction


@router.get(
    "/movements",
    response_model=List[StockMovementResponse],
    status_code=status.HTTP_200_OK,
    summary="Get stock movements",
    description="Retrieve all stock movements with optional filtering and pagination.",
    responses={
        200: {
            "description": "List of stock movements retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "product_id": "123e4567-e89b-12d3-a456-426614174001",
                            "product_name": "Widget A",
                            "product_sku": "WDG-001",
                            "transaction_type": "adjustment",
                            "quantity": 50,
                            "previous_stock": 100,
                            "new_stock": 150,
                            "reason": "Received shipment",
                            "user_id": "123e4567-e89b-12d3-a456-426614174002",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def get_movements(
    product_id: Optional[UUID] = Query(None, description="Filter by product ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve stock movement history with optional filtering.
    
    This endpoint returns a paginated list of all inventory transactions across
    all products or filtered to a specific product. Each movement includes complete
    product details and transaction information.
    
    **Query Parameters:**
    - **product_id**: Optional UUID to filter movements for a specific product
    - **skip**: Number of records to skip (for pagination, default: 0)
    - **limit**: Maximum number of records to return (1-1000, default: 100)
    
    **Returns:**
    - List of stock movements with product details (name, SKU)
    - Transaction details (type, quantity, previous/new stock)
    - Audit information (user, timestamp, reason)
    
    **Use Cases:**
    - View all inventory activity across the system
    - Track stock changes for a specific product
    - Audit inventory adjustments and identify patterns
    """
    service = InventoryService(db)
    transactions = service.get_movements(product_id=product_id, skip=skip, limit=limit)
    
    # Transform to include product details
    movements = []
    for transaction in transactions:
        movement = StockMovementResponse(
            id=transaction.id,
            product_id=transaction.product_id,
            product_name=transaction.product.name,
            product_sku=transaction.product.sku,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            previous_stock=transaction.previous_stock,
            new_stock=transaction.new_stock,
            reason=transaction.reason,
            user_id=transaction.user_id,
            created_at=transaction.created_at
        )
        movements.append(movement)
    
    return movements


@router.get(
    "/products/{product_id}/history",
    response_model=List[InventoryTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get product stock history",
    description="Retrieve complete stock movement history for a specific product.",
    responses={
        200: {
            "description": "Product history retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "product_id": "123e4567-e89b-12d3-a456-426614174001",
                            "transaction_type": "adjustment",
                            "quantity": 50,
                            "previous_stock": 100,
                            "new_stock": 150,
                            "reason": "Received shipment",
                            "user_id": "123e4567-e89b-12d3-a456-426614174002",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Product not found"}
    }
)
async def get_product_history(
    product_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve complete stock movement history for a specific product.
    
    This endpoint returns all inventory transactions for a single product,
    ordered by timestamp (most recent first). Useful for tracking product
    lifecycle and understanding stock level changes over time.
    
    **Path Parameters:**
    - **product_id**: UUID of the product
    
    **Query Parameters:**
    - **skip**: Number of records to skip (for pagination, default: 0)
    - **limit**: Maximum number of records to return (1-1000, default: 100)
    
    **Returns:**
    - Chronological list of all stock adjustments for the product
    - Each transaction includes quantity, previous/new stock, reason, and user
    
    **Use Cases:**
    - Audit trail for a specific product
    - Analyze consumption patterns for ML predictions
    - Investigate stock discrepancies
    """
    service = InventoryService(db)
    transactions = service.get_product_history(product_id, skip=skip, limit=limit)
    return transactions
