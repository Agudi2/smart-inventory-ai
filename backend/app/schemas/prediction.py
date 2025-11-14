"""Pydantic schemas for ML predictions."""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class DataSummaryResponse(BaseModel):
    """Response schema for data summary."""
    
    product_id: str
    has_sufficient_data: bool
    days_of_data: int
    min_required_days: Optional[int] = None
    total_transactions: Optional[int] = None
    date_range: Optional[Dict[str, str]] = None
    stock_statistics: Optional[Dict[str, float]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PredictionMetadata(BaseModel):
    """Metadata about a prediction."""
    
    product_id: str
    product_name: str
    product_sku: str
    days_of_data: int
    data_start_date: str
    data_end_date: str
    total_records: int
    current_stock: int
    reorder_threshold: int
    prepared_at: str
    
    model_config = ConfigDict(from_attributes=True)


class ForecastPoint(BaseModel):
    """A single point in a forecast."""
    
    date: str
    predicted_stock: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class PredictionResult(BaseModel):
    """Result of a stock depletion prediction."""
    
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    current_stock: Optional[int] = None
    predicted_depletion_date: Optional[str] = None  # ISO format date string
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    daily_consumption_rate: Optional[float] = None
    model_version: Optional[str] = None
    model_type: Optional[str] = None
    forecast: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None  # ISO format datetime string
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MLPredictionResponse(BaseModel):
    """Response schema for ML prediction from database."""
    
    id: UUID
    product_id: UUID
    predicted_depletion_date: Optional[date] = None
    confidence_score: Optional[Decimal] = None
    daily_consumption_rate: Optional[Decimal] = None
    model_version: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class TrainingRequest(BaseModel):
    """Request schema for model training."""
    
    product_id: UUID
    force_retrain: bool = Field(
        default=False,
        description="Force retraining even if a recent model exists"
    )
    
    model_config = ConfigDict(from_attributes=True)


class TrainingResponse(BaseModel):
    """Response schema for model training."""
    
    product_id: str
    success: bool
    message: str
    model_version: Optional[str] = None
    training_metrics: Optional[Dict[str, Any]] = None
    trained_at: str  # ISO format datetime string
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions."""
    
    product_ids: Optional[List[UUID]] = Field(
        default=None,
        description="List of product IDs to predict. If None, predict all products with sufficient data."
    )
    min_confidence: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to include in results"
    )
    
    model_config = ConfigDict(from_attributes=True)


class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions."""
    
    total_products: int
    successful_predictions: int
    failed_predictions: int
    predictions: List[Dict[str, Any]]  # Use Dict to allow flexible prediction format
    errors: Optional[List[Dict[str, str]]] = None
    
    model_config = ConfigDict(from_attributes=True)
