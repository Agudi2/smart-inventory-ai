from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import (
    InventoryException,
    ProductNotFoundException,
    InsufficientStockException,
    BarcodeNotFoundException,
    UnauthorizedException,
    ValidationException,
    NotFoundException
)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register routes
    register_routes(app)
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""
    
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException):
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
        return JSONResponse(
            status_code=404,
            content={
                "error": "Product not found",
                "detail": str(exc),
                "type": "ProductNotFoundException"
            }
        )
    
    @app.exception_handler(InsufficientStockException)
    async def insufficient_stock_handler(request: Request, exc: InsufficientStockException):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Insufficient stock",
                "detail": str(exc),
                "type": "InsufficientStockException"
            }
        )
    
    @app.exception_handler(BarcodeNotFoundException)
    async def barcode_not_found_handler(request: Request, exc: BarcodeNotFoundException):
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
    
    # Health check endpoint (no versioning)
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version
        }
    
    # API v1 metrics endpoint
    @app.get(f"{settings.api_v1_prefix}/metrics")
    async def get_metrics():
        return {
            "status": "ok",
            "version": "v1",
            "endpoints": "N/A"
        }
    
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
    
    # API v1 routes will be added here in future tasks
    # from app.api.routes import predictions, alerts
    # app.include_router(predictions.router, prefix=settings.api_v1_prefix, tags=["predictions"])
    # etc.


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
