"""Pydantic schemas for API request/response validation."""

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    UserUpdate
)
from app.schemas.product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse
)
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
from app.schemas.alert import (
    AlertBase,
    AlertCreate,
    AlertResponse,
    AlertAcknowledge,
    AlertResolve,
    AlertSettingsResponse,
    AlertSettingsUpdate
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "TokenRefresh",
    "UserResponse",
    "UserUpdate",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "DataSummaryResponse",
    "PredictionMetadata",
    "ForecastPoint",
    "PredictionResult",
    "MLPredictionResponse",
    "TrainingRequest",
    "TrainingResponse",
    "BatchPredictionRequest",
    "BatchPredictionResponse",
    "AlertBase",
    "AlertCreate",
    "AlertResponse",
    "AlertAcknowledge",
    "AlertResolve",
    "AlertSettingsResponse",
    "AlertSettingsUpdate"
]
