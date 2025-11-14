import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.exceptions import (
    InventoryException,
    ProductNotFoundException,
    InsufficientStockException,
    BarcodeNotFoundException,
    UnauthorizedException,
    ValidationException,
    NotFoundException,
    AlertNotFoundException
)
from app.ml.prediction_service import InsufficientDataException

# Setup logging
setup_logging(
    log_level="DEBUG" if settings.debug else "INFO",
    json_logs=not settings.debug  # Use JSON logs in production, plain text in debug
)

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
## Smart Inventory Management System API

A comprehensive inventory management system with AI-powered stock prediction capabilities.

### Features

* **Product Management**: Create, read, update, and delete products with SKU tracking
* **Barcode Scanning**: Scan and lookup products using barcodes
* **Inventory Tracking**: Track stock movements and adjustments with full history
* **ML Predictions**: AI-powered stock depletion forecasting using Prophet
* **Vendor Management**: Compare vendor prices and get restocking recommendations
* **Smart Alerts**: Automated low stock and predicted depletion alerts
* **Authentication**: Secure JWT-based authentication system

### Authentication

Most endpoints require authentication using JWT tokens. To authenticate:

1. Register a new account using `POST /api/v1/auth/register`
2. Login using `POST /api/v1/auth/login` to receive access and refresh tokens
3. Include the access token in the `Authorization` header: `Bearer <token>`
4. Refresh expired tokens using `POST /api/v1/auth/refresh`

### Rate Limiting

API requests are rate-limited to ensure fair usage and system stability.

### Support

For issues or questions, please refer to the project documentation.
        """,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "User authentication and authorization endpoints. Register, login, and manage JWT tokens."
            },
            {
                "name": "products",
                "description": "Product management operations. Create, read, update, and delete products with SKU tracking and stock status."
            },
            {
                "name": "inventory",
                "description": "Inventory tracking and stock movement operations. Adjust stock levels and view transaction history."
            },
            {
                "name": "barcode",
                "description": "Barcode scanning and lookup operations. Scan barcodes to identify products and update inventory."
            },
            {
                "name": "vendors",
                "description": "Vendor management and price comparison. Manage suppliers and compare pricing for restocking decisions."
            },
            {
                "name": "predictions",
                "description": "ML-powered stock depletion predictions. Train models and forecast when products will run out of stock."
            },
            {
                "name": "alerts",
                "description": "Alert management for low stock and predicted depletion. View, acknowledge, and resolve inventory alerts."
            },
            {
                "name": "monitoring",
                "description": "System health checks and monitoring endpoints. Check service status and view system metrics."
            }
        ],
        contact={
            "name": "Smart Inventory System",
            "url": "https://github.com/yourusername/smart-inventory-system",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.yourdomain.com",
                "description": "Production server"
            }
        ]
    )
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Log application startup."""
        logger.info(
            f"Application starting: {settings.app_name} v{settings.app_version}",
            extra={
                'event': 'startup',
                'debug_mode': settings.debug,
                'api_prefix': settings.api_v1_prefix
            }
        )
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Log application shutdown."""
        logger.info(
            f"Application shutting down: {settings.app_name}",
            extra={'event': 'shutdown'}
        )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register routes
    register_routes(app)
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with logging."""
    
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Resource not found: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'NotFoundException'
            }
        )
        return JSONResponse(
            status_code=404,
            content={
                "error": "Resource not found",
                "detail": str(exc),
                "type": "NotFoundException"
            }
        )
    
    @app.exception_handler(ProductNotFoundException)
    async def product_not_found_handler(request: Request, exc: ProductNotFoundException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Product not found: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'ProductNotFoundException'
            }
        )
        return JSONResponse(
            status_code=404,
            content={
                "error": "Product not found",
                "detail": str(exc),
                "type": "ProductNotFoundException"
            }
        )
    
    @app.exception_handler(AlertNotFoundException)
    async def alert_not_found_handler(request: Request, exc: AlertNotFoundException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Alert not found: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'AlertNotFoundException'
            }
        )
        return JSONResponse(
            status_code=404,
            content={
                "error": "Alert not found",
                "detail": str(exc),
                "type": "AlertNotFoundException"
            }
        )
    
    @app.exception_handler(InsufficientStockException)
    async def insufficient_stock_handler(request: Request, exc: InsufficientStockException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Insufficient stock: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'InsufficientStockException'
            }
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "Insufficient stock",
                "detail": str(exc),
                "type": "InsufficientStockException"
            }
        )
    
    @app.exception_handler(InsufficientDataException)
    async def insufficient_data_handler(request: Request, exc: InsufficientDataException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Insufficient data for prediction: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'InsufficientDataException'
            }
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "Insufficient data",
                "detail": str(exc),
                "type": "InsufficientDataException"
            }
        )
    
    @app.exception_handler(BarcodeNotFoundException)
    async def barcode_not_found_handler(request: Request, exc: BarcodeNotFoundException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Barcode not found: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'BarcodeNotFoundException'
            }
        )
        return JSONResponse(
            status_code=404,
            content={
                "error": "Barcode not found",
                "detail": str(exc),
                "type": "BarcodeNotFoundException"
            }
        )
    
    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request: Request, exc: UnauthorizedException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Unauthorized access attempt: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'UnauthorizedException'
            }
        )
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
                "detail": str(exc),
                "type": "UnauthorizedException"
            }
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Validation error: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'ValidationException'
            }
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation error",
                "detail": str(exc),
                "type": "ValidationException"
            }
        )
    
    @app.exception_handler(InventoryException)
    async def inventory_exception_handler(request: Request, exc: InventoryException):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Inventory error: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': exc.__class__.__name__
            }
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "Inventory error",
                "detail": str(exc),
                "type": exc.__class__.__name__
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.warning(
            f"Request validation error: {exc.errors()}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': 'RequestValidationError',
                'validation_errors': exc.errors()
            }
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "detail": exc.errors(),
                "type": "RequestValidationError"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                'correlation_id': correlation_id,
                'request_path': request.url.path,
                'error_type': type(exc).__name__
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred",
                "type": "InternalServerError"
            }
        )


def register_routes(app: FastAPI) -> None:
    """Register API routes with versioning."""
    
    # Import and register monitoring routes (health check and metrics)
    from app.api.routes import monitoring
    app.include_router(monitoring.router)
    
    # Import and register auth routes
    from app.api.routes import auth
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    
    # Import and register product routes
    from app.api.routes import products
    app.include_router(products.router, prefix=settings.api_v1_prefix)
    
    # Import and register inventory routes
    from app.api.routes import inventory
    app.include_router(inventory.router, prefix=settings.api_v1_prefix)
    
    # Import and register barcode routes
    from app.api.routes import barcode
    app.include_router(barcode.router, prefix=settings.api_v1_prefix)
    
    # Import and register vendor routes
    from app.api.routes import vendors
    app.include_router(vendors.router, prefix=settings.api_v1_prefix)
    
    # Import and register prediction routes
    from app.api.routes import predictions
    app.include_router(predictions.router, prefix=settings.api_v1_prefix)
    
    # Import and register alert routes
    from app.api.routes import alerts
    app.include_router(alerts.router, prefix=settings.api_v1_prefix)


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
