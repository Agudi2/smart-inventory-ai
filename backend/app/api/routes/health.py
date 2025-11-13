from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "inventory-api"
    }


@router.get("/metrics")
async def get_metrics():
    """System metrics endpoint (placeholder for future implementation)."""
    return {
        "status": "ok",
        "metrics": {
            "uptime": "N/A",
            "requests": "N/A"
        }
    }
