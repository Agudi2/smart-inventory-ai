"""Celery tasks for ML model training and predictions."""

import logging
from typing import List, Dict, Any
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.ml.prediction_service import MLPredictionService, InsufficientDataException
from app.models.product import Product

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session management."""
    
    _db: Session = None
    
    @property
    def db(self) -> Session:
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Clean up database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.ml_tasks.train_model_for_product",
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def train_model_for_product(self, product_id: str) -> Dict[str, Any]:
    """
    Train ML model for a specific product.
    
    Args:
        product_id: UUID string of the product
    
    Returns:
        Dictionary with training results
    """
    try:
        logger.info(f"Starting model training task for product {product_id}")
        
        # Convert string to UUID
        product_uuid = UUID(product_id)
        
        # Initialize prediction service
        prediction_service = MLPredictionService(self.db)
        
        # Check if product has sufficient data
        has_sufficient, days_of_data = prediction_service.has_sufficient_data(product_uuid)
        
        if not has_sufficient:
            logger.warning(
                f"Product {product_id} has insufficient data for training "
                f"({days_of_data} days, requires {prediction_service.MIN_TRAINING_DAYS})"
            )
            return {
                "product_id": product_id,
                "success": False,
                "message": f"Insufficient data: {days_of_data} days available",
                "skipped": True
            }
        
        # Train the model
        result = prediction_service.train_model(product_uuid, force_retrain=True)
        
        logger.info(f"Model training completed successfully for product {product_id}")
        return result
        
    except InsufficientDataException as e:
        logger.warning(f"Insufficient data for product {product_id}: {str(e)}")
        return {
            "product_id": product_id,
            "success": False,
            "message": str(e),
            "skipped": True
        }
    
    except Exception as e:
        logger.error(f"Error training model for product {product_id}: {str(e)}", exc_info=True)
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying training for product {product_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "product_id": product_id,
            "success": False,
            "message": f"Training failed after {self.max_retries} retries: {str(e)}",
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.ml_tasks.train_all_models",
    time_limit=3600 * 4  # 4 hours
)
def train_all_models(self) -> Dict[str, Any]:
    """
    Train ML models for all products with sufficient historical data.
    
    This task is scheduled to run weekly to keep models up-to-date.
    
    Returns:
        Dictionary with summary of training results
    """
    try:
        logger.info("Starting batch model training for all products")
        
        # Initialize prediction service
        prediction_service = MLPredictionService(self.db)
        
        # Get all products
        products = self.db.query(Product).all()
        logger.info(f"Found {len(products)} total products")
        
        # Track results
        results = {
            "total_products": len(products),
            "trained": 0,
            "skipped": 0,
            "failed": 0,
            "product_results": []
        }
        
        # Train models for each product
        for product in products:
            try:
                # Check if product has sufficient data
                has_sufficient, days_of_data = prediction_service.has_sufficient_data(product.id)
                
                if not has_sufficient:
                    logger.debug(
                        f"Skipping product {product.id} ({product.name}): "
                        f"insufficient data ({days_of_data} days)"
                    )
                    results["skipped"] += 1
                    results["product_results"].append({
                        "product_id": str(product.id),
                        "product_name": product.name,
                        "status": "skipped",
                        "reason": f"Insufficient data ({days_of_data} days)"
                    })
                    continue
                
                # Train the model
                training_result = prediction_service.train_model(product.id, force_retrain=True)
                
                results["trained"] += 1
                results["product_results"].append({
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "status": "success",
                    "model_version": training_result.get("model_version"),
                    "model_type": training_result.get("training_metrics", {}).get("model_type")
                })
                
                logger.info(f"Successfully trained model for product {product.id} ({product.name})")
                
            except Exception as e:
                logger.error(
                    f"Failed to train model for product {product.id} ({product.name}): {str(e)}",
                    exc_info=True
                )
                results["failed"] += 1
                results["product_results"].append({
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info(
            f"Batch training completed. "
            f"Trained: {results['trained']}, "
            f"Skipped: {results['skipped']}, "
            f"Failed: {results['failed']}"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Batch training task failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Batch training task failed"
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.ml_tasks.generate_prediction",
    max_retries=2,
    default_retry_delay=180  # 3 minutes
)
def generate_prediction(self, product_id: str, forecast_days: int = 90) -> Dict[str, Any]:
    """
    Generate stock depletion prediction for a specific product.
    
    Args:
        product_id: UUID string of the product
        forecast_days: Number of days to forecast
    
    Returns:
        Dictionary with prediction results
    """
    try:
        logger.info(f"Generating prediction for product {product_id}")
        
        # Convert string to UUID
        product_uuid = UUID(product_id)
        
        # Initialize prediction service
        prediction_service = MLPredictionService(self.db)
        
        # Generate prediction
        result = prediction_service.predict_depletion(product_uuid, forecast_days=forecast_days)
        
        logger.info(f"Prediction generated successfully for product {product_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating prediction for product {product_id}: {str(e)}", exc_info=True)
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying prediction for product {product_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "product_id": product_id,
            "success": False,
            "error": str(e),
            "message": f"Prediction failed after {self.max_retries} retries"
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.ml_tasks.batch_generate_predictions"
)
def batch_generate_predictions(self, min_confidence: float = 0.0) -> Dict[str, Any]:
    """
    Generate predictions for all products with sufficient data.
    
    Args:
        min_confidence: Minimum confidence score to include in results
    
    Returns:
        Dictionary with batch prediction results
    """
    try:
        logger.info("Starting batch prediction generation")
        
        # Initialize prediction service
        prediction_service = MLPredictionService(self.db)
        
        # Generate batch predictions
        result = prediction_service.batch_predict(min_confidence=min_confidence)
        
        logger.info(
            f"Batch predictions completed. "
            f"Successful: {result['successful_predictions']}, "
            f"Failed: {result['failed_predictions']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Batch prediction task failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Batch prediction task failed"
        }
