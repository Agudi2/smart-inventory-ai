"""Script to create the forecasting.py file."""

content = '''"""Prophet-based forecasting model for stock depletion prediction."""

import logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.ml.utils import save_model, load_model
from app.core.exceptions import InventoryException

logger = logging.getLogger(__name__)

# Minimum number of data points for Prophet
MIN_PROPHET_POINTS = 30
# Minimum number of data points for linear regression fallback
MIN_LINEAR_POINTS = 7


class ModelTrainingException(InventoryException):
    """Raised when model training fails."""
    pass


class ForecastingModel:
    """
    Prophet-based forecasting model with linear regression fallback.
    
    This class handles training and prediction for stock depletion forecasting.
    It uses Prophet for products with sufficient data and falls back to simple
    linear regression for products with limited data.
    """
    
    def __init__(self):
        """Initialize the forecasting model."""
        self.model = None
        self.model_type = None  # 'prophet' or 'linear'
        self.model_version = None
        self.training_metrics = {}
    
    def train_prophet_model(
        self,
        df: pd.DataFrame,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Train a Prophet model on historical stock data.
        
        Args:
            df: DataFrame with 'date' and 'stock_level' columns
            product_id: UUID of the product
        
        Returns:
            Dictionary with training metrics
        
        Raises:
            ModelTrainingException: If training fails
        """
        try:
            # Prepare data in Prophet format (ds, y)
            prophet_df = pd.DataFrame({
                'ds': pd.to_datetime(df['date']),
                'y': df['stock_level'].astype(float)
            })
            
            # Initialize Prophet with reasonable defaults
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05,  # Less flexible to avoid overfitting
                seasonality_prior_scale=10.0,
                interval_width=0.95  # 95% confidence intervals
            )
            
            # Fit the model
            logger.info(f"Training Prophet model for product {product_id}")
            model.fit(prophet_df)
            
            # Calculate training metrics
            predictions = model.predict(prophet_df)
            mae = mean_absolute_error(prophet_df['y'], predictions['yhat'])
            rmse = np.sqrt(mean_squared_error(prophet_df['y'], predictions['yhat']))
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            # Avoid division by zero
            non_zero_mask = prophet_df['y'] != 0
            if non_zero_mask.sum() > 0:
                mape = np.mean(
                    np.abs(
                        (prophet_df.loc[non_zero_mask, 'y'] - predictions.loc[non_zero_mask, 'yhat']) /
                        prophet_df.loc[non_zero_mask, 'y']
                    )
                ) * 100
            else:
                mape = 0.0
            
            self.model = model
            self.model_type = 'prophet'
            self.model_version = f"prophet_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            metrics = {
                'model_type': 'prophet',
                'mae': float(mae),
                'rmse': float(rmse),
                'mape': float(mape),
                'training_samples': len(prophet_df),
                'trained_at': datetime.utcnow().isoformat()
            }
            
            self.training_metrics = metrics
            
            logger.info(
                f"Prophet model trained successfully for product {product_id}. "
                f"MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}%"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to train Prophet model for product {product_id}: {str(e)}")
            raise ModelTrainingException(f"Prophet training failed: {str(e)}")
    
    def train_linear_model(
        self,
        df: pd.DataFrame,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Train a simple linear regression model as fallback.
        
        Args:
            df: DataFrame with 'date' and 'stock_level' columns
            product_id: UUID of the product
        
        Returns:
            Dictionary with training metrics
        
        Raises:
            ModelTrainingException: If training fails
        """
        try:
            # Prepare data for linear regression
            df = df.copy()
            df['date'] = pd.to_datetime(df['date'])
            
            # Convert dates to numeric (days since first date)
            min_date = df['date'].min()
            df['days_since_start'] = (df['date'] - min_date).dt.days
            
            X = df[['days_since_start']].values
            y = df['stock_level'].values
            
            # Train linear regression model
            model = LinearRegression()
            logger.info(f"Training linear regression model for product {product_id}")
            model.fit(X, y)
            
            # Calculate training metrics
            predictions = model.predict(X)
            mae = mean_absolute_error(y, predictions)
            rmse = np.sqrt(mean_squared_error(y, predictions))
            
            # Calculate MAPE
            non_zero_mask = y != 0
            if non_zero_mask.sum() > 0:
                mape = np.mean(np.abs((y[non_zero_mask] - predictions[non_zero_mask]) / y[non_zero_mask])) * 100
            else:
                mape = 0.0
            
            # Store additional info needed for prediction
            model_data = {
                'model': model,
                'min_date': min_date,
                'slope': float(model.coef_[0]),
                'intercept': float(model.intercept_)
            }
            
            self.model = model_data
            self.model_type = 'linear'
            self.model_version = f"linear_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            metrics = {
                'model_type': 'linear',
                'mae': float(mae),
                'rmse': float(rmse),
                'mape': float(mape),
                'slope': float(model.coef_[0]),
                'training_samples': len(df),
                'trained_at': datetime.utcnow().isoformat()
            }
            
            self.training_metrics = metrics
            
            logger.info(
                f"Linear model trained successfully for product {product_id}. "
                f"MAE: {mae:.2f}, RMSE: {rmse:.2f}, Slope: {model.coef_[0]:.4f}"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to train linear model for product {product_id}: {str(e)}")
            raise ModelTrainingException(f"Linear regression training failed: {str(e)}")
    
    def train(
        self,
        df: pd.DataFrame,
        product_id: str,
        force_model_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Train the appropriate model based on data availability.
        
        Automatically selects Prophet for sufficient data or falls back to
        linear regression for limited data.
        
        Args:
            df: DataFrame with 'date' and 'stock_level' columns
            product_id: UUID of the product
            force_model_type: Optional model type to force ('prophet' or 'linear')
        
        Returns:
            Dictionary with training metrics
        
        Raises:
            ModelTrainingException: If training fails
        """
        if df.empty:
            raise ModelTrainingException("Cannot train model with empty dataset")
        
        data_points = len(df)
        
        # Determine which model to use
        if force_model_type:
            model_type = force_model_type
            logger.info(f"Forcing model type: {model_type}")
        elif data_points >= MIN_PROPHET_POINTS:
            model_type = 'prophet'
            logger.info(f"Using Prophet model ({data_points} data points)")
        elif data_points >= MIN_LINEAR_POINTS:
            model_type = 'linear'
            logger.info(f"Using linear regression fallback ({data_points} data points)")
        else:
            raise ModelTrainingException(
                f"Insufficient data for training. Has {data_points} points, "
                f"requires at least {MIN_LINEAR_POINTS} points."
            )
        
        # Train the selected model
        if model_type == 'prophet':
            try:
                return self.train_prophet_model(df, product_id)
            except ModelTrainingException:
                # If Prophet fails, try linear regression as fallback
                if data_points >= MIN_LINEAR_POINTS:
                    logger.warning(
                        f"Prophet training failed for product {product_id}, "
                        "falling back to linear regression"
                    )
                    return self.train_linear_model(df, product_id)
                else:
                    raise
        else:
            return self.train_linear_model(df, product_id)
    
    def predict_prophet(
        self,
        current_stock: int,
        forecast_days: int = 90
    ) -> Tuple[Optional[date], float, List[Dict[str, Any]]]:
        """
        Make predictions using Prophet model.
        
        Args:
            current_stock: Current stock level
            forecast_days: Number of days to forecast
        
        Returns:
            Tuple of (depletion_date, confidence_score, forecast_data)
        """
        if self.model is None or self.model_type != 'prophet':
            raise ValueError("Prophet model not trained")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=forecast_days, freq='D')
        
        # Make predictions
        forecast = self.model.predict(future)
        
        # Get only future predictions
        forecast_future = forecast.tail(forecast_days)
        
        # Find depletion date (when stock reaches 0)
        depletion_date = None
        for idx, row in forecast_future.iterrows():
            if row['yhat'] <= 0:
                depletion_date = row['ds'].date()
                break
        
        # Calculate confidence score based on prediction intervals
        confidence_score = self._calculate_confidence_prophet(forecast_future)
        
        # Prepare forecast data
        forecast_data = []
        for idx, row in forecast_future.iterrows():
            forecast_data.append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'predicted_stock': float(max(0, row['yhat'])),  # Don't show negative stock
                'lower_bound': float(max(0, row['yhat_lower'])),
                'upper_bound': float(max(0, row['yhat_upper']))
            })
        
        return depletion_date, confidence_score, forecast_data
    
    def predict_linear(
        self,
        current_stock: int,
        forecast_days: int = 90
    ) -> Tuple[Optional[date], float, List[Dict[str, Any]]]:
        """
        Make predictions using linear regression model.
        
        Args:
            current_stock: Current stock level
            forecast_days: Number of days to forecast
        
        Returns:
            Tuple of (depletion_date, confidence_score, forecast_data)
        """
        if self.model is None or self.model_type != 'linear':
            raise ValueError("Linear model not trained")
        
        model_data = self.model
        linear_model = model_data['model']
        min_date = model_data['min_date']
        slope = model_data['slope']
        
        # Calculate days since start for current date
        current_date = datetime.now().date()
        days_since_start = (pd.Timestamp(current_date) - min_date).days
        
        # Generate future dates
        future_dates = [current_date + timedelta(days=i) for i in range(forecast_days + 1)]
        future_days = np.array([days_since_start + i for i in range(forecast_days + 1)]).reshape(-1, 1)
        
        # Make predictions
        predictions = linear_model.predict(future_days)
        
        # Find depletion date
        depletion_date = None
        for i, pred in enumerate(predictions):
            if pred <= 0:
                depletion_date = future_dates[i]
                break
        
        # Calculate confidence score (lower for linear model)
        # Based on the slope and variance
        confidence_score = self._calculate_confidence_linear(slope, predictions)
        
        # Prepare forecast data
        forecast_data = []
        for i, (pred_date, pred_stock) in enumerate(zip(future_dates, predictions)):
            # Simple confidence interval (±20% for linear model)
            margin = abs(pred_stock * 0.2)
            forecast_data.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_stock': float(max(0, pred_stock)),
                'lower_bound': float(max(0, pred_stock - margin)),
                'upper_bound': float(max(0, pred_stock + margin))
            })
        
        return depletion_date, confidence_score, forecast_data
    
    def predict(
        self,
        current_stock: int,
        forecast_days: int = 90
    ) -> Tuple[Optional[date], float, List[Dict[str, Any]], float]:
        """
        Make stock depletion predictions.
        
        Args:
            current_stock: Current stock level
            forecast_days: Number of days to forecast
        
        Returns:
            Tuple of (depletion_date, confidence_score, forecast_data, daily_consumption_rate)
        """
        if self.model is None:
            raise ValueError("Model not trained")
        
        if self.model_type == 'prophet':
            depletion_date, confidence, forecast_data = self.predict_prophet(
                current_stock, forecast_days
            )
        else:
            depletion_date, confidence, forecast_data = self.predict_linear(
                current_stock, forecast_days
            )
        
        # Calculate daily consumption rate
        daily_consumption_rate = self._calculate_consumption_rate(forecast_data)
        
        return depletion_date, confidence, forecast_data, daily_consumption_rate
    
    def _calculate_confidence_prophet(self, forecast: pd.DataFrame) -> float:
        """
        Calculate confidence score based on Prophet prediction intervals.
        
        Args:
            forecast: Prophet forecast DataFrame
        
        Returns:
            Confidence score between 0 and 1
        """
        # Calculate average interval width
        interval_widths = forecast['yhat_upper'] - forecast['yhat_lower']
        avg_interval_width = interval_widths.mean()
        
        # Calculate average prediction
        avg_prediction = forecast['yhat'].mean()
        
        # Confidence is inversely proportional to interval width
        # Normalize by the average prediction to get relative uncertainty
        if avg_prediction > 0:
            relative_uncertainty = avg_interval_width / avg_prediction
            # Convert to confidence score (0 to 1)
            # Lower uncertainty = higher confidence
            confidence = 1.0 / (1.0 + relative_uncertainty)
        else:
            confidence = 0.5  # Neutral confidence if prediction is near zero
        
        # Clamp between 0 and 1
        confidence = max(0.0, min(1.0, confidence))
        
        return float(confidence)
    
    def _calculate_confidence_linear(
        self,
        slope: float,
        predictions: np.ndarray
    ) -> float:
        """
        Calculate confidence score for linear regression model.
        
        Args:
            slope: Slope of the linear model
            predictions: Array of predictions
        
        Returns:
            Confidence score between 0 and 1
        """
        # Linear models are less confident than Prophet
        # Base confidence is lower (0.6 max)
        base_confidence = 0.6
        
        # Reduce confidence if slope is very steep (unstable)
        if abs(slope) > 10:
            base_confidence *= 0.7
        
        # Reduce confidence if predictions vary wildly
        if len(predictions) > 1:
            std_dev = np.std(predictions)
            mean_pred = np.mean(predictions)
            if mean_pred > 0:
                cv = std_dev / mean_pred  # Coefficient of variation
                if cv > 0.5:
                    base_confidence *= 0.8
        
        return float(base_confidence)
    
    def _calculate_consumption_rate(
        self,
        forecast_data: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate average daily consumption rate from forecast.
        
        Args:
            forecast_data: List of forecast points
        
        Returns:
            Average daily consumption rate (positive number)
        """
        if len(forecast_data) < 2:
            return 0.0
        
        # Calculate differences between consecutive days
        consumption_rates = []
        for i in range(1, min(len(forecast_data), 30)):  # Use first 30 days
            prev_stock = forecast_data[i - 1]['predicted_stock']
            curr_stock = forecast_data[i]['predicted_stock']
            daily_change = prev_stock - curr_stock
            consumption_rates.append(daily_change)
        
        if not consumption_rates:
            return 0.0
        
        # Return average consumption rate (as positive number)
        avg_rate = np.mean(consumption_rates)
        return float(max(0, avg_rate))
    
    def save(self, product_id: str) -> str:
        """
        Save the trained model to disk.
        
        Args:
            product_id: UUID of the product
        
        Returns:
            Model version string
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'model_version': self.model_version,
            'training_metrics': self.training_metrics,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        save_model(model_data, product_id, self.model_version)
        logger.info(f"Model saved for product {product_id}, version: {self.model_version}")
        
        return self.model_version
    
    def load(self, product_id: str, model_version: Optional[str] = None) -> bool:
        """
        Load a trained model from disk.
        
        Args:
            product_id: UUID of the product
            model_version: Optional specific version to load
        
        Returns:
            True if loaded successfully, False otherwise
        """
        model_data = load_model(product_id, model_version)
        
        if model_data is None:
            logger.warning(f"No saved model found for product {product_id}")
            return False
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.model_version = model_data['model_version']
        self.training_metrics = model_data.get('training_metrics', {})
        
        logger.info(
            f"Model loaded for product {product_id}, "
            f"type: {self.model_type}, version: {self.model_version}"
        )
        
        return True
'''

import os
os.makedirs('app/ml', exist_ok=True)
with open('app/ml/forecasting.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File created successfully!")
