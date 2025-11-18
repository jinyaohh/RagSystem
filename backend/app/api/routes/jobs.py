"""
Processing job API endpoints.

Handles job status tracking and monitoring for async document processing.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.core.config import settings
from app.models.user import User
from app.models.job import ProcessingJob, JobStatus, JobListResponse, JobStats
from app.services.supabase_service import get_supabase_service, SupabaseService
from app.middleware.auth import get_current_user_optional, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Processing Jobs"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CancelJobRequest(BaseModel):
    """Request to cancel a job."""
    reason: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status_filter: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    List processing jobs.

    Returns jobs for the authenticated user, or all jobs if no auth.

    Args:
        status_filter: Optional filter by job status
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip (for pagination)
        current_user: Current user (optional)

    Returns:
        List of processing jobs with pagination info
    """
    try:
        # If auth is enabled but no user, require auth
        if settings.AUTH_ENABLED and not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Get jobs for user (or all if no user)
        if current_user:
            jobs = await supabase.list_user_jobs(
                current_user.id,
                status=status_filter,
                limit=limit,
                offset=offset
            )
        else:
            # No auth mode - would need different implementation
            jobs = []

        # Calculate stats
        active_jobs = sum(1 for job in jobs if job.is_active)
        completed_jobs = sum(1 for job in jobs if job.status == JobStatus.COMPLETED)
        failed_jobs = sum(1 for job in jobs if job.status == JobStatus.FAILED)

        return JobListResponse(
            jobs=jobs,
            total=len(jobs),
            page=offset // limit + 1,
            page_size=limit,
            active_jobs=active_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )


@router.get("/{job_id}", response_model=ProcessingJob)
async def get_job(
    job_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Get processing job by ID.

    Returns job status and progress information.

    Args:
        job_id: Job UUID
        current_user: Current user (optional)

    Returns:
        Processing job details

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        # Get job
        job = await supabase.get_job_by_id(
            job_id,
            user_id=current_user.id if current_user else None
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        return job

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )


@router.post("/{job_id}/cancel", response_model=ProcessingJob)
async def cancel_job(
    job_id: UUID,
    request: CancelJobRequest,
    current_user: User = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Cancel a processing job.

    Attempts to cancel a running or queued job.

    Args:
        job_id: Job UUID
        request: Cancellation request with optional reason
        current_user: Current authenticated user

    Returns:
        Updated job with cancelled status

    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Job cancellation requires authentication"
        )

    try:
        # Get job
        job = await supabase.get_job_by_id(job_id, user_id=current_user.id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # Check if job can be cancelled
        if job.is_finished:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is already {job.status.value} and cannot be cancelled"
            )

        # Cancel Celery task
        from app.tasks.celery_app import celery_app
        celery_app.control.revoke(job.task_id, terminate=True)

        # Update job status
        from app.models.job import ProcessingJobUpdate, ProcessingStep
        from datetime import datetime

        updated_job = await supabase.update_job(
            job_id,
            ProcessingJobUpdate(
                status=JobStatus.CANCELLED,
                current_step=ProcessingStep.FAILED,
                error_message=request.reason or "Cancelled by user",
                completed_at=datetime.utcnow()
            )
        )

        logger.info(f"Job {job_id} cancelled by user {current_user.id}")

        return updated_job

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )


@router.get("/stats/summary", response_model=JobStats)
async def get_job_stats(
    current_user: Optional[User] = Depends(get_current_user_optional),
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Get job statistics summary.

    Returns aggregated statistics about processing jobs.

    Args:
        current_user: Current user (optional)

    Returns:
        Job statistics
    """
    try:
        # Get all jobs for user
        if current_user:
            jobs = await supabase.list_user_jobs(current_user.id, limit=1000)
        else:
            jobs = []

        # Calculate stats
        total = len(jobs)
        queued = sum(1 for job in jobs if job.status == JobStatus.QUEUED)
        processing = sum(1 for job in jobs if job.status == JobStatus.PROCESSING)
        completed = sum(1 for job in jobs if job.status == JobStatus.COMPLETED)
        failed = sum(1 for job in jobs if job.status == JobStatus.FAILED)
        cancelled = sum(1 for job in jobs if job.status == JobStatus.CANCELLED)

        # Calculate average duration for completed jobs
        completed_jobs = [job for job in jobs if job.status == JobStatus.COMPLETED and job.duration_seconds]
        avg_duration = (
            sum(job.duration_seconds for job in completed_jobs) / len(completed_jobs)
            if completed_jobs
            else None
        )

        # Calculate success rate
        finished_jobs = completed + failed
        success_rate = (completed / finished_jobs * 100) if finished_jobs > 0 else 0.0

        return JobStats(
            total_jobs=total,
            queued=queued,
            processing=processing,
            completed=completed,
            failed=failed,
            cancelled=cancelled,
            average_duration_seconds=avg_duration,
            success_rate=success_rate
        )

    except Exception as e:
        logger.error(f"Failed to get job stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job statistics"
        )
