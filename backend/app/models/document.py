"""
Document models for document management and metadata.

Represents documents stored in Supabase with processing status.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"  # Uploaded, waiting for processing
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"  # Successfully processed
    FAILED = "failed"  # Processing failed


class DocumentBase(BaseModel):
    """Base document model with common attributes."""
    filename: str
    file_type: str
    file_size: int
    storage_path: str  # Path in Supabase Storage


class DocumentCreate(DocumentBase):
    """Model for creating a new document."""
    user_id: UUID
    metadata: Optional[dict] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    """Model for updating document information."""
    filename: Optional[str] = None
    status: Optional[DocumentStatus] = None
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None


class Document(DocumentBase):
    """Document model for API responses."""
    id: UUID
    user_id: UUID
    status: DocumentStatus
    processing_job_id: Optional[UUID] = None

    # Processing metadata
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    # Computed fields
    @property
    def is_processing(self) -> bool:
        """Check if document is currently processing."""
        return self.status == DocumentStatus.PROCESSING

    @property
    def is_ready(self) -> bool:
        """Check if document is ready for queries."""
        return self.status == DocumentStatus.COMPLETED

    model_config = {"from_attributes": True}


class DocumentInDB(Document):
    """Document model as stored in database."""
    file_path: str  # Local file path (for backward compatibility)


class DocumentChunk(BaseModel):
    """Represents a chunk of a document."""
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    vector_id: str  # Qdrant point ID
    metadata: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentWithChunks(Document):
    """Document with its chunks (for detailed view)."""
    chunks: list[DocumentChunk] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: list[Document]
    total: int
    page: int = 1
    page_size: int = 50


class DocumentStats(BaseModel):
    """Statistics for a single document."""
    document_id: UUID
    filename: str
    file_size: int
    total_chunks: int
    total_queries: int
    last_queried: Optional[datetime] = None
    created_at: datetime
