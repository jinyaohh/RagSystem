"""
Database models for Financial RAG System.

Phase 2 models for Supabase/PostgreSQL integration.
"""

from app.models.user import User, UserCreate, UserUpdate, UserInDB
from app.models.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentInDB,
    DocumentStatus,
)
from app.models.job import (
    ProcessingJob,
    ProcessingJobCreate,
    ProcessingJobUpdate,
    ProcessingJobInDB,
    JobStatus,
    ProcessingStep,
)

__all__ = [
    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    # Document models
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentInDB",
    "DocumentStatus",
    # Job models
    "ProcessingJob",
    "ProcessingJobCreate",
    "ProcessingJobUpdate",
    "ProcessingJobInDB",
    "JobStatus",
    "ProcessingStep",
]
