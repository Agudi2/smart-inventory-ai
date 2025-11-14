"""Redis cache utilities for caching API responses."""

import json
import logging
from typing import Optional, Any
from functools import wraps

import redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager for storing and retrieving cached data."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except RedisError as e:
            logger.warning(f"Redis connection failed: {str(e)}. Caching will be disabled.")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or error
        """
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default: 1 hour)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.warning(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "predictions:*")
        
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Error deleting cache pattern {pattern}: {str(e)}")
            return 0
    
    def is_available(self) -> bool:
        """
        Check if Redis is available.
        
        Returns:
            True if Redis is connected and responsive
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False


# Global cache instance
cache = RedisCache()


def cache_key_prediction(product_id: str) -> str:
    """Generate cache key for product prediction."""
    return f"prediction:{product_id}"


def cache_key_batch_predictions() -> str:
    """Generate cache key for batch predictions."""
    return "predictions:batch"


def invalidate_prediction_cache(product_id: Optional[str] = None) -> None:
    """
    Invalidate prediction cache for a product or all products.
    
    Args:
        product_id: Optional product ID. If None, invalidate all predictions.
    """
    if product_id:
        cache.delete(cache_key_prediction(product_id))
    else:
        cache.delete_pattern("prediction:*")
        cache.delete(cache_key_batch_predictions())
