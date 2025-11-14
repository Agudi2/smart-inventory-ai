"""Unit tests for InventoryService."""

import pytest
from uuid import uuid4
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.schemas.inventory import StockAdjustment
from app.schemas.product import ProductCreate
from app.core.exceptions import ProductNotFoundException, InsufficientStockException


class TestInventoryService:
    """Test cases for InventoryService methods."""
    
    def test_adjust_stock_addition(self, db_session):
        """Test adding stock to a product."""
        # Create a product first
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=50, reorder_threshold=20
        ))
        
        # Adjust stock
        inventory_service = InventoryService(db_session)
        adjustment = StockAdjustment(
            product_id=product.id,
            quantity=30,
            reason="Restocking"
        )
        
        transaction = inventory_service.adjust_stock(adjustment)
        
        assert transaction.product_id == product.id
        assert transaction.quantity == 30
        assert transaction.previous_stock == 50
        assert transaction.new_stock == 80
        assert transaction.transaction_type == "addition"
        assert transaction.reason == "Restocking"
        
        # Verify product stock was updated
        updated_product = product_service.get_product_by_id(product.id)
        assert updated_product.current_stock == 80
    
    def test_adjust_stock_removal(self, db_session):
        """Test removing stock from a product."""
        # Create a product
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        
        # Remove stock
        inventory_service = InventoryService(db_session)
        adjustment = StockAdjustment(
            product_id=product.id,
            quantity=-25,
            reason="Sale"
        )
        
        transaction = inventory_service.adjust_stock(adjustment)
        
        assert transaction.quantity == -25
        assert transaction.previous_stock == 100
        assert transaction.new_stock == 75
        assert transaction.transaction_type == "removal"
        
        # Verify product stock was updated
        updated_product = product_service.get_product_by_id(product.id)
        assert updated_product.current_stock == 75
    
    def test_adjust_stock_zero_quantity(self, db_session):
        """Test adjustment with zero quantity."""
        # Create a product
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=50, reorder_threshold=20
        ))
        
        # Adjust with zero
        inventory_service = InventoryService(db_session)
        adjustment = StockAdjustment(
            product_id=product.id,
            quantity=0,
            reason="Inventory count correction"
        )
        
        transaction = inventory_service.adjust_stock(adjustment)
        
        assert transaction.transaction_type == "adjustment"
        assert transaction.new_stock == 50
    
    def test_adjust_stock_insufficient(self, db_session):
        """Test that removing more stock than available raises InsufficientStockException."""
        # Create a product with limited stock
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=10, reorder_threshold=5
        ))
        
        # Try to remove more than available
        inventory_service = InventoryService(db_session)
        adjustment = StockAdjustment(
            product_id=product.id,
            quantity=-20,
            reason="Sale"
        )
        
        with pytest.raises(InsufficientStockException) as exc_info:
            inventory_service.adjust_stock(adjustment)
        
        assert "Insufficient stock" in str(exc_info.value)
        
        # Verify stock was not changed
        product = product_service.get_product_by_id(product.id)
        assert product.current_stock == 10
    
    def test_adjust_stock_product_not_found(self, db_session):
        """Test that adjusting stock for non-existent product raises ProductNotFoundException."""
        inventory_service = InventoryService(db_session)
        non_existent_id = uuid4()
        
        adjustment = StockAdjustment(
            product_id=non_existent_id,
            quantity=10,
            reason="Test"
        )
        
        with pytest.raises(ProductNotFoundException):
            inventory_service.adjust_stock(adjustment)
    
    def test_adjust_stock_with_user_id(self, db_session):
        """Test stock adjustment with user tracking."""
        # Create a product
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=50, reorder_threshold=20
        ))
        
        # Adjust stock with user_id
        inventory_service = InventoryService(db_session)
        user_id = uuid4()
        adjustment = StockAdjustment(
            product_id=product.id,
            quantity=10,
            reason="Manual adjustment"
        )
        
        transaction = inventory_service.adjust_stock(adjustment, user_id=user_id)
        
        assert transaction.user_id == user_id
    
    def test_get_movements(self, db_session):
        """Test retrieving all stock movements."""
        # Create products and transactions
        product_service = ProductService(db_session)
        inventory_service = InventoryService(db_session)
        
        product1 = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Product 1", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        product2 = product_service.create_product(ProductCreate(
            sku="TEST-002", name="Product 2", category="Test",
            current_stock=50, reorder_threshold=10
        ))
        
        # Create multiple transactions
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product1.id, quantity=10, reason="Restock"
        ))
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product2.id, quantity=-5, reason="Sale"
        ))
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product1.id, quantity=-20, reason="Sale"
        ))
        
        # Get all movements
        movements = inventory_service.get_movements()
        
        assert len(movements) == 3
        # Should be ordered by most recent first
        assert movements[0].quantity == -20
        assert movements[1].quantity == -5
        assert movements[2].quantity == 10
    
    def test_get_movements_filtered_by_product(self, db_session):
        """Test retrieving movements filtered by product."""
        # Create products and transactions
        product_service = ProductService(db_session)
        inventory_service = InventoryService(db_session)
        
        product1 = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Product 1", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        product2 = product_service.create_product(ProductCreate(
            sku="TEST-002", name="Product 2", category="Test",
            current_stock=50, reorder_threshold=10
        ))
        
        # Create transactions for both products
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product1.id, quantity=10, reason="Restock"
        ))
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product2.id, quantity=-5, reason="Sale"
        ))
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product1.id, quantity=-20, reason="Sale"
        ))
        
        # Get movements for product1 only
        movements = inventory_service.get_movements(product_id=product1.id)
        
        assert len(movements) == 2
        assert all(m.product_id == product1.id for m in movements)
    
    def test_get_movements_pagination(self, db_session):
        """Test movement pagination."""
        # Create product and multiple transactions
        product_service = ProductService(db_session)
        inventory_service = InventoryService(db_session)
        
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        
        # Create 10 transactions
        for i in range(10):
            inventory_service.adjust_stock(StockAdjustment(
                product_id=product.id, quantity=1, reason=f"Transaction {i}"
            ))
        
        # Get first page
        page1 = inventory_service.get_movements(skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2 = inventory_service.get_movements(skip=5, limit=5)
        assert len(page2) == 5
        
        # Ensure different transactions
        page1_ids = {m.id for m in page1}
        page2_ids = {m.id for m in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_get_product_history(self, db_session):
        """Test retrieving stock history for a specific product."""
        # Create products
        product_service = ProductService(db_session)
        inventory_service = InventoryService(db_session)
        
        product1 = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Product 1", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        product2 = product_service.create_product(ProductCreate(
            sku="TEST-002", name="Product 2", category="Test",
            current_stock=50, reorder_threshold=10
        ))
        
        # Create transactions for both products
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product1.id, quantity=10, reason="Restock"
        ))
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product2.id, quantity=-5, reason="Sale"
        ))
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product1.id, quantity=-20, reason="Sale"
        ))
        
        # Get history for product1
        history = inventory_service.get_product_history(product1.id)
        
        assert len(history) == 2
        assert all(h.product_id == product1.id for h in history)
    
    def test_get_product_history_not_found(self, db_session):
        """Test that getting history for non-existent product raises ProductNotFoundException."""
        inventory_service = InventoryService(db_session)
        non_existent_id = uuid4()
        
        with pytest.raises(ProductNotFoundException):
            inventory_service.get_product_history(non_existent_id)
    
    def test_get_current_stock(self, db_session):
        """Test getting current stock level."""
        # Create product
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=75, reorder_threshold=20
        ))
        
        # Get current stock
        inventory_service = InventoryService(db_session)
        stock = inventory_service.get_current_stock(product.id)
        
        assert stock == 75
    
    def test_get_current_stock_not_found(self, db_session):
        """Test that getting stock for non-existent product raises ProductNotFoundException."""
        inventory_service = InventoryService(db_session)
        non_existent_id = uuid4()
        
        with pytest.raises(ProductNotFoundException):
            inventory_service.get_current_stock(non_existent_id)
    
    def test_multiple_adjustments_sequential(self, db_session):
        """Test multiple sequential stock adjustments."""
        # Create product
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=50, reorder_threshold=20
        ))
        
        inventory_service = InventoryService(db_session)
        
        # First adjustment: add 30
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product.id, quantity=30, reason="Restock"
        ))
        
        # Second adjustment: remove 20
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product.id, quantity=-20, reason="Sale"
        ))
        
        # Third adjustment: add 10
        inventory_service.adjust_stock(StockAdjustment(
            product_id=product.id, quantity=10, reason="Return"
        ))
        
        # Verify final stock
        final_stock = inventory_service.get_current_stock(product.id)
        assert final_stock == 70  # 50 + 30 - 20 + 10
        
        # Verify all transactions recorded
        history = inventory_service.get_product_history(product.id)
        assert len(history) == 3
