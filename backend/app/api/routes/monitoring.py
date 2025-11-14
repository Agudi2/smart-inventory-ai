"""Health check and monitoring endpoints."""

import logging
import time
import psutil
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db, engine
from app.core.cache import cache
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])

# Track application start time
app_start_time = time.time()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint that verifies database and Redis connectivity.
    
    Returns:
        Health status with component checks
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_name": settings.app_name,
        "version": settings.app_version,
        "checks": {}
    }
    
    # Check database connectivity
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis connectivity
    redis_available = cache.is_available()
    if redis_available:
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    else:
        logger.warning("Redis health check failed")
        health_status["checks"]["redis"] = {
            "status": "degraded",
            "message": "Redis connection failed - caching disabled"
        }
        # Redis failure is not critical, so we mark as degraded
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    
    return health_status


@router.get("/api/v1/metrics")
async def get_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    System metrics endpoint with application and infrastructure statistics.
    
    Returns:
        System metrics including uptime, resource usage, and database stats
    """
    try:
        # Calculate uptime
        uptime_seconds = time.time() - app_start_time
        uptime_hours = uptime_seconds / 3600
        
        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get database statistics
        db_stats = {}
        try:
            # Get database pool statistics
            pool = engine.pool
            db_stats = {
                "pool_size": pool.size(),
                "checked_out_connections": pool.checkedout(),
                "overflow_connections": pool.overflow(),
                "total_connections": pool.size() + pool.overflow(),
            }
            
            # Get table counts
            from app.models import Product, InventoryTransaction, Vendor, User, Alert
            
            product_count = db.query(Product).count()
            transaction_count = db.query(InventoryTransaction).count()
            vendor_count = db.query(Vendor).count()
            user_count = db.query(User).count()
            alert_count = db.query(Alert).filter(Alert.status == 'active').count()
            
            db_stats.update({
                "products": product_count,
                "transactions": transaction_count,
                "vendors": vendor_count,
                "users": user_count,
                "active_alerts": alert_count,
            })
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}", exc_info=True)
            db_stats["error"] = str(e)
        
        # Get Redis statistics
        redis_stats = {}
        if cache.is_available():
            try:
                info = cache.redis_client.info()
                redis_stats = {
                    "connected": True,
                    "used_memory_human": info.get('used_memory_human', 'N/A'),
                    "connected_clients": info.get('connected_clients', 0),
                    "total_commands_processed": info.get('total_commands_processed', 0),
                }
            except Exception as e:
                logger.error(f"Error getting Redis statistics: {str(e)}", exc_info=True)
                redis_stats = {"connected": False, "error": str(e)}
        else:
            redis_stats = {"connected": False, "message": "Redis not available"}
        
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "application": {
                "name": settings.app_name,
                "version": settings.app_version,
                "uptime_seconds": round(uptime_seconds, 2),
                "uptime_hours": round(uptime_hours, 2),
                "debug_mode": settings.debug,
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent,
                }
            },
            "database": db_stats,
            "redis": redis_stats,
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}", exc_info=True)
        return {
            "error": "Failed to generate metrics",
            "detail": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
