"""
Document management API endpoints.

Handles document upload, processing, and listing.
Supports both Phase 1 (sync) and Phase 2 (async + auth) modes.
"""

import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    status,
    BackgroundTasks,
    Depends,
)
from pydantic import BaseModel

from app.core.config import settings
from app.services.document_processor import DocumentProcessor
from app.models.user import User
from app.middleware.auth import get_current_user_optional

# Phase 2 imports (conditional)
if settings.AUTH_ENABLED:
    from app.services.supabase_service import get_supabase_service, SupabaseService
    from app.models.document import DocumentCreate, DocumentUpdate, DocumentStatus

if settings.CELERY_ENABLED:
    from app.tasks.document_tasks import process_document_async
    from app.models.job import ProcessingJobCreate, JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

# Initialize document processor
document_processor = DocumentProcessor()


# ============================================================================
# Request/Response Models
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    message: str


class DocumentProcessingResult(BaseModel):
    """Result of document processing."""
    document_id: str
    filename: str
    file_type: str
    status: str
    extraction: Optional[dict] = None
    chunking: Optional[dict] = None
    embedding: Optional[dict] = None
    storage: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: List[dict]
    total: int


# ============================================================================
# Helper Functions
# ============================================================================

async def save_upload_file(
    upload_file: UploadFile,
    destination: Path,
) -> None:
    """
    Save uploaded file to disk.

    Args:
        upload_file: FastAPI UploadFile
        destination: Destination path
    """
    try:
        with open(destination, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)

        logger.info(f"Saved uploaded file: {destination}")

    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    supabase: Optional["SupabaseService"] = Depends(get_supabase_service) if settings.AUTH_ENABLED else None,
) -> DocumentUploadResponse:
    """
    Upload a document file.

    Accepts PDF, DOCX, XLSX, and TXT files.
    File is saved but not yet processed.

    Args:
        file: Document file to upload

    Returns:
        Upload confirmation with document ID
    """
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lstrip('.').lower()

        if not document_processor.extraction_service.is_supported_format(file_ext):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. "
                       f"Supported: {', '.join(document_processor.get_supported_formats())}"
            )

        # Generate document ID
        document_id = str(uuid4())

        # Create upload directory if needed
        upload_dir = settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_dir / f"{document_id}_{file.filename}"
        await save_upload_file(file, file_path)

        # Get file size
        file_size = file_path.stat().st_size

        # Validate file size
        if file_size > settings.MAX_FILE_SIZE:
            file_path.unlink()  # Delete file
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE} bytes)"
            )

        logger.info(
            f"Uploaded document: {file.filename} "
            f"(ID: {document_id}, size: {file_size} bytes)"
        )

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            status="uploaded",
            message="File uploaded successfully. Use /documents/process/{document_id} to process it."
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/upload-and-process", response_model=DocumentProcessingResult)
async def upload_and_process_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    supabase: Optional["SupabaseService"] = Depends(get_supabase_service) if settings.AUTH_ENABLED else None,
) -> DocumentProcessingResult:
    """
    Upload and process a document.

    **Phase 1 Mode (AUTH_ENABLED=False, CELERY_ENABLED=False):**
    - Synchronous processing
    - Returns complete results immediately

    **Phase 2 Mode (AUTH_ENABLED=True or CELERY_ENABLED=True):**
    - Async processing with Celery
    - Returns job ID for status tracking
    - Document metadata stored in Supabase

    Args:
        file: Document file to upload and process
        current_user: Current authenticated user (Phase 2 only)

    Returns:
        Processing result or job ID
    """
    try:
        # First, upload the file
        upload_response = await upload_document(file, current_user, supabase)

        document_id = upload_response.document_id

        # ====================================================================
        # Phase 2: Async Processing with Celery
        # ====================================================================
        if settings.CELERY_ENABLED and current_user:
            logger.info(f"Queueing async processing for document: {document_id}")

            # Create Supabase document record
            if settings.AUTH_ENABLED and supabase:
                # Read file for Supabase Storage
                file_path = settings.UPLOAD_DIR / f"{document_id}_{upload_response.filename}"
                file_data = file_path.read_bytes()

                # Upload to Supabase Storage
                storage_path = await supabase.upload_file(
                    file_path=upload_response.filename,
                    file_data=file_data,
                    user_id=current_user.id
                )

                if storage_path:
                    # Create document record
                    document = await supabase.create_document(
                        DocumentCreate(
                            user_id=current_user.id,
                            filename=upload_response.filename,
                            file_type=upload_response.file_type,
                            file_size=upload_response.file_size,
                            storage_path=storage_path
                        )
                    )

                    if document:
                        # Queue async processing task
                        task = process_document_async.delay(
                            str(document.id),
                            str(current_user.id)
                        )

                        # Create job record
                        job = await supabase.create_processing_job(
                            ProcessingJobCreate(
                                document_id=document.id,
                                user_id=current_user.id,
                                task_id=task.id
                            )
                        )

                        # Update document with job ID
                        await supabase.update_document(
                            document.id,
                            DocumentUpdate(
                                processing_job_id=job.id if job else None,
                                status=DocumentStatus.PROCESSING
                            ),
                            current_user.id
                        )

                        logger.info(
                            f"✓ Document {document.id} queued for processing "
                            f"(task: {task.id}, job: {job.id if job else None})"
                        )

                        return DocumentProcessingResult(
                            document_id=str(document.id),
                            filename=upload_response.filename,
                            file_type=upload_response.file_type,
                            status="queued",
                            message=f"Document queued for processing. Job ID: {job.id if job else task.id}",
                            extraction={"job_id": str(job.id) if job else task.id}
                        )

        # ====================================================================
        # Phase 1: Synchronous Processing (Backward Compatible)
        # ====================================================================
        logger.info(f"Processing document synchronously: {document_id}")

        # Get file path
        file_path = settings.UPLOAD_DIR / f"{document_id}_{upload_response.filename}"

        # Process the document
        processing_result = await document_processor.process_document(
            file_path=file_path,
            document_id=document_id,
            metadata={
                'original_filename': upload_response.filename,
                'upload_date': str(Path(file_path).stat().st_mtime),
                'user_id': str(current_user.id) if current_user else None,
            }
        )

        # If Supabase enabled, update document status
        if settings.AUTH_ENABLED and current_user and supabase:
            # Find document in database
            doc = await supabase.get_document_by_id(UUID(document_id), current_user.id)
            if doc:
                await supabase.update_document(
                    doc.id,
                    DocumentUpdate(
                        status=DocumentStatus.COMPLETED if processing_result.get('status') == 'completed' else DocumentStatus.FAILED,
                        total_chunks=processing_result.get('chunking', {}).get('num_chunks'),
                        processing_time_ms=processing_result.get('processing_time_ms'),
                        processed_at=datetime.utcnow()
                    ),
                    current_user.id
                )

        return DocumentProcessingResult(**processing_result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Upload and process failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.post("/process/{document_id}", response_model=DocumentProcessingResult)
async def process_document(
    document_id: str,
) -> DocumentProcessingResult:
    """
    Process a previously uploaded document.

    Args:
        document_id: Document ID from upload

    Returns:
        Processing result
    """
    try:
        # Find the file
        upload_dir = settings.UPLOAD_DIR

        # Look for file with this document_id prefix
        matching_files = list(upload_dir.glob(f"{document_id}_*"))

        if not matching_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        file_path = matching_files[0]

        logger.info(f"Processing document: {document_id}")

        # Process the document
        processing_result = await document_processor.process_document(
            file_path=file_path,
            document_id=document_id,
        )

        return DocumentProcessingResult(**processing_result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: Optional[User] = Depends(get_current_user_optional),
    supabase: Optional["SupabaseService"] = Depends(get_supabase_service) if settings.AUTH_ENABLED else None,
) -> DocumentListResponse:
    """
    List uploaded documents.

    **Phase 1 Mode:** Lists all documents from file system
    **Phase 2 Mode:** Lists user's documents from Supabase

    Returns:
        List of documents with metadata
    """
    try:
        # ====================================================================
        # Phase 2: List from Supabase (user-scoped)
        # ====================================================================
        if settings.AUTH_ENABLED and current_user and supabase:
            logger.info(f"Listing documents for user {current_user.id}")

            docs = await supabase.list_user_documents(current_user.id, limit=100)

            documents = [
                {
                    'document_id': str(doc.id),
                    'filename': doc.filename,
                    'file_type': doc.file_type,
                    'file_size': doc.file_size,
                    'upload_date': doc.created_at.timestamp(),
                    'status': doc.status.value,
                    'total_chunks': doc.total_chunks,
                    'processing_job_id': str(doc.processing_job_id) if doc.processing_job_id else None,
                }
                for doc in docs
            ]

            return DocumentListResponse(
                documents=documents,
                total=len(documents)
            )

        # ====================================================================
        # Phase 1: List from file system (backward compatible)
        # ====================================================================
        upload_dir = settings.UPLOAD_DIR

        if not upload_dir.exists():
            return DocumentListResponse(documents=[], total=0)

        documents = []

        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                # Extract document_id from filename (format: {id}_{original_name})
                filename = file_path.name
                parts = filename.split('_', 1)

                if len(parts) == 2:
                    document_id = parts[0]
                    original_name = parts[1]
                else:
                    document_id = filename
                    original_name = filename

                file_stat = file_path.stat()

                documents.append({
                    'document_id': document_id,
                    'filename': original_name,
                    'file_type': file_path.suffix.lstrip('.'),
                    'file_size': file_stat.st_size,
                    'upload_date': file_stat.st_mtime,
                })

        # Sort by upload date (most recent first)
        documents.sort(key=lambda x: x['upload_date'], reverse=True)

        logger.info(f"Listed {len(documents)} documents")

        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    supabase: Optional["SupabaseService"] = Depends(get_supabase_service) if settings.AUTH_ENABLED else None,
) -> dict:
    """
    Delete a document and its embeddings.

    Args:
        document_id: Document ID to delete

    Returns:
        Deletion confirmation
    """
    try:
        # Find and delete file
        upload_dir = settings.UPLOAD_DIR
        matching_files = list(upload_dir.glob(f"{document_id}_*"))

        if not matching_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        file_path = matching_files[0]
        file_path.unlink()

        logger.info(f"Deleted file: {file_path}")

        # Delete from vector database
        # Note: Full implementation requires tracking chunk IDs (Phase 2)
        deletion_result = await document_processor.delete_document(document_id)

        return {
            'document_id': document_id,
            'status': 'deleted',
            'message': f'Document {document_id} deleted successfully',
            'file_deleted': True,
            'vectors_deleted': deletion_result.get('status') == 'completed',
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("/supported-formats")
async def get_supported_formats() -> dict:
    """
    Get list of supported file formats.

    Returns:
        Supported formats and limits
    """
    return {
        'supported_formats': document_processor.get_supported_formats(),
        'max_file_size_bytes': settings.MAX_FILE_SIZE,
        'max_file_size_mb': settings.MAX_FILE_SIZE / (1024 * 1024),
    }
