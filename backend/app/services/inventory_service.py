"""Inventory service for stock adjustments and transaction tracking."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import (
    ProductNotFoundException,
    InsufficientStockException,
    ValidationException
)
from app.models.product import Product
from app.models.inventory_transaction import InventoryTransaction
from app.schemas.inventory import StockAdjustment


class InventoryService:
    """Service class for inventory transaction operations."""
    
    def __init__(self, db: Session):
        """Initialize the inventory service with a database session."""
        self.db = db
    
    def adjust_stock(
        self,
        adjustment: StockAdjustment,
        user_id: Optional[UUID] = None
    ) -> InventoryTransaction:
        """
        Adjust product stock and record transaction.
        
        This method wraps the stock adjustment in a database transaction
        to ensure atomicity. If the adjustment would result in negative stock,
        the transaction is rolled back.
        
        Args:
            adjustment: Stock adjustment data
            user_id: Optional UUID of the user making the adjustment
            
        Returns:
            Created InventoryTransaction object
            
        Raises:
            ProductNotFoundException: If product is not found
            InsufficientStockException: If adjustment would result in negative stock
        """
        try:
            # Get product with row-level lock to prevent race conditions
            product = self.db.query(Product).filter(
                Product.id == adjustment.product_id
            ).with_for_update().first()
            
            if not product:
                raise ProductNotFoundException(
                    f"Product with ID {adjustment.product_id} not found"
                )
            
            # Calculate new stock level
            previous_stock = product.current_stock
            new_stock = previous_stock + adjustment.quantity
            
            # Validate that stock won't go negative
            if new_stock < 0:
                raise InsufficientStockException(
                    f"Insufficient stock. Current: {previous_stock}, "
                    f"Requested change: {adjustment.quantity}, "
                    f"Would result in: {new_stock}"
                )
            
            # Determine transaction type
            if adjustment.quantity > 0:
                transaction_type = "addition"
            elif adjustment.quantity < 0:
                transaction_type = "removal"
            else:
                transaction_type = "adjustment"
            
            # Update product stock
            product.current_stock = new_stock
            
            # Create transaction record
            transaction = InventoryTransaction(
                product_id=adjustment.product_id,
                transaction_type=transaction_type,
                quantity=adjustment.quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                reason=adjustment.reason,
                user_id=user_id
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            return transaction
            
        except (ProductNotFoundException, InsufficientStockException):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to adjust stock: {str(e)}")
    
    def get_movements(
        self,
        product_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """
        Retrieve stock movements with optional filtering.
        
        Args:
            product_id: Optional filter by product ID
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of InventoryTransaction objects with product details loaded
        """
        query = self.db.query(InventoryTransaction).options(
            joinedload(InventoryTransaction.product)
        )
        
        # Apply product filter if provided
        if product_id:
            query = query.filter(InventoryTransaction.product_id == product_id)
        
        # Order by most recent first
        query = query.order_by(desc(InventoryTransaction.created_at))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    def get_product_history(
        self,
        product_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """
        Retrieve stock movement history for a specific product.
        
        Args:
            product_id: UUID of the product
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of InventoryTransaction objects
            
        Raises:
            ProductNotFoundException: If product is not found
        """
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundException(f"Product with ID {product_id} not found")
        
        # Get transactions for this product
        return self.get_movements(product_id=product_id, skip=skip, limit=limit)
    
    def get_current_stock(self, product_id: UUID) -> int:
        """
        Get current stock level for a product.
        
        Args:
            product_id: UUID of the product
            
        Returns:
            Current stock quantity
            
        Raises:
            ProductNotFoundException: If product is not found
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise ProductNotFoundException(f"Product with ID {product_id} not found")
        
        return product.current_stock
