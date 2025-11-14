"""Request logging middleware with correlation IDs."""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests with correlation IDs."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add logging with correlation ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
        
        Returns:
            HTTP response
        """
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        
        # Add correlation ID to request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'correlation_id': correlation_id,
                'request_method': request.method,
                'request_path': request.url.path,
                'request_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}",
                extra={
                    'correlation_id': correlation_id,
                    'request_method': request.method,
                    'request_path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                }
            )
            
            # Add correlation ID to response headers
            response.headers['X-Correlation-ID'] = correlation_id
            
            return response
            
        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - Error: {str(exc)}",
                extra={
                    'correlation_id': correlation_id,
                    'request_method': request.method,
                    'request_path': request.url.path,
                    'duration_ms': round(duration * 1000, 2),
                    'error': str(exc),
                    'error_type': type(exc).__name__,
                },
                exc_info=True
            )
            
            # Re-raise exception to be handled by exception handlers
            raise
