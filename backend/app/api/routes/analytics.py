"""
Analytics API Routes

Endpoints for analytics and insights.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import settings
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models.analytics import (
    PopularQueriesResponse,
    ProcessingStatsResponse,
    SystemOverview,
    UserActivityResponse,
    UserAnalyticsStats,
)
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(
    supabase: SupabaseService = Depends(lambda: SupabaseService() if settings.AUTH_ENABLED else None)
) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(supabase)


# ============================================================================
# User Analytics Endpoints
# ============================================================================

@router.get("/user/stats", response_model=UserAnalyticsStats)
async def get_user_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get analytics statistics for the current user.

    Returns:
        - Total documents, queries, storage
        - Average response time
        - Document breakdown by type
        - Most queried documents
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=501,
            detail="Analytics require authentication to be enabled"
        )

    try:
        stats = await analytics.get_user_stats(current_user.id, days)
        return stats

    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user statistics"
        )


@router.get("/user/activity", response_model=UserActivityResponse)
async def get_user_activity(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$", description="Time period"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get user activity over time.

    Returns daily breakdown of queries and uploads for the specified period.

    Query Parameters:
        - period: 7d, 30d, 90d, or 1y
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=501,
            detail="Analytics require authentication to be enabled"
        )

    try:
        activity = await analytics.get_user_activity(current_user.id, period)
        return activity

    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user activity"
        )


@router.get("/user/popular-queries", response_model=PopularQueriesResponse)
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get most popular queries for the current user.

    Returns the most frequently asked questions along with:
        - Number of times asked
        - Average response time
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=501,
            detail="Analytics require authentication to be enabled"
        )

    try:
        popular = await analytics.get_popular_queries(current_user.id, limit)
        return popular

    except Exception as e:
        logger.error(f"Error getting popular queries: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve popular queries"
        )


# ============================================================================
# System Analytics Endpoints (Admin Only - Future)
# ============================================================================
# Note: These endpoints would require admin role checking
# For now, they're commented out. Implement when admin roles are added.

@router.get("/system/overview", response_model=SystemOverview)
async def get_system_overview(
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get system-wide overview statistics.

    **Note**: In a production system, this should be restricted to admin users.
    For now, it's available to all authenticated users for demonstration.

    Returns:
        - Total users, documents, queries
        - Active users in last 30 days
        - Storage usage
        - Average query latency
        - Success rate
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=501,
            detail="Analytics require authentication to be enabled"
        )

    try:
        # TODO: Add admin role check
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin access required")

        overview = await analytics.get_system_overview()
        return overview

    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system overview"
        )


# ============================================================================
# Document Analytics Endpoints
# ============================================================================

@router.get("/documents/processing-stats", response_model=ProcessingStatsResponse)
async def get_processing_stats(
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get document processing statistics.

    Returns processing performance metrics:
        - Average processing time
        - Performance by step (extraction, chunking, embedding, storage)
        - Performance by document type (PDF, DOCX, XLSX)
        - Success rates

    **Note**: Currently returns system-wide stats. In production,
    this should be user-scoped or admin-only.
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=501,
            detail="Analytics require authentication to be enabled"
        )

    try:
        stats = await analytics.get_processing_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve processing statistics"
        )


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def analytics_health(
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """
    Check analytics service health.

    Returns status of analytics tables and connectivity.
    """
    try:
        health = analytics.health_check()
        return health

    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
