"""ML Prediction API endpoints."""

import logging
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.cache import cache, cache_key_prediction, cache_key_batch_predictions, invalidate_prediction_cache
from app.models.user import User
from app.ml.prediction_service import MLPredictionService, InsufficientDataException
from app.schemas.prediction import (
    PredictionResult,
    TrainingRequest,
    TrainingResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    DataSummaryResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])


def get_prediction_service(db: Session = Depends(get_db)) -> MLPredictionService:
    """Dependency to get MLPredictionService instance."""
    return MLPredictionService(db)


@router.get("/{product_id}", response_model=Dict[str, Any])
async def get_prediction(
    product_id: UUID,
    forecast_days: int = Query(90, ge=7, le=365, description="Number of days to forecast"),
    use_cache: bool = Query(True, description="Whether to use cached results"),
    current_user: User = Depends(get_current_user),
    prediction_service: MLPredictionService = Depends(get_prediction_service)
) -> Dict[str, Any]:
    """
    Get stock depletion prediction for a specific product.
    
    Returns prediction with depletion date, confidence score, and forecast data.
    Results are cached for 1 hour by default.
    
    - **product_id**: UUID of the product
    - **forecast_days**: Number of days to forecast (7-365)
    - **use_cache**: Whether to use cached results (default: true)
    
    **Returns:**
    - predicted_depletion_date: Date when stock is predicted to run out
    - confidence_score: Confidence level of the prediction (0.0-1.0)
    - daily_consumption_rate: Average daily consumption rate
    - forecast: List of forecasted stock levels
    - model_version: Version of the trained model
    - model_type: Type of model used (prophet, linear, etc.)
    
    **Errors:**
    - 404: Product not found
    - 400: Insufficient data for prediction
    """
    cache_key = cache_key_prediction(str(product_id))
    
    # Try to get from cache if enabled
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached prediction for product {product_id}")
            return cached_result
    
    # Generate prediction
    try:
        result = prediction_service.predict_depletion(
            product_id=product_id,
            forecast_days=forecast_days
        )
        
        # Cache the result for 1 hour (3600 seconds)
        cache.set(cache_key, result, ttl=3600)
        
        logger.info(f"Generated and cached prediction for product {product_id}")
        return result
        
    except InsufficientDataException as e:
        logger.warning(f"Insufficient data for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Insufficient data for prediction",
                "message": str(e),
                "product_id": str(product_id)
            }
        )
    except Exception as e:
        logger.error(f"Error generating prediction for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Prediction generation failed",
                "message": str(e),
                "product_id": str(product_id)
            }
        )


@router.post("/train", response_model=TrainingResponse, status_code=status.HTTP_200_OK)
async def train_model(
    training_request: TrainingRequest,
    current_user: User = Depends(get_current_user),
    prediction_service: MLPredictionService = Depends(get_prediction_service)
) -> TrainingResponse:
    """
    Train or retrain a forecasting model for a specific product.
    
    This endpoint triggers model training using historical stock data.
    Training may take several seconds depending on data volume.
    
    - **product_id**: UUID of the product to train model for
    - **force_retrain**: Force retraining even if a recent model exists
    
    **Returns:**
    - success: Whether training was successful
    - message: Status message
    - model_version: Version identifier of the trained model
    - training_metrics: Metrics about the training process
    - trained_at: Timestamp when training completed
    
    **Errors:**
    - 404: Product not found
    - 400: Insufficient data for training (requires minimum 30 days)
    - 500: Model training failed
    """
    try:
        result = prediction_service.train_model(
            product_id=training_request.product_id,
            force_retrain=training_request.force_retrain
        )
        
        # Invalidate cache for this product after training
        invalidate_prediction_cache(str(training_request.product_id))
        
        logger.info(f"Model training completed for product {training_request.product_id}")
        
        return TrainingResponse(**result)
        
    except InsufficientDataException as e:
        logger.warning(f"Insufficient data for training product {training_request.product_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Insufficient data for training",
                "message": str(e),
                "product_id": str(training_request.product_id),
                "min_required_days": 30
            }
        )
    except Exception as e:
        logger.error(f"Model training failed for product {training_request.product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Model training failed",
                "message": str(e),
                "product_id": str(training_request.product_id)
            }
        )


@router.get("/batch", response_model=BatchPredictionResponse)
async def batch_predictions(
    product_ids: List[UUID] = Query(None, description="List of product IDs (if empty, predict all)"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score"),
    use_cache: bool = Query(True, description="Whether to use cached results"),
    current_user: User = Depends(get_current_user),
    prediction_service: MLPredictionService = Depends(get_prediction_service)
) -> BatchPredictionResponse:
    """
    Generate predictions for multiple products in batch.
    
    If no product IDs are provided, generates predictions for all products
    with sufficient historical data (minimum 30 days).
    
    Results are cached for 1 hour by default.
    
    - **product_ids**: Optional list of product UUIDs (if empty, predict all eligible products)
    - **min_confidence**: Minimum confidence score to include in results (0.0-1.0)
    - **use_cache**: Whether to use cached results (default: true)
    
    **Returns:**
    - total_products: Number of products processed
    - successful_predictions: Number of successful predictions
    - failed_predictions: Number of failed predictions
    - predictions: List of prediction results
    - errors: List of errors for failed predictions (if any)
    
    **Note:** This operation may take several seconds for large product catalogs.
    """
    cache_key = cache_key_batch_predictions()
    
    # Try to get from cache if enabled and no specific product IDs provided
    if use_cache and not product_ids:
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached batch predictions")
            return BatchPredictionResponse(**cached_result)
    
    # Generate batch predictions
    try:
        result = prediction_service.batch_predict(
            product_ids=product_ids if product_ids else None,
            min_confidence=min_confidence
        )
        
        # Cache the result for 1 hour if no specific product IDs were provided
        if not product_ids:
            cache.set(cache_key, result, ttl=3600)
        
        logger.info(
            f"Batch prediction completed: {result['successful_predictions']} successful, "
            f"{result['failed_predictions']} failed"
        )
        
        return BatchPredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Batch prediction failed",
                "message": str(e)
            }
        )


@router.get("/{product_id}/data-summary", response_model=DataSummaryResponse)
async def get_data_summary(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    prediction_service: MLPredictionService = Depends(get_prediction_service)
) -> DataSummaryResponse:
    """
    Get a summary of available historical data for a product.
    
    Useful for checking if a product has sufficient data for training
    before attempting to train a model or generate predictions.
    
    - **product_id**: UUID of the product
    
    **Returns:**
    - has_sufficient_data: Whether product has enough data for training
    - days_of_data: Number of days of historical data available
    - min_required_days: Minimum days required for training
    - total_transactions: Total number of inventory transactions
    - date_range: Start and end dates of available data
    - stock_statistics: Min, max, mean, and current stock levels
    """
    try:
        summary = prediction_service.get_data_summary(product_id)
        return DataSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting data summary for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get data summary",
                "message": str(e),
                "product_id": str(product_id)
            }
        )


@router.delete("/{product_id}/cache", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_cache(
    product_id: UUID,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Invalidate cached prediction for a specific product.
    
    Use this endpoint after making significant changes to a product's
    inventory data to ensure fresh predictions are generated.
    
    - **product_id**: UUID of the product
    """
    invalidate_prediction_cache(str(product_id))
    logger.info(f"Cache invalidated for product {product_id}")
    return None
