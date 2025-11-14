"""Unit tests for ProductService."""

import pytest
from uuid import uuid4
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate
from app.models.product import Product
from app.core.exceptions import ProductNotFoundException, ValidationException


class TestProductService:
    """Test cases for ProductService methods."""
    
    def test_create_product(self, db_session):
        """Test creating a new product."""
        service = ProductService(db_session)
        product_data = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            current_stock=100,
            reorder_threshold=20,
            barcode="123456789",
            unit_cost=29.99
        )
        
        product = service.create_product(product_data)
        
        assert product.id is not None
        assert product.sku == "TEST-001"
        assert product.name == "Test Product"
        assert product.category == "Electronics"
        assert product.current_stock == 100
        assert product.reorder_threshold == 20
        assert product.barcode == "123456789"
        assert float(product.unit_cost) == 29.99
    
    def test_create_product_duplicate_sku(self, db_session):
        """Test that creating a product with duplicate SKU raises ValidationException."""
        service = ProductService(db_session)
        product_data = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            current_stock=100,
            reorder_threshold=20
        )
        
        # Create first product
        service.create_product(product_data)
        
        # Try to create duplicate
        with pytest.raises(ValidationException) as exc_info:
            service.create_product(product_data)
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_product_duplicate_barcode(self, db_session):
        """Test that creating a product with duplicate barcode raises ValidationException."""
        service = ProductService(db_session)
        
        # Create first product
        product_data1 = ProductCreate(
            sku="TEST-001",
            name="Product 1",
            category="Electronics",
            current_stock=100,
            reorder_threshold=20,
            barcode="123456789"
        )
        service.create_product(product_data1)
        
        # Try to create product with same barcode
        product_data2 = ProductCreate(
            sku="TEST-002",
            name="Product 2",
            category="Electronics",
            current_stock=50,
            reorder_threshold=10,
            barcode="123456789"
        )
        
        with pytest.raises(ValidationException) as exc_info:
            service.create_product(product_data2)
        
        assert "barcode" in str(exc_info.value).lower()
    
    def test_get_product_by_id(self, db_session):
        """Test retrieving a product by ID."""
        service = ProductService(db_session)
        product_data = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            current_stock=100,
            reorder_threshold=20
        )
        
        created_product = service.create_product(product_data)
        retrieved_product = service.get_product_by_id(created_product.id)
        
        assert retrieved_product.id == created_product.id
        assert retrieved_product.sku == "TEST-001"
        assert retrieved_product.name == "Test Product"
    
    def test_get_product_by_id_not_found(self, db_session):
        """Test that getting non-existent product raises ProductNotFoundException."""
        service = ProductService(db_session)
        non_existent_id = uuid4()
        
        with pytest.raises(ProductNotFoundException):
            service.get_product_by_id(non_existent_id)
    
    def test_get_product_by_sku(self, db_session):
        """Test retrieving a product by SKU."""
        service = ProductService(db_session)
        product_data = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            current_stock=100,
            reorder_threshold=20
        )
        
        service.create_product(product_data)
        product = service.get_product_by_sku("TEST-001")
        
        assert product is not None
        assert product.sku == "TEST-001"
    
    def test_get_product_by_sku_not_found(self, db_session):
        """Test that getting product by non-existent SKU returns None."""
        service = ProductService(db_session)
        product = service.get_product_by_sku("NON-EXISTENT")
        
        assert product is None
    
    def test_get_all_products(self, db_session):
        """Test retrieving all products."""
        service = ProductService(db_session)
        
        # Create multiple products
        for i in range(3):
            product_data = ProductCreate(
                sku=f"TEST-{i:03d}",
                name=f"Product {i}",
                category="Electronics",
                current_stock=100,
                reorder_threshold=20
            )
            service.create_product(product_data)
        
        products = service.get_all_products()
        
        assert len(products) == 3
    
    def test_get_all_products_with_category_filter(self, db_session):
        """Test retrieving products filtered by category."""
        service = ProductService(db_session)
        
        # Create products in different categories
        service.create_product(ProductCreate(
            sku="ELEC-001", name="Electronics Product", category="Electronics",
            current_stock=100, reorder_threshold=20
        ))
        service.create_product(ProductCreate(
            sku="FOOD-001", name="Food Product", category="Food",
            current_stock=50, reorder_threshold=10
        ))
        service.create_product(ProductCreate(
            sku="ELEC-002", name="Another Electronics", category="Electronics",
            current_stock=75, reorder_threshold=15
        ))
        
        electronics = service.get_all_products(category="Electronics")
        
        assert len(electronics) == 2
        assert all(p.category == "Electronics" for p in electronics)
    
    def test_get_all_products_with_search(self, db_session):
        """Test retrieving products with search filter."""
        service = ProductService(db_session)
        
        # Create products
        service.create_product(ProductCreate(
            sku="TEST-001", name="Laptop Computer", category="Electronics",
            current_stock=100, reorder_threshold=20
        ))
        service.create_product(ProductCreate(
            sku="TEST-002", name="Desktop Computer", category="Electronics",
            current_stock=50, reorder_threshold=10
        ))
        service.create_product(ProductCreate(
            sku="TEST-003", name="Mouse", category="Accessories",
            current_stock=200, reorder_threshold=50
        ))
        
        # Search for "computer"
        results = service.get_all_products(search="computer")
        
        assert len(results) == 2
        assert all("computer" in p.name.lower() for p in results)
    
    def test_get_all_products_pagination(self, db_session):
        """Test product pagination."""
        service = ProductService(db_session)
        
        # Create 10 products
        for i in range(10):
            service.create_product(ProductCreate(
                sku=f"TEST-{i:03d}", name=f"Product {i}", category="Test",
                current_stock=100, reorder_threshold=20
            ))
        
        # Get first page
        page1 = service.get_all_products(skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2 = service.get_all_products(skip=5, limit=5)
        assert len(page2) == 5
        
        # Ensure different products
        page1_ids = {p.id for p in page1}
        page2_ids = {p.id for p in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_update_product(self, db_session):
        """Test updating a product."""
        service = ProductService(db_session)
        
        # Create product
        product_data = ProductCreate(
            sku="TEST-001", name="Original Name", category="Electronics",
            current_stock=100, reorder_threshold=20
        )
        product = service.create_product(product_data)
        
        # Update product
        update_data = ProductUpdate(
            name="Updated Name",
            current_stock=150
        )
        updated_product = service.update_product(product.id, update_data)
        
        assert updated_product.name == "Updated Name"
        assert updated_product.current_stock == 150
        assert updated_product.sku == "TEST-001"  # Unchanged
    
    def test_update_product_not_found(self, db_session):
        """Test that updating non-existent product raises ProductNotFoundException."""
        service = ProductService(db_session)
        non_existent_id = uuid4()
        
        update_data = ProductUpdate(name="Updated Name")
        
        with pytest.raises(ProductNotFoundException):
            service.update_product(non_existent_id, update_data)
    
    def test_update_product_duplicate_barcode(self, db_session):
        """Test that updating to duplicate barcode raises ValidationException."""
        service = ProductService(db_session)
        
        # Create two products
        product1 = service.create_product(ProductCreate(
            sku="TEST-001", name="Product 1", category="Test",
            current_stock=100, reorder_threshold=20, barcode="111111"
        ))
        product2 = service.create_product(ProductCreate(
            sku="TEST-002", name="Product 2", category="Test",
            current_stock=50, reorder_threshold=10, barcode="222222"
        ))
        
        # Try to update product2 with product1's barcode
        update_data = ProductUpdate(barcode="111111")
        
        with pytest.raises(ValidationException) as exc_info:
            service.update_product(product2.id, update_data)
        
        assert "barcode" in str(exc_info.value).lower()
    
    def test_delete_product(self, db_session):
        """Test deleting a product."""
        service = ProductService(db_session)
        
        # Create product
        product_data = ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=100, reorder_threshold=20
        )
        product = service.create_product(product_data)
        
        # Delete product
        result = service.delete_product(product.id)
        
        assert result is True
        
        # Verify product is deleted
        with pytest.raises(ProductNotFoundException):
            service.get_product_by_id(product.id)
    
    def test_delete_product_not_found(self, db_session):
        """Test that deleting non-existent product raises ProductNotFoundException."""
        service = ProductService(db_session)
        non_existent_id = uuid4()
        
        with pytest.raises(ProductNotFoundException):
            service.delete_product(non_existent_id)
    
    def test_calculate_stock_status_sufficient(self, db_session):
        """Test stock status calculation for sufficient stock."""
        service = ProductService(db_session)
        
        product = Product(
            sku="TEST-001", name="Test", category="Test",
            current_stock=100, reorder_threshold=20
        )
        
        status = service.calculate_stock_status(product)
        
        assert status == "sufficient"
    
    def test_calculate_stock_status_low(self, db_session):
        """Test stock status calculation for low stock."""
        service = ProductService(db_session)
        
        product = Product(
            sku="TEST-001", name="Test", category="Test",
            current_stock=15, reorder_threshold=20
        )
        
        status = service.calculate_stock_status(product)
        
        assert status == "low"
    
    def test_calculate_stock_status_critical(self, db_session):
        """Test stock status calculation for critical (zero) stock."""
        service = ProductService(db_session)
        
        product = Product(
            sku="TEST-001", name="Test", category="Test",
            current_stock=0, reorder_threshold=20
        )
        
        status = service.calculate_stock_status(product)
        
        assert status == "critical"
    
    def test_calculate_stock_status_at_threshold(self, db_session):
        """Test stock status when exactly at reorder threshold."""
        service = ProductService(db_session)
        
        product = Product(
            sku="TEST-001", name="Test", category="Test",
            current_stock=20, reorder_threshold=20
        )
        
        status = service.calculate_stock_status(product)
        
        assert status == "low"
