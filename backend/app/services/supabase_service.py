"""
Supabase service for database, authentication, and storage operations.

Provides a high-level interface to Supabase for the RAG system.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from supabase import create_client, Client
from postgrest.exceptions import APIError as PostgrestAPIError

from app.core.config import settings
from app.models.user import User, UserCreate, UserInDB
from app.models.document import Document, DocumentCreate, DocumentUpdate, DocumentStatus
from app.models.job import ProcessingJob, ProcessingJobCreate, ProcessingJobUpdate, JobStatus

logger = logging.getLogger(__name__)


class SupabaseService:
    """
    Service for interacting with Supabase.

    Handles database operations, authentication, and file storage.
    """

    def __init__(self):
        """Initialize Supabase client."""
        if settings.AUTH_ENABLED:
            try:
                self.client: Client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise
        else:
            logger.info("Supabase disabled (AUTH_ENABLED=False)")
            self.client = None

    # ========================================================================
    # User Operations
    # ========================================================================

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User object or None if not found
        """
        if not self.client:
            return None

        try:
            response = self.client.table("users").select("*").eq("id", str(user_id)).execute()

            if response.data and len(response.data) > 0:
                return User(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User object or None if not found
        """
        if not self.client:
            return None

        try:
            response = self.client.table("users").select("*").eq("email", email).execute()

            if response.data and len(response.data) > 0:
                return UserInDB(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None

    async def update_user_stats(
        self,
        user_id: UUID,
        total_documents: Optional[int] = None,
        total_queries: Optional[int] = None
    ) -> bool:
        """
        Update user statistics.

        Args:
            user_id: User UUID
            total_documents: New total document count
            total_queries: New total query count

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            update_data = {}
            if total_documents is not None:
                update_data["total_documents"] = total_documents
            if total_queries is not None:
                update_data["total_queries"] = total_queries

            if not update_data:
                return True

            self.client.table("users").update(update_data).eq("id", str(user_id)).execute()

            logger.info(f"Updated stats for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update user stats: {e}")
            return False

    # ========================================================================
    # Document Operations
    # ========================================================================

    async def create_document(self, document: DocumentCreate) -> Optional[Document]:
        """
        Create a new document record.

        Args:
            document: Document creation data

        Returns:
            Created document or None if failed
        """
        if not self.client:
            return None

        try:
            data = {
                "user_id": str(document.user_id),
                "filename": document.filename,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "storage_path": document.storage_path,
                "status": DocumentStatus.PENDING.value,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            response = self.client.table("documents").insert(data).execute()

            if response.data and len(response.data) > 0:
                return Document(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            return None

    async def get_document_by_id(self, document_id: UUID, user_id: Optional[UUID] = None) -> Optional[Document]:
        """
        Get document by ID.

        Args:
            document_id: Document UUID
            user_id: Optional user ID for ownership verification

        Returns:
            Document or None if not found
        """
        if not self.client:
            return None

        try:
            query = self.client.table("documents").select("*").eq("id", str(document_id))

            if user_id:
                query = query.eq("user_id", str(user_id))

            response = query.execute()

            if response.data and len(response.data) > 0:
                return Document(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    async def list_user_documents(
        self,
        user_id: UUID,
        status: Optional[DocumentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """
        List documents for a user.

        Args:
            user_id: User UUID
            status: Optional status filter
            limit: Maximum number of documents
            offset: Number of documents to skip

        Returns:
            List of documents
        """
        if not self.client:
            return []

        try:
            query = self.client.table("documents").select("*").eq("user_id", str(user_id))

            if status:
                query = query.eq("status", status.value)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

            response = query.execute()

            return [Document(**doc) for doc in response.data]

        except Exception as e:
            logger.error(f"Failed to list documents for user {user_id}: {e}")
            return []

    async def update_document(
        self,
        document_id: UUID,
        update_data: DocumentUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[Document]:
        """
        Update document.

        Args:
            document_id: Document UUID
            update_data: Update data
            user_id: Optional user ID for ownership verification

        Returns:
            Updated document or None
        """
        if not self.client:
            return None

        try:
            data = update_data.model_dump(exclude_unset=True)
            data["updated_at"] = datetime.utcnow().isoformat()

            # Convert enum to string if present
            if "status" in data and isinstance(data["status"], DocumentStatus):
                data["status"] = data["status"].value

            query = self.client.table("documents").update(data).eq("id", str(document_id))

            if user_id:
                query = query.eq("user_id", str(user_id))

            response = query.execute()

            if response.data and len(response.data) > 0:
                return Document(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            return None

    async def delete_document(self, document_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """
        Delete document.

        Args:
            document_id: Document UUID
            user_id: Optional user ID for ownership verification

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            query = self.client.table("documents").delete().eq("id", str(document_id))

            if user_id:
                query = query.eq("user_id", str(user_id))

            query.execute()

            logger.info(f"Deleted document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    # ========================================================================
    # Processing Job Operations
    # ========================================================================

    async def create_processing_job(self, job: ProcessingJobCreate) -> Optional[ProcessingJob]:
        """
        Create a new processing job record.

        Args:
            job: Job creation data

        Returns:
            Created job or None
        """
        if not self.client:
            return None

        try:
            data = {
                "document_id": str(job.document_id),
                "user_id": str(job.user_id),
                "task_id": job.task_id,
                "status": JobStatus.QUEUED.value,
                "progress": 0,
                "created_at": datetime.utcnow().isoformat(),
            }

            response = self.client.table("processing_jobs").insert(data).execute()

            if response.data and len(response.data) > 0:
                return ProcessingJob(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to create processing job: {e}")
            return None

    async def get_job_by_id(self, job_id: UUID, user_id: Optional[UUID] = None) -> Optional[ProcessingJob]:
        """
        Get processing job by ID.

        Args:
            job_id: Job UUID
            user_id: Optional user ID for ownership verification

        Returns:
            Processing job or None
        """
        if not self.client:
            return None

        try:
            query = self.client.table("processing_jobs").select("*").eq("id", str(job_id))

            if user_id:
                query = query.eq("user_id", str(user_id))

            response = query.execute()

            if response.data and len(response.data) > 0:
                return ProcessingJob(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None

    async def get_job_by_task_id(self, task_id: str) -> Optional[ProcessingJob]:
        """
        Get processing job by Celery task ID.

        Args:
            task_id: Celery task ID

        Returns:
            Processing job or None
        """
        if not self.client:
            return None

        try:
            response = self.client.table("processing_jobs").select("*").eq("task_id", task_id).execute()

            if response.data and len(response.data) > 0:
                return ProcessingJob(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get job by task_id {task_id}: {e}")
            return None

    async def update_job(self, job_id: UUID, update_data: ProcessingJobUpdate) -> Optional[ProcessingJob]:
        """
        Update processing job.

        Args:
            job_id: Job UUID
            update_data: Update data

        Returns:
            Updated job or None
        """
        if not self.client:
            return None

        try:
            data = update_data.model_dump(exclude_unset=True)

            # Convert enums to strings
            if "status" in data and isinstance(data["status"], JobStatus):
                data["status"] = data["status"].value
            if "current_step" in data:
                from app.models.job import ProcessingStep
                if isinstance(data["current_step"], ProcessingStep):
                    data["current_step"] = data["current_step"].value

            # Convert datetime objects to ISO format
            for key in ["started_at", "completed_at"]:
                if key in data and isinstance(data[key], datetime):
                    data[key] = data[key].isoformat()

            response = self.client.table("processing_jobs").update(data).eq("id", str(job_id)).execute()

            if response.data and len(response.data) > 0:
                return ProcessingJob(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            return None

    async def list_user_jobs(
        self,
        user_id: UUID,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingJob]:
        """
        List processing jobs for a user.

        Args:
            user_id: User UUID
            status: Optional status filter
            limit: Maximum number of jobs
            offset: Number of jobs to skip

        Returns:
            List of processing jobs
        """
        if not self.client:
            return []

        try:
            query = self.client.table("processing_jobs").select("*").eq("user_id", str(user_id))

            if status:
                query = query.eq("status", status.value)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

            response = query.execute()

            return [ProcessingJob(**job) for job in response.data]

        except Exception as e:
            logger.error(f"Failed to list jobs for user {user_id}: {e}")
            return []

    # ========================================================================
    # Storage Operations
    # ========================================================================

    async def upload_file(self, file_path: str, file_data: bytes, user_id: UUID) -> Optional[str]:
        """
        Upload file to Supabase Storage.

        Args:
            file_path: Path in storage bucket
            file_data: File binary data
            user_id: User UUID (for organizing files)

        Returns:
            Storage path or None if failed
        """
        if not self.client:
            return None

        try:
            # Organize files by user
            storage_path = f"{user_id}/{file_path}"

            self.client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
                storage_path,
                file_data
            )

            logger.info(f"Uploaded file to storage: {storage_path}")
            return storage_path

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return None

    async def download_file(self, storage_path: str) -> Optional[bytes]:
        """
        Download file from Supabase Storage.

        Args:
            storage_path: Path in storage bucket

        Returns:
            File binary data or None
        """
        if not self.client:
            return None

        try:
            data = self.client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).download(storage_path)

            logger.info(f"Downloaded file from storage: {storage_path}")
            return data

        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return None

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from Supabase Storage.

        Args:
            storage_path: Path in storage bucket

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).remove([storage_path])

            logger.info(f"Deleted file from storage: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    # ========================================================================
    # Health Check
    # ========================================================================

    def health_check(self) -> Dict[str, Any]:
        """
        Check Supabase connection health.

        Returns:
            Health status
        """
        if not self.client:
            return {
                "status": "disabled",
                "message": "Supabase is disabled (AUTH_ENABLED=False)"
            }

        try:
            # Simple query to check connection
            self.client.table("documents").select("id").limit(1).execute()

            return {
                "status": "healthy",
                "url": settings.SUPABASE_URL,
                "bucket": settings.SUPABASE_STORAGE_BUCKET
            }

        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# ============================================================================
# Global Service Instance
# ============================================================================

supabase_service = SupabaseService()


# ============================================================================
# Helper Functions
# ============================================================================

def get_supabase_service() -> SupabaseService:
    """
    Get Supabase service instance.

    Use this for dependency injection in FastAPI.
    """
    return supabase_service
