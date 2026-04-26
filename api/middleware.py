"""FastAPI middleware components."""

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config.logging_config import correlation_id, LogContext
from config.settings import settings

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cid = request.headers.get(settings.correlation_id_header.lower(), "")
        if not cid:
            import uuid
            cid = str(uuid.uuid4())
        
        with LogContext(cid):
            response = await call_next(request)
            response.headers[settings.correlation_id_header] = cid
            return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"extra_data": {"client_ip": request.client.host if request.client else None}}
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={"extra_data": {
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }}
            )
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={"extra_data": {
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2)
                }}
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app: FastAPI, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            ip: [t for t in times if current_time - t < self.window]
            for ip, times in self.requests.items()
        }
        
        # Check rate limit
        client_requests = self.requests.get(client_ip, [])
        if len(client_requests) >= self.max_requests:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Record request
        self.requests[client_ip] = client_requests + [current_time]
        
        return await call_next(request)


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware."""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Custom middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.rate_limit_requests,
        window=settings.rate_limit_window
    )
