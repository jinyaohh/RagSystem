"""
Celery tasks for async document processing.

Handles background processing of uploaded documents.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any
from uuid import UUID

from celery import Task

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.models.document import DocumentStatus
from app.models.job import JobStatus, ProcessingStep, ProcessingJobUpdate
from app.services.supabase_service import supabase_service
from app.services.document_extraction import DocumentExtractionService
from app.services.chunking import ChunkingService
from app.services.factory import get_embedding_service
from app.services.vector.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class DocumentProcessingTask(Task):
    """
    Base task class for document processing.

    Provides common functionality for updating job status.
    """

    def __init__(self):
        super().__init__()
        self.extraction_service = DocumentExtractionService()
        self.chunking_service = ChunkingService()
        self.embedding_service = get_embedding_service()
        self.vector_service = QdrantService()

    async def update_job_status(
        self,
        task_id: str,
        status: JobStatus,
        progress: int,
        current_step: ProcessingStep,
        error_message: str = None
    ):
        """Update job status in database."""
        try:
            job = await supabase_service.get_job_by_task_id(task_id)

            if not job:
                logger.warning(f"Job not found for task {task_id}")
                return

            update_data = ProcessingJobUpdate(
                status=status,
                progress=progress,
                current_step=current_step,
                error_message=error_message
            )

            if status == JobStatus.PROCESSING and not job.started_at:
                from datetime import datetime
                update_data.started_at = datetime.utcnow()

            if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                from datetime import datetime
                update_data.completed_at = datetime.utcnow()

            await supabase_service.update_job(job.id, update_data)

        except Exception as e:
            logger.error(f"Failed to update job status: {e}")


@celery_app.task(
    bind=True,
    base=DocumentProcessingTask,
    name="process_document_async",
    max_retries=3,
    default_retry_delay=60
)
def process_document_async(self, document_id: str, user_id: str) -> Dict[str, Any]:
    """
    Process document asynchronously.

    Steps:
    1. Extract text from document (25% progress)
    2. Chunk text (50% progress)
    3. Generate embeddings (75% progress)
    4. Store vectors in Qdrant (100% progress)

    Args:
        document_id: Document UUID
        user_id: User UUID

    Returns:
        Processing result dictionary
    """
    start_time = time.time()
    task_id = self.request.id

    logger.info(f"Starting document processing: {document_id} (task: {task_id})")

    try:
        # Get document from database
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        document = loop.run_until_complete(
            supabase_service.get_document_by_id(UUID(document_id), UUID(user_id))
        )

        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Update status: processing
        loop.run_until_complete(
            self.update_job_status(
                task_id,
                JobStatus.PROCESSING,
                0,
                ProcessingStep.EXTRACTION
            )
        )

        # ====================================================================
        # Step 1: Extract text (25% progress)
        # ====================================================================
        logger.info(f"Step 1/4: Extracting text from {document.filename}")

        # Download file from Supabase Storage
        file_data = loop.run_until_complete(
            supabase_service.download_file(document.storage_path)
        )

        if not file_data:
            raise ValueError("Failed to download file from storage")

        # Save temporarily for extraction
        temp_path = Path(settings.UPLOAD_DIR) / f"temp_{document_id}.{document.file_type}"
        temp_path.write_bytes(file_data)

        # Extract text
        extraction_result = loop.run_until_complete(
            self.extraction_service.extract_text(temp_path, document.file_type)
        )

        if not extraction_result.get("success"):
            raise ValueError(f"Extraction failed: {extraction_result.get('error')}")

        text = extraction_result["text"]
        total_pages = extraction_result.get("total_pages", 1)

        # Clean up temp file
        temp_path.unlink(missing_ok=True)

        # Update progress
        loop.run_until_complete(
            self.update_job_status(
                task_id,
                JobStatus.PROCESSING,
                25,
                ProcessingStep.CHUNKING
            )
        )

        logger.info(f"Extracted {len(text)} characters from {document.filename}")

        # ====================================================================
        # Step 2: Chunk text (50% progress)
        # ====================================================================
        logger.info(f"Step 2/4: Chunking text")

        metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "filename": document.filename,
            "file_type": document.file_type,
            "total_pages": total_pages
        }

        chunks = loop.run_until_complete(
            self.chunking_service.chunk_text(text, metadata)
        )

        if not chunks:
            raise ValueError("Chunking produced no results")

        loop.run_until_complete(
            self.update_job_status(
                task_id,
                JobStatus.PROCESSING,
                50,
                ProcessingStep.EMBEDDING
            )
        )

        logger.info(f"Created {len(chunks)} chunks")

        # ====================================================================
        # Step 3: Generate embeddings (75% progress)
        # ====================================================================
        logger.info(f"Step 3/4: Generating embeddings")

        chunk_texts = [chunk["content"] for chunk in chunks]

        embeddings_response = loop.run_until_complete(
            self.embedding_service.embed_texts(chunk_texts)
        )

        if not embeddings_response.success:
            raise ValueError(f"Embedding failed: {embeddings_response.error}")

        embeddings = embeddings_response.embeddings

        loop.run_until_complete(
            self.update_job_status(
                task_id,
                JobStatus.PROCESSING,
                75,
                ProcessingStep.STORAGE
            )
        )

        logger.info(f"Generated {len(embeddings)} embeddings")

        # ====================================================================
        # Step 4: Store in Qdrant (100% progress)
        # ====================================================================
        logger.info(f"Step 4/4: Storing vectors in Qdrant")

        # Prepare payloads
        payloads = []
        for i, chunk in enumerate(chunks):
            payload = {
                **chunk["metadata"],
                "content": chunk["content"],
                "chunk_index": i,
                "document_id": document_id,
                "user_id": user_id
            }
            payloads.append(payload)

        # Store in Qdrant
        loop.run_until_complete(
            self.vector_service.store_vectors(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors=embeddings,
                payloads=payloads
            )
        )

        logger.info(f"Stored {len(embeddings)} vectors in Qdrant")

        # ====================================================================
        # Update document status
        # ====================================================================
        from app.models.document import DocumentUpdate
        from datetime import datetime

        processing_time_ms = int((time.time() - start_time) * 1000)

        loop.run_until_complete(
            supabase_service.update_document(
                UUID(document_id),
                DocumentUpdate(
                    status=DocumentStatus.COMPLETED,
                    total_pages=total_pages,
                    total_chunks=len(chunks),
                    processing_time_ms=processing_time_ms,
                    processed_at=datetime.utcnow()
                ),
                UUID(user_id)
            )
        )

        # Update job status: completed
        loop.run_until_complete(
            self.update_job_status(
                task_id,
                JobStatus.COMPLETED,
                100,
                ProcessingStep.COMPLETED
            )
        )

        logger.info(
            f"✓ Document processing completed: {document_id} "
            f"({processing_time_ms}ms, {len(chunks)} chunks)"
        )

        return {
            "success": True,
            "document_id": document_id,
            "total_chunks": len(chunks),
            "total_pages": total_pages,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)

        # Update document status: failed
        try:
            loop = asyncio.get_event_loop()

            from app.models.document import DocumentUpdate

            loop.run_until_complete(
                supabase_service.update_document(
                    UUID(document_id),
                    DocumentUpdate(
                        status=DocumentStatus.FAILED,
                        error_message=str(e)
                    ),
                    UUID(user_id)
                )
            )

            # Update job status: failed
            loop.run_until_complete(
                self.update_job_status(
                    task_id,
                    JobStatus.FAILED,
                    0,
                    ProcessingStep.FAILED,
                    str(e)
                )
            )

        except Exception as update_error:
            logger.error(f"Failed to update error status: {update_error}")

        # Retry if possible
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "success": False,
            "document_id": document_id,
            "error": str(e)
        }
