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
                "Positive quantity adds stock, negative removes stock."
)
async def adjust_stock(
    adjustment: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adjust product stock level.
    
    - **product_id**: UUID of the product to adjust
    - **quantity**: Amount to adjust (positive for addition, negative for removal)
    - **reason**: Optional reason for the adjustment
    
    Returns the created inventory transaction record.
    """
    service = InventoryService(db)
    transaction = service.adjust_stock(adjustment, user_id=current_user.id)
    return transaction


@router.get(
    "/movements",
    response_model=List[StockMovementResponse],
    status_code=status.HTTP_200_OK,
    summary="Get stock movements",
    description="Retrieve all stock movements with optional filtering and pagination."
)
async def get_movements(
    product_id: Optional[UUID] = Query(None, description="Filter by product ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get stock movement history.
    
    - **product_id**: Optional filter by product ID
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    
    Returns a list of inventory transactions with product details.
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
    description="Retrieve stock movement history for a specific product."
)
async def get_product_history(
    product_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get stock movement history for a specific product.
    
    - **product_id**: UUID of the product
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    
    Returns a list of inventory transactions for the specified product.
    """
    service = InventoryService(db)
    transactions = service.get_product_history(product_id, skip=skip, limit=limit)
    return transactions
