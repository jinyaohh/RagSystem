"""
Financial RAG System - Main FastAPI Application.

Provides REST API for document upload, processing, and querying.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings, print_config_summary
from app.core.logging import setup_logging, get_logger
from app.services.factory import (
    get_llm_service,
    get_embedding_service,
    get_vector_service,
    cleanup_services,
)

# Initialize logging
setup_logging()
logger = get_logger(__name__)


# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # ========================================================================
    # Startup
    # ========================================================================
    logger.info("=" * 70)
    logger.info("Starting Financial RAG System...")
    logger.info("=" * 70)

    # Print configuration summary
    if settings.DEBUG:
        print_config_summary()

    # Initialize services (lazy initialization)
    logger.info("Initializing services...")

    try:
        # Test LLM service connection
        llm_service = get_llm_service()
        logger.info(f"✓ LLM Service: {llm_service.get_model_name()}")

        # Test embedding service connection
        embedding_service = get_embedding_service()
        logger.info(
            f"✓ Embedding Service: {embedding_service.get_model_name()} "
            f"(dimension: {embedding_service.get_dimension()})"
        )

        # Test vector DB connection
        vector_service = get_vector_service()
        is_connected = await vector_service.validate_connection()
        if is_connected:
            logger.info("✓ Vector DB: Connected to Qdrant")

            # Ensure collection exists
            await vector_service.ensure_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                dimension=embedding_service.get_dimension(),
            )
            logger.info(f"✓ Collection: {settings.QDRANT_COLLECTION_NAME}")
        else:
            logger.warning("⚠ Vector DB: Could not connect to Qdrant")

        logger.info("=" * 70)
        logger.info("✓ All services initialized successfully!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        if settings.is_production:
            raise

    # Yield control to application
    yield

    # ========================================================================
    # Shutdown
    # ========================================================================
    logger.info("Shutting down Financial RAG System...")

    # Cleanup services
    await cleanup_services()

    logger.info("✓ Shutdown complete")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RAG system for querying financial reports using natural language",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ============================================================================
# Middleware
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        Status indicating if service is running
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with service status.

    Returns:
        Detailed status of all services
    """
    try:
        # Check LLM service
        llm_service = get_llm_service()
        llm_status = {
            "provider": settings.LLM_PROVIDER.value,
            "model": llm_service.get_model_name(),
            "status": "healthy",
        }

        # Check embedding service
        embedding_service = get_embedding_service()
        embedding_status = {
            "provider": settings.EMBEDDING_PROVIDER.value,
            "model": embedding_service.get_model_name(),
            "dimension": embedding_service.get_dimension(),
            "status": "healthy",
        }

        # Check vector DB
        vector_service = get_vector_service()
        is_connected = await vector_service.validate_connection()
        vector_status = {
            "type": "qdrant",
            "host": settings.QDRANT_HOST,
            "port": settings.QDRANT_PORT,
            "status": "healthy" if is_connected else "unhealthy",
        }

        # Collection info
        collection_status = {}
        if is_connected:
            try:
                collection_exists = await vector_service.collection_exists(
                    settings.QDRANT_COLLECTION_NAME
                )
                if collection_exists:
                    collection_info = await vector_service.get_collection_info(
                        settings.QDRANT_COLLECTION_NAME
                    )
                    collection_status = {
                        "name": settings.QDRANT_COLLECTION_NAME,
                        "exists": True,
                        "vectors_count": collection_info.get("vectors_count", 0),
                        "points_count": collection_info.get("points_count", 0),
                    }
                else:
                    collection_status = {
                        "name": settings.QDRANT_COLLECTION_NAME,
                        "exists": False,
                    }
            except Exception as e:
                logger.error(f"Error getting collection info: {e}")
                collection_status = {"error": str(e)}

        # Phase 2 Services
        services_status = {
            "llm": llm_status,
            "embedding": embedding_status,
            "vector_db": vector_status,
            "collection": collection_status,
        }

        # Check Supabase (Phase 2)
        if settings.AUTH_ENABLED:
            try:
                from app.services.supabase_service import get_supabase_service
                supabase_service = get_supabase_service()
                supabase_status = supabase_service.health_check()
                services_status["supabase"] = supabase_status
            except Exception as e:
                logger.error(f"Supabase health check failed: {e}")
                services_status["supabase"] = {"status": "unhealthy", "error": str(e)}

        # Check Celery (Phase 2)
        if settings.CELERY_ENABLED:
            try:
                from app.tasks.celery_app import celery_app
                # Check Celery worker status
                inspect = celery_app.control.inspect()
                stats = inspect.stats()
                active = inspect.active()

                celery_status = {
                    "status": "healthy" if stats else "unhealthy",
                    "workers": len(stats) if stats else 0,
                    "active_tasks": sum(len(tasks) for tasks in active.values()) if active else 0,
                }
                services_status["celery"] = celery_status
            except Exception as e:
                logger.error(f"Celery health check failed: {e}")
                services_status["celery"] = {"status": "unhealthy", "error": str(e)}

        # Feature flags
        feature_flags = {
            "auth_enabled": settings.AUTH_ENABLED,
            "celery_enabled": settings.CELERY_ENABLED,
            "redis_enabled": settings.REDIS_ENABLED,
        }

        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
            "services": services_status,
            "features": feature_flags,
            "config": {
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "top_k": settings.TOP_K,
                "max_file_size": settings.MAX_FILE_SIZE,
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e) if settings.DEBUG else "Service unavailable",
            },
        )


# ============================================================================
# API Routes
# ============================================================================

# Import routers
from app.api.routes import documents, query, auth, jobs

# Include routers - Phase 1
app.include_router(documents.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")

# Include routers - Phase 2 (conditionally based on feature flags)
if settings.AUTH_ENABLED:
    app.include_router(auth.router, prefix="/api/v1")
    logger.info("✓ Authentication routes enabled")

if settings.CELERY_ENABLED or settings.AUTH_ENABLED:
    app.include_router(jobs.router, prefix="/api/v1")
    logger.info("✓ Job tracking routes enabled")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        API information and available endpoints
    """
    endpoints = {
        "health": "/health",
        "detailed_health": "/health/detailed",
        "docs": "/docs" if settings.DEBUG else None,
        "redoc": "/redoc" if settings.DEBUG else None,
        "documents": "/api/v1/documents",
        "query": "/api/v1/query",
    }

    # Add Phase 2 endpoints if enabled
    if settings.AUTH_ENABLED:
        endpoints["auth"] = {
            "signup": "/api/v1/auth/signup",
            "login": "/api/v1/auth/login",
            "logout": "/api/v1/auth/logout",
            "refresh": "/api/v1/auth/refresh",
            "me": "/api/v1/auth/me",
        }

    if settings.CELERY_ENABLED or settings.AUTH_ENABLED:
        endpoints["jobs"] = {
            "list": "/api/v1/jobs",
            "get": "/api/v1/jobs/{job_id}",
            "cancel": "/api/v1/jobs/{job_id}/cancel",
            "stats": "/api/v1/jobs/stats/summary",
        }

    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "RAG system for querying financial reports",
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/health",
        "features": {
            "authentication": settings.AUTH_ENABLED,
            "async_processing": settings.CELERY_ENABLED,
        },
        "endpoints": endpoints
    }


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
