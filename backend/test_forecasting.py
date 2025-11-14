"""Test script for Prophet-based forecasting model."""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ml.forecasting import ForecastingModel, ModelTrainingException


def create_sample_data(days=60, initial_stock=1000, daily_consumption=10):
    """Create sample stock data with declining trend."""
    dates = [datetime.now().date() - timedelta(days=i) for i in range(days, 0, -1)]
    stock_levels = [initial_stock - (i * daily_consumption) + np.random.randint(-20, 20) 
                    for i in range(days)]
    
    df = pd.DataFrame({
        'date': dates,
        'stock_level': stock_levels
    })
    
    return df


def test_prophet_model():
    """Test Prophet model training and prediction."""
    print("=" * 60)
    print("Testing Prophet Model")
    print("=" * 60)
    
    # Create sample data (60 days, sufficient for Prophet)
    df = create_sample_data(days=60, initial_stock=1000, daily_consumption=10)
    print(f"\nCreated sample data: {len(df)} days")
    print(f"Stock range: {df['stock_level'].min():.0f} to {df['stock_level'].max():.0f}")
    
    # Initialize and train model
    model = ForecastingModel()
    
    try:
        print("\nTraining Prophet model...")
        metrics = model.train(df, product_id="test-product-prophet")
        
        print(f"\n✓ Training successful!")
        print(f"  Model type: {metrics['model_type']}")
        print(f"  MAE: {metrics['mae']:.2f}")
        print(f"  RMSE: {metrics['rmse']:.2f}")
        print(f"  MAPE: {metrics['mape']:.2f}%")
        print(f"  Training samples: {metrics['training_samples']}")
        
        # Make prediction
        print("\nMaking prediction...")
        current_stock = int(df['stock_level'].iloc[-1])
        depletion_date, confidence, forecast_data, consumption_rate = model.predict(
            current_stock=current_stock,
            forecast_days=90
        )
        
        print(f"\n✓ Prediction successful!")
        print(f"  Current stock: {current_stock}")
        print(f"  Predicted depletion date: {depletion_date}")
        print(f"  Confidence score: {confidence:.4f}")
        print(f"  Daily consumption rate: {consumption_rate:.2f}")
        print(f"  Forecast points: {len(forecast_data)}")
        
        # Show first few forecast points
        print("\n  First 5 forecast points:")
        for i, point in enumerate(forecast_data[:5]):
            print(f"    {point['date']}: {point['predicted_stock']:.2f} "
                  f"(±{point['upper_bound'] - point['predicted_stock']:.2f})")
        
        # Test model save/load
        print("\nTesting model persistence...")
        model_version = model.save("test-product-prophet")
        print(f"  ✓ Model saved: {model_version}")
        
        new_model = ForecastingModel()
        loaded = new_model.load("test-product-prophet")
        print(f"  ✓ Model loaded: {loaded}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_linear_model():
    """Test linear regression model training and prediction."""
    print("\n" + "=" * 60)
    print("Testing Linear Regression Model (Fallback)")
    print("=" * 60)
    
    # Create sample data (15 days, not enough for Prophet)
    df = create_sample_data(days=15, initial_stock=500, daily_consumption=15)
    print(f"\nCreated sample data: {len(df)} days")
    print(f"Stock range: {df['stock_level'].min():.0f} to {df['stock_level'].max():.0f}")
    
    # Initialize and train model
    model = ForecastingModel()
    
    try:
        print("\nTraining linear regression model...")
        metrics = model.train(df, product_id="test-product-linear")
        
        print(f"\n✓ Training successful!")
        print(f"  Model type: {metrics['model_type']}")
        print(f"  MAE: {metrics['mae']:.2f}")
        print(f"  RMSE: {metrics['rmse']:.2f}")
        print(f"  MAPE: {metrics['mape']:.2f}%")
        print(f"  Slope: {metrics['slope']:.4f}")
        print(f"  Training samples: {metrics['training_samples']}")
        
        # Make prediction
        print("\nMaking prediction...")
        current_stock = int(df['stock_level'].iloc[-1])
        depletion_date, confidence, forecast_data, consumption_rate = model.predict(
            current_stock=current_stock,
            forecast_days=60
        )
        
        print(f"\n✓ Prediction successful!")
        print(f"  Current stock: {current_stock}")
        print(f"  Predicted depletion date: {depletion_date}")
        print(f"  Confidence score: {confidence:.4f}")
        print(f"  Daily consumption rate: {consumption_rate:.2f}")
        print(f"  Forecast points: {len(forecast_data)}")
        
        # Show first few forecast points
        print("\n  First 5 forecast points:")
        for i, point in enumerate(forecast_data[:5]):
            print(f"    {point['date']}: {point['predicted_stock']:.2f} "
                  f"(±{point['upper_bound'] - point['predicted_stock']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_insufficient_data():
    """Test handling of insufficient data."""
    print("\n" + "=" * 60)
    print("Testing Insufficient Data Handling")
    print("=" * 60)
    
    # Create sample data (only 5 days, not enough)
    df = create_sample_data(days=5, initial_stock=100, daily_consumption=5)
    print(f"\nCreated sample data: {len(df)} days (insufficient)")
    
    model = ForecastingModel()
    
    try:
        print("\nAttempting to train model...")
        metrics = model.train(df, product_id="test-product-insufficient")
        print(f"\n✗ Should have raised exception but didn't!")
        return False
        
    except ModelTrainingException as e:
        print(f"\n✓ Correctly raised ModelTrainingException:")
        print(f"  {str(e)}")
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        return False


def test_prophet_fallback():
    """Test Prophet fallback to linear regression."""
    print("\n" + "=" * 60)
    print("Testing Prophet Fallback to Linear Regression")
    print("=" * 60)
    
    # Create problematic data that might cause Prophet to fail
    # (e.g., all zeros or constant values)
    df = pd.DataFrame({
        'date': [datetime.now().date() - timedelta(days=i) for i in range(10, 0, -1)],
        'stock_level': [100] * 10  # Constant values
    })
    print(f"\nCreated problematic data: {len(df)} days (constant values)")
    
    model = ForecastingModel()
    
    try:
        print("\nTraining model (should fallback to linear)...")
        metrics = model.train(df, product_id="test-product-fallback")
        
        print(f"\n✓ Training successful with fallback!")
        print(f"  Model type: {metrics['model_type']}")
        
        if metrics['model_type'] == 'linear':
            print("  ✓ Correctly fell back to linear regression")
            return True
        else:
            print("  ✗ Did not fallback as expected")
            return False
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PROPHET-BASED FORECASTING MODEL TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Prophet Model", test_prophet_model()))
    results.append(("Linear Model", test_linear_model()))
    results.append(("Insufficient Data", test_insufficient_data()))
    results.append(("Prophet Fallback", test_prophet_fallback()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)
