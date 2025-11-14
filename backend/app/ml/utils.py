"""Utility functions for ML model storage and persistence."""

import os
import joblib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Model storage directory
MODEL_STORAGE_DIR = Path("ml_models")


def ensure_model_directory() -> Path:
    """
    Ensure the model storage directory exists.
    
    Returns:
        Path: Path to the model storage directory
    """
    MODEL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return MODEL_STORAGE_DIR


def get_model_path(product_id: str, model_version: Optional[str] = None) -> Path:
    """
    Get the file path for a product's model.
    
    Args:
        product_id: UUID of the product
        model_version: Optional version string, defaults to 'latest'
    
    Returns:
        Path: Full path to the model file
    """
    ensure_model_directory()
    version = model_version or "latest"
    filename = f"model_{product_id}_{version}.joblib"
    return MODEL_STORAGE_DIR / filename


def save_model(model: Any, product_id: str, model_version: Optional[str] = None) -> Path:
    """
    Save a trained model to disk using joblib.
    
    Args:
        model: The trained model object to save
        product_id: UUID of the product
        model_version: Optional version string
    
    Returns:
        Path: Path where the model was saved
    """
    model_path = get_model_path(product_id, model_version)
    
    try:
        joblib.dump(model, model_path)
        logger.info(f"Model saved successfully for product {product_id} at {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to save model for product {product_id}: {str(e)}")
        raise


def load_model(product_id: str, model_version: Optional[str] = None) -> Optional[Any]:
    """
    Load a trained model from disk.
    
    Args:
        product_id: UUID of the product
        model_version: Optional version string
    
    Returns:
        The loaded model object, or None if not found
    """
    model_path = get_model_path(product_id, model_version)
    
    if not model_path.exists():
        logger.warning(f"Model not found for product {product_id} at {model_path}")
        return None
    
    try:
        model = joblib.load(model_path)
        logger.info(f"Model loaded successfully for product {product_id}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model for product {product_id}: {str(e)}")
        return None


def delete_model(product_id: str, model_version: Optional[str] = None) -> bool:
    """
    Delete a model file from disk.
    
    Args:
        product_id: UUID of the product
        model_version: Optional version string
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    model_path = get_model_path(product_id, model_version)
    
    if not model_path.exists():
        logger.warning(f"Model file not found for deletion: {model_path}")
        return False
    
    try:
        model_path.unlink()
        logger.info(f"Model deleted successfully for product {product_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete model for product {product_id}: {str(e)}")
        return False


def get_model_metadata(product_id: str, model_version: Optional[str] = None) -> Optional[dict]:
    """
    Get metadata about a saved model.
    
    Args:
        product_id: UUID of the product
        model_version: Optional version string
    
    Returns:
        dict: Metadata including file size, modification time, etc.
    """
    model_path = get_model_path(product_id, model_version)
    
    if not model_path.exists():
        return None
    
    stat = model_path.stat()
    return {
        "path": str(model_path),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "product_id": product_id,
        "model_version": model_version or "latest"
    }
