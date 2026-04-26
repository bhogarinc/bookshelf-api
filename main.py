"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.error_handlers import setup_error_handlers
from api.middleware import setup_middleware
from api.routes import auth, books
from config.database import db_manager
from config.logging_config import setup_logging
from config.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    setup_logging(settings.log_level, settings.log_format)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    await db_manager.initialize()
    await db_manager.create_tables()
    
    yield
    
    # Shutdown
    await db_manager.close()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Personal book collection management API",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Register routes
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(books.router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/api/docs"
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers
    )
