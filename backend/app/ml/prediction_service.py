"""ML Prediction Service for stock depletion forecasting."""

import logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.inventory_transaction import InventoryTransaction
from app.models.product import Product
from app.core.exceptions import InventoryException

logger = logging.getLogger(__name__)

# Minimum number of days of historical data required for training
MIN_TRAINING_DAYS = 30


class InsufficientDataException(InventoryException):
    """Raised when there is insufficient data for ML training."""
    pass


class MLPredictionService:
    """
    Service for ML-based stock depletion prediction.
    Handles data preparation, preprocessing, and model management.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the ML prediction service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def fetch_historical_data(self, product_id: UUID) -> pd.DataFrame:
        """
        Fetch historical stock movements for a product and convert to time series format.
        
        Args:
            product_id: UUID of the product
        
        Returns:
            DataFrame with columns: date, stock_level, transaction_count
        
        Raises:
            InsufficientDataException: If no historical data exists
        """
        # Query all transactions for the product, ordered by date
        transactions = (
            self.db.query(InventoryTransaction)
            .filter(InventoryTransaction.product_id == product_id)
            .order_by(InventoryTransaction.created_at)
            .all()
        )
        
        if not transactions:
            raise InsufficientDataException(
                f"No historical data found for product {product_id}"
            )
        
        # Convert to DataFrame
        data = []
        for txn in transactions:
            data.append({
                "date": txn.created_at.date(),
                "stock_level": txn.new_stock,
                "quantity_change": txn.quantity,
                "transaction_type": txn.transaction_type
            })
        
        df = pd.DataFrame(data)
        
        # Aggregate by date (take the last stock level of each day)
        df_agg = df.groupby("date").agg({
            "stock_level": "last",  # Last stock level of the day
            "quantity_change": "sum"  # Total quantity change
        }).reset_index()
        
        # Sort by date
        df_agg = df_agg.sort_values("date").reset_index(drop=True)
        
        logger.info(
            f"Fetched {len(df_agg)} days of historical data for product {product_id}"
        )
        
        return df_agg
    
    def preprocess_data(
        self,
        df: pd.DataFrame,
        fill_missing_dates: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess time series data by handling missing dates and outliers.
        
        Args:
            df: DataFrame with date and stock_level columns
            fill_missing_dates: Whether to fill in missing dates
        
        Returns:
            Preprocessed DataFrame
        """
        if df.empty:
            return df
        
        # Ensure date column is datetime
        df["date"] = pd.to_datetime(df["date"])
        
        # Fill missing dates if requested
        if fill_missing_dates:
            df = self._fill_missing_dates(df)
        
        # Handle outliers in stock levels
        df = self._handle_outliers(df)
        
        # Add additional features
        df = self._add_features(df)
        
        logger.info(f"Preprocessed data: {len(df)} records")
        
        return df
    
    def _fill_missing_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill in missing dates with forward-filled stock levels.
        
        Args:
            df: DataFrame with date and stock_level columns
        
        Returns:
            DataFrame with all dates filled
        """
        if df.empty:
            return df
        
        # Create a complete date range
        min_date = df["date"].min()
        max_date = df["date"].max()
        date_range = pd.date_range(start=min_date, end=max_date, freq="D")
        
        # Create a new DataFrame with all dates
        complete_df = pd.DataFrame({"date": date_range})
        
        # Merge with original data
        merged_df = complete_df.merge(df, on="date", how="left")
        
        # Forward fill stock levels for missing dates
        merged_df["stock_level"] = merged_df["stock_level"].ffill()
        
        # Fill quantity_change with 0 for missing dates (no transactions)
        if "quantity_change" in merged_df.columns:
            merged_df["quantity_change"] = merged_df["quantity_change"].fillna(0)
        
        logger.debug(
            f"Filled missing dates: {len(merged_df)} total days "
            f"(added {len(merged_df) - len(df)} days)"
        )
        
        return merged_df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle outliers in stock levels using IQR method.
        
        Args:
            df: DataFrame with stock_level column
        
        Returns:
            DataFrame with outliers handled
        """
        if df.empty or "stock_level" not in df.columns:
            return df
        
        # Calculate IQR
        Q1 = df["stock_level"].quantile(0.25)
        Q3 = df["stock_level"].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outlier bounds
        lower_bound = Q1 - 3 * IQR
        upper_bound = Q3 + 3 * IQR
        
        # Count outliers
        outliers = (
            (df["stock_level"] < lower_bound) | 
            (df["stock_level"] > upper_bound)
        )
        outlier_count = outliers.sum()
        
        if outlier_count > 0:
            logger.warning(f"Found {outlier_count} outliers in stock levels")
            
            # Cap outliers instead of removing them
            df.loc[df["stock_level"] < lower_bound, "stock_level"] = lower_bound
            df.loc[df["stock_level"] > upper_bound, "stock_level"] = upper_bound
        
        return df
    
    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add additional features to the time series data.
        
        Args:
            df: DataFrame with date and stock_level columns
        
        Returns:
            DataFrame with additional features
        """
        if df.empty:
            return df
        
        # Add day of week
        df["day_of_week"] = df["date"].dt.dayofweek
        
        # Add day of month
        df["day_of_month"] = df["date"].dt.day
        
        # Add month
        df["month"] = df["date"].dt.month
        
        # Calculate rolling average (7-day window)
        if len(df) >= 7:
            df["stock_level_ma7"] = (
                df["stock_level"].rolling(window=7, min_periods=1).mean()
            )
        
        # Calculate daily change in stock
        df["stock_change"] = df["stock_level"].diff().fillna(0)
        
        return df
    
    def has_sufficient_data(self, product_id: UUID) -> Tuple[bool, int]:
        """
        Check if a product has sufficient historical data for training.
        
        Args:
            product_id: UUID of the product
        
        Returns:
            Tuple of (has_sufficient_data, days_of_data)
        """
        try:
            # Get the date range of transactions
            result = (
                self.db.query(
                    func.min(InventoryTransaction.created_at).label("first_date"),
                    func.max(InventoryTransaction.created_at).label("last_date"),
                    func.count(InventoryTransaction.id).label("transaction_count")
                )
                .filter(InventoryTransaction.product_id == product_id)
                .first()
            )
            
            if not result or not result.first_date or not result.last_date:
                logger.info(f"No transactions found for product {product_id}")
                return False, 0
            
            # Calculate days of data
            days_of_data = (result.last_date - result.first_date).days + 1
            
            # Check if we have enough data
            has_sufficient = days_of_data >= MIN_TRAINING_DAYS
            
            logger.info(
                f"Product {product_id} has {days_of_data} days of data "
                f"({result.transaction_count} transactions). "
                f"Sufficient: {has_sufficient}"
            )
            
            return has_sufficient, days_of_data
            
        except Exception as e:
            logger.error(
                f"Error checking data sufficiency for product {product_id}: {str(e)}"
            )
            return False, 0
    
    def prepare_training_data(
        self,
        product_id: UUID
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Prepare complete training dataset for a product.
        
        This method fetches historical data, preprocesses it, and returns
        it in a format ready for model training.
        
        Args:
            product_id: UUID of the product
        
        Returns:
            Tuple of (preprocessed_dataframe, metadata_dict)
        
        Raises:
            InsufficientDataException: If insufficient data for training
        """
        # Check if we have sufficient data
        has_sufficient, days_of_data = self.has_sufficient_data(product_id)
        
        if not has_sufficient:
            raise InsufficientDataException(
                f"Insufficient data for product {product_id}. "
                f"Has {days_of_data} days, requires {MIN_TRAINING_DAYS} days."
            )
        
        # Fetch historical data
        df = self.fetch_historical_data(product_id)
        
        # Preprocess data
        df_processed = self.preprocess_data(df, fill_missing_dates=True)
        
        # Get product information
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        # Prepare metadata
        metadata = {
            "product_id": str(product_id),
            "product_name": product.name if product else "Unknown",
            "product_sku": product.sku if product else "Unknown",
            "days_of_data": days_of_data,
            "data_start_date": df_processed["date"].min().isoformat(),
            "data_end_date": df_processed["date"].max().isoformat(),
            "total_records": len(df_processed),
            "current_stock": product.current_stock if product else 0,
            "reorder_threshold": product.reorder_threshold if product else 0,
            "prepared_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Training data prepared for product {product_id}: "
            f"{len(df_processed)} records over {days_of_data} days"
        )
        
        return df_processed, metadata
    
    def get_data_summary(self, product_id: UUID) -> Dict[str, Any]:
        """
        Get a summary of available data for a product.
        
        Args:
            product_id: UUID of the product
        
        Returns:
            Dictionary with data summary statistics
        """
        try:
            has_sufficient, days_of_data = self.has_sufficient_data(product_id)
            
            if days_of_data == 0:
                return {
                    "product_id": str(product_id),
                    "has_sufficient_data": False,
                    "days_of_data": 0,
                    "message": "No historical data available"
                }
            
            # Fetch and preprocess data
            df = self.fetch_historical_data(product_id)
            df_processed = self.preprocess_data(df)
            
            # Calculate statistics
            summary = {
                "product_id": str(product_id),
                "has_sufficient_data": has_sufficient,
                "days_of_data": days_of_data,
                "min_required_days": MIN_TRAINING_DAYS,
                "total_transactions": len(df),
                "date_range": {
                    "start": df_processed["date"].min().isoformat(),
                    "end": df_processed["date"].max().isoformat()
                },
                "stock_statistics": {
                    "min": float(df_processed["stock_level"].min()),
                    "max": float(df_processed["stock_level"].max()),
                    "mean": float(df_processed["stock_level"].mean()),
                    "current": float(df_processed["stock_level"].iloc[-1])
                }
            }
            
            return summary
            
        except InsufficientDataException as e:
            return {
                "product_id": str(product_id),
                "has_sufficient_data": False,
                "days_of_data": 0,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Error getting data summary for product {product_id}: {str(e)}")
            return {
                "product_id": str(product_id),
                "error": str(e)
            }

    
    def train_model(
        self,
        product_id: UUID,
        force_retrain: bool = False
    ) -> Dict[str, Any]:
        """
        Train a forecasting model for a product.
        
        Args:
            product_id: UUID of the product
            force_retrain: Force retraining even if model exists
        
        Returns:
            Dictionary with training results and metrics
        
        Raises:
            InsufficientDataException: If insufficient data for training
            ModelTrainingException: If training fails
        """
        from app.ml.forecasting import ForecastingModel, ModelTrainingException
        from app.models.ml_prediction import MLPrediction
        
        logger.info(f"Starting model training for product {product_id}")
        
        # Prepare training data
        df, metadata = self.prepare_training_data(product_id)
        
        # Initialize and train model
        forecasting_model = ForecastingModel()
        
        try:
            training_metrics = forecasting_model.train(df, str(product_id))
            
            # Save the model
            model_version = forecasting_model.save(str(product_id))
            
            # Make an initial prediction and save to database
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                try:
                    depletion_date, confidence, forecast_data, consumption_rate = forecasting_model.predict(
                        product.current_stock,
                        forecast_days=90
                    )
                    
                    # Save prediction to database
                    ml_prediction = MLPrediction(
                        product_id=product_id,
                        predicted_depletion_date=depletion_date,
                        confidence_score=confidence,
                        daily_consumption_rate=consumption_rate,
                        model_version=model_version
                    )
                    self.db.add(ml_prediction)
                    self.db.commit()
                    
                    logger.info(
                        f"Initial prediction saved for product {product_id}. "
                        f"Depletion date: {depletion_date}, Confidence: {confidence:.2f}"
                    )
                    
                except Exception as e:
                    logger.warning(f"Failed to save initial prediction: {str(e)}")
                    self.db.rollback()
            
            result = {
                'product_id': str(product_id),
                'success': True,
                'message': f'Model trained successfully using {training_metrics["model_type"]}',
                'model_version': model_version,
                'training_metrics': training_metrics,
                'trained_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Model training completed for product {product_id}")
            return result
            
        except ModelTrainingException as e:
            logger.error(f"Model training failed for product {product_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during training for product {product_id}: {str(e)}")
            raise ModelTrainingException(f"Training failed: {str(e)}")
    
    def predict_depletion(
        self,
        product_id: UUID,
        forecast_days: int = 90
    ) -> Dict[str, Any]:
        """
        Predict stock depletion for a product.
        
        Args:
            product_id: UUID of the product
            forecast_days: Number of days to forecast
        
        Returns:
            Dictionary with prediction results
        
        Raises:
            InsufficientDataException: If no model exists or insufficient data
        """
        from app.ml.forecasting import ForecastingModel
        from app.models.ml_prediction import MLPrediction
        
        logger.info(f"Generating prediction for product {product_id}")
        
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise InsufficientDataException(f"Product {product_id} not found")
        
        # Try to load existing model
        forecasting_model = ForecastingModel()
        model_loaded = forecasting_model.load(str(product_id))
        
        if not model_loaded:
            # No model exists, try to train one
            logger.info(f"No existing model for product {product_id}, training new model")
            try:
                training_result = self.train_model(product_id)
                # Reload the newly trained model
                forecasting_model.load(str(product_id))
            except (InsufficientDataException, Exception) as e:
                raise InsufficientDataException(
                    f"Cannot generate prediction: {str(e)}"
                )
        
        # Make prediction
        try:
            depletion_date, confidence, forecast_data, consumption_rate = forecasting_model.predict(
                product.current_stock,
                forecast_days=forecast_days
            )
            
            # Save prediction to database
            ml_prediction = MLPrediction(
                product_id=product_id,
                predicted_depletion_date=depletion_date,
                confidence_score=confidence,
                daily_consumption_rate=consumption_rate,
                model_version=forecasting_model.model_version
            )
            self.db.add(ml_prediction)
            self.db.commit()
            self.db.refresh(ml_prediction)
            
            result = {
                'product_id': str(product_id),
                'product_name': product.name,
                'product_sku': product.sku,
                'current_stock': product.current_stock,
                'predicted_depletion_date': depletion_date.isoformat() if depletion_date else None,
                'confidence_score': confidence,
                'daily_consumption_rate': consumption_rate,
                'model_version': forecasting_model.model_version,
                'model_type': forecasting_model.model_type,
                'forecast': forecast_data[:30],  # Return first 30 days
                'created_at': ml_prediction.created_at.isoformat()
            }
            
            logger.info(
                f"Prediction generated for product {product_id}. "
                f"Depletion: {depletion_date}, Confidence: {confidence:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for product {product_id}: {str(e)}")
            self.db.rollback()
            raise InsufficientDataException(f"Prediction failed: {str(e)}")
    
    def batch_predict(
        self,
        product_ids: Optional[List[UUID]] = None,
        min_confidence: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate predictions for multiple products.
        
        Args:
            product_ids: Optional list of product IDs. If None, predict all products with sufficient data.
            min_confidence: Minimum confidence score to include in results
        
        Returns:
            Dictionary with batch prediction results
        """
        logger.info("Starting batch prediction")
        
        # Determine which products to predict
        if product_ids is None:
            # Get all products with sufficient data
            all_products = self.db.query(Product).all()
            product_ids = []
            for product in all_products:
                has_sufficient, _ = self.has_sufficient_data(product.id)
                if has_sufficient:
                    product_ids.append(product.id)
            
            logger.info(f"Found {len(product_ids)} products with sufficient data")
        
        # Generate predictions
        predictions = []
        errors = []
        successful = 0
        failed = 0
        
        for product_id in product_ids:
            try:
                prediction = self.predict_depletion(product_id)
                
                # Filter by confidence
                if prediction['confidence_score'] >= min_confidence:
                    predictions.append(prediction)
                    successful += 1
                else:
                    logger.debug(
                        f"Skipping product {product_id} due to low confidence: "
                        f"{prediction['confidence_score']:.2f}"
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to predict for product {product_id}: {str(e)}")
                errors.append({
                    'product_id': str(product_id),
                    'error': str(e)
                })
                failed += 1
        
        result = {
            'total_products': len(product_ids),
            'successful_predictions': successful,
            'failed_predictions': failed,
            'predictions': predictions,
            'errors': errors if errors else None
        }
        
        logger.info(
            f"Batch prediction completed. "
            f"Successful: {successful}, Failed: {failed}"
        )
        
        return result
