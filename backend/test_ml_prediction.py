"""Test ML prediction service foundation."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing ML Prediction Service Foundation...")
print("=" * 60)

def test_imports():
    """Test that all ML modules can be imported."""
    
    print("\n--- Test 1: Import ML modules ---")
    
    # Test ML service import
    from app.ml.prediction_service import MLPredictionService, InsufficientDataException
    print("✓ MLPredictionService imported successfully")
    
    # Test ML utils import
    from app.ml.utils import (
        ensure_model_directory,
        get_model_path,
        save_model,
        load_model,
        delete_model,
        get_model_metadata
    )
    print("✓ ML utils imported successfully")
    
    # Test prediction schemas import
    from app.schemas.prediction import (
        DataSummaryResponse,
        PredictionMetadata,
        ForecastPoint,
        PredictionResult,
        MLPredictionResponse,
        TrainingRequest,
        TrainingResponse,
        BatchPredictionRequest,
        BatchPredictionResponse
    )
    print("✓ Prediction schemas imported successfully")
    
    return True


def test_model_storage():
    """Test model storage utilities."""
    
    print("\n--- Test 2: Model storage utilities ---")
    
    from app.ml.utils import (
        ensure_model_directory,
        get_model_path,
        save_model,
        load_model,
        delete_model,
        get_model_metadata
    )
    from uuid import uuid4
    
    # Ensure model directory exists
    model_dir = ensure_model_directory()
    print(f"✓ Model directory created/verified: {model_dir}")
    assert model_dir.exists(), "Model directory should exist"
    
    # Test model path generation
    test_product_id = str(uuid4())
    model_path = get_model_path(test_product_id, "v1.0")
    print(f"✓ Model path generated: {model_path}")
    assert "model_" in str(model_path), "Model path should contain 'model_'"
    assert test_product_id in str(model_path), "Model path should contain product ID"
    
    # Test model save/load
    dummy_model = {"type": "test_model", "version": "1.0", "data": [1, 2, 3, 4, 5]}
    saved_path = save_model(dummy_model, test_product_id, "v1.0")
    print(f"✓ Model saved to: {saved_path}")
    assert saved_path.exists(), "Saved model file should exist"
    
    loaded_model = load_model(test_product_id, "v1.0")
    print(f"✓ Model loaded successfully")
    assert loaded_model == dummy_model, "Loaded model should match saved model"
    
    # Test model metadata
    metadata = get_model_metadata(test_product_id, "v1.0")
    print(f"✓ Model metadata retrieved: {metadata['size_bytes']} bytes")
    assert metadata is not None, "Should have model metadata"
    assert metadata["product_id"] == test_product_id, "Metadata should have correct product_id"
    
    # Test model deletion
    deleted = delete_model(test_product_id, "v1.0")
    print(f"✓ Model deleted successfully")
    assert deleted, "Model should be deleted"
    assert not saved_path.exists(), "Model file should not exist after deletion"
    
    return True


def test_data_preprocessing():
    """Test data preprocessing functions."""
    
    print("\n--- Test 3: Data preprocessing ---")
    
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    from app.ml.prediction_service import MLPredictionService
    
    # Create mock database session (we'll just test preprocessing logic)
    class MockDB:
        pass
    
    ml_service = MLPredictionService(MockDB())
    print("✓ MLPredictionService instantiated")
    
    # Create sample data with missing dates
    dates = []
    stock_levels = []
    base_date = datetime(2024, 1, 1)
    
    # Add data with gaps
    for i in [0, 1, 2, 5, 6, 10, 11, 12, 15]:  # Missing days 3, 4, 7, 8, 9, 13, 14
        dates.append(base_date + timedelta(days=i))
        stock_levels.append(100 - (i * 5))
    
    df = pd.DataFrame({
        "date": dates,
        "stock_level": stock_levels,
        "quantity_change": [-5] * len(dates)
    })
    
    print(f"✓ Created sample data with {len(df)} records and missing dates")
    
    # Test preprocessing
    df_processed = ml_service.preprocess_data(df, fill_missing_dates=True)
    print(f"✓ Preprocessed data: {len(df_processed)} records (filled missing dates)")
    
    # Check that missing dates were filled
    assert len(df_processed) > len(df), "Should have more records after filling missing dates"
    assert len(df_processed) == 16, f"Should have 16 days total, got {len(df_processed)}"
    
    # Check that features were added
    assert "day_of_week" in df_processed.columns, "Should have day_of_week feature"
    assert "stock_change" in df_processed.columns, "Should have stock_change feature"
    assert "month" in df_processed.columns, "Should have month feature"
    print("✓ Features added: day_of_week, stock_change, month, etc.")
    
    return True


def test_schemas():
    """Test prediction schemas."""
    
    print("\n--- Test 4: Prediction schemas ---")
    
    from app.schemas.prediction import (
        DataSummaryResponse,
        TrainingRequest,
        PredictionResult
    )
    from uuid import uuid4
    from datetime import datetime, date
    
    # Test DataSummaryResponse
    summary = DataSummaryResponse(
        product_id=str(uuid4()),
        has_sufficient_data=True,
        days_of_data=45,
        min_required_days=30
    )
    print(f"✓ DataSummaryResponse created: {summary.days_of_data} days")
    
    # Test TrainingRequest
    training_req = TrainingRequest(
        product_id=uuid4(),
        force_retrain=False
    )
    print(f"✓ TrainingRequest created: force_retrain={training_req.force_retrain}")
    
    # Test PredictionResult
    prediction = PredictionResult(
        product_id=str(uuid4()),
        predicted_depletion_date=date(2024, 12, 31),
        confidence_score=0.85,
        daily_consumption_rate=5.2,
        model_version="v1.0",
        created_at=datetime.utcnow()
    )
    print(f"✓ PredictionResult created: confidence={prediction.confidence_score}")
    
    return True


def run_all_tests():
    """Run all tests."""
    
    try:
        test_imports()
        test_model_storage()
        test_data_preprocessing()
        test_schemas()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nML Prediction Service Foundation is working correctly:")
        print("  ✓ All modules import successfully")
        print("  ✓ Model storage and persistence utilities work")
        print("  ✓ Data preprocessing functions work")
        print("  ✓ Prediction schemas validate correctly")
        print("\nReady for next task: Prophet-based forecasting model")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

