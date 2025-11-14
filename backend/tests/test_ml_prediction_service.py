"""Unit tests for MLPredictionService."""

import pytest
import pandas as pd
from datetime import datetime, timedelta, date
from uuid import uuid4
from app.ml.prediction_service import MLPredictionService, InsufficientDataException
from app.services.product_service import ProductService
from app.services.inventory_service import InventoryService
from app.schemas.product import ProductCreate
from app.schemas.inventory import StockAdjustment


class TestMLPredictionService:
    """Test cases for MLPredictionService data preparation methods."""
    
    def test_fetch_historical_data(self, db_session):
        """Test fetching historical transaction data."""
        # Create product and transactions
        product_service = ProductService(db_session)
        inventory_service = InventoryService(db_session)
        
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        
        # Create transactions over multiple days
        for i in range(5):
            inventory_service.adjust_stock(StockAdjustment(
                product_id=product.id, quantity=-10, reason=f"Day {i}"
            ))
        
        # Fetch historical data
        ml_service = MLPredictionService(db_session)
        df = ml_service.fetch_historical_data(product.id)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "date" in df.columns
        assert "stock_level" in df.columns
        assert "quantity_change" in df.columns

    
    def test_fetch_historical_data_no_transactions(self, db_session):
        """Test that fetching data with no transactions raises InsufficientDataException."""
        # Create product without transactions
        product_service = ProductService(db_session)
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        
        ml_service = MLPredictionService(db_session)
        
        with pytest.raises(InsufficientDataException):
            ml_service.fetch_historical_data(product.id)
    
    def test_preprocess_data_fill_missing_dates(self, db_session):
        """Test preprocessing fills missing dates."""
        ml_service = MLPredictionService(db_session)
        
        # Create sample data with gaps
        data = {
            "date": [date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 5)],
            "stock_level": [100, 90, 80],
            "quantity_change": [-10, -10, -10]
        }
        df = pd.DataFrame(data)
        
        # Preprocess
        df_processed = ml_service.preprocess_data(df, fill_missing_dates=True)
        
        # Should have 5 days (Jan 1-5)
        assert len(df_processed) == 5
        assert df_processed["stock_level"].isna().sum() == 0
    
    def test_preprocess_data_no_fill(self, db_session):
        """Test preprocessing without filling missing dates."""
        ml_service = MLPredictionService(db_session)
        
        data = {
            "date": [date(2024, 1, 1), date(2024, 1, 3)],
            "stock_level": [100, 90],
            "quantity_change": [-10, -10]
        }
        df = pd.DataFrame(data)
        
        df_processed = ml_service.preprocess_data(df, fill_missing_dates=False)
        
        # Should still have 2 days
        assert len(df_processed) == 2

    
    def test_add_features(self, db_session):
        """Test that additional features are added to data."""
        ml_service = MLPredictionService(db_session)
        
        data = {
            "date": pd.date_range(start="2024-01-01", periods=10, freq="D"),
            "stock_level": [100 - i*5 for i in range(10)]
        }
        df = pd.DataFrame(data)
        
        df_processed = ml_service._add_features(df)
        
        assert "day_of_week" in df_processed.columns
        assert "day_of_month" in df_processed.columns
        assert "month" in df_processed.columns
        assert "stock_change" in df_processed.columns
    
    def test_has_sufficient_data_true(self, db_session):
        """Test checking for sufficient data returns True when enough data exists."""
        # Create product with 35 days of transactions
        product_service = ProductService(db_session)
        inventory_service = InventoryService(db_session)
        
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        
        # Create transactions spanning 35 days
        base_date = datetime.utcnow() - timedelta(days=35)
        for i in range(35):
            # Manually create transaction with specific date
            from app.models.inventory_transaction import InventoryTransaction
            txn = InventoryTransaction(
                product_id=product.id,
                transaction_type="removal",
                quantity=-1,
                previous_stock=100-i,
                new_stock=99-i,
                reason="Daily sale",
                created_at=base_date + timedelta(days=i)
            )
            db_session.add(txn)
        db_session.commit()
        
        ml_service = MLPredictionService(db_session)
        has_sufficient, days = ml_service.has_sufficient_data(product.id)
        
        assert has_sufficient is True
        assert days >= 30
    
    def test_has_sufficient_data_false(self, db_session):
        """Test checking for sufficient data returns False when not enough data."""
        # Create product with only 10 days of transactions
        product_service = ProductService(db_session)
        inventory_service = InventoryService(db_session)
        
        product = product_service.create_product(ProductCreate(
            sku="TEST-001", name="Test Product", category="Test",
            current_stock=100, reorder_threshold=20
        ))
        
        # Create only 10 transactions
        for i in range(10):
            inventory_service.adjust_stock(StockAdjustment(
                product_id=product.id, quantity=-1, reason=f"Day {i}"
            ))
        
        ml_service = MLPredictionService(db_session)
        has_sufficient, days = ml_service.has_sufficient_data(product.id)
        
        assert has_sufficient is False
