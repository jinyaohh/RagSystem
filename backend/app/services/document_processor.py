"""
Document processing pipeline.

Orchestrates the complete document processing workflow:
1. Extract text from document
2. Chunk text into pieces
3. Generate embeddings
4. Store in vector database
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

from app.core.config import settings
from app.services.document_extraction import DocumentExtractionService
from app.services.chunking import ChunkingService
from app.services.factory import get_embedding_service, get_vector_service

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Complete document processing pipeline."""

    def __init__(self):
        """Initialize document processor."""
        self.extraction_service = DocumentExtractionService()
        self.chunking_service = ChunkingService()
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()

        logger.info("Initialized DocumentProcessor")

    async def process_document(
        self,
        file_path: Path,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline.

        Args:
            file_path: Path to document file
            document_id: Optional document ID (generates UUID if not provided)
            metadata: Additional metadata to attach

        Returns:
            Processing result with statistics

        Raises:
            Exception: If any step fails
        """
        document_id = document_id or str(uuid4())
        metadata = metadata or {}

        logger.info(f"Processing document: {file_path.name} (ID: {document_id})")

        result = {
            'document_id': document_id,
            'filename': file_path.name,
            'file_type': file_path.suffix.lstrip('.').lower(),
            'status': 'processing',
        }

        try:
            # ================================================================
            # Step 1: Extract text
            # ================================================================
            logger.info(f"[{document_id}] Step 1/4: Extracting text...")

            extraction_result = await self.extraction_service.extract_text(file_path)

            text = extraction_result['text']
            doc_metadata = extraction_result['metadata']

            result['extraction'] = {
                'text_length': len(text),
                'metadata': doc_metadata,
            }

            logger.info(
                f"[{document_id}] Extracted {len(text)} characters "
                f"({doc_metadata.get('num_pages', 'N/A')} pages)"
            )

            if not text or len(text) < 100:
                raise ValueError("Extracted text is too short or empty")

            # ================================================================
            # Step 2: Chunk text
            # ================================================================
            logger.info(f"[{document_id}] Step 2/4: Chunking text...")

            # Combine metadata
            chunk_metadata = {
                **metadata,
                'document_id': document_id,
                'filename': file_path.name,
                'file_type': result['file_type'],
                **doc_metadata,
            }

            chunks = await self.chunking_service.chunk_text(
                text=text,
                metadata=chunk_metadata,
            )

            result['chunking'] = {
                'num_chunks': len(chunks),
                'avg_chunk_size': sum(len(c['content']) for c in chunks) / len(chunks) if chunks else 0,
            }

            logger.info(f"[{document_id}] Created {len(chunks)} chunks")

            if not chunks:
                raise ValueError("No chunks created from document")

            # ================================================================
            # Step 3: Generate embeddings
            # ================================================================
            logger.info(f"[{document_id}] Step 3/4: Generating embeddings...")

            # Extract texts for embedding
            chunk_texts = [chunk['content'] for chunk in chunks]

            # Generate embeddings (batch for efficiency)
            embeddings_response = await self.embedding_service.embed_texts(chunk_texts)
            embeddings = embeddings_response.embeddings

            result['embedding'] = {
                'model': embeddings_response.model,
                'dimension': embeddings_response.dimension,
                'tokens_used': embeddings_response.tokens_used,
            }

            logger.info(
                f"[{document_id}] Generated {len(embeddings)} embeddings "
                f"(tokens: {embeddings_response.tokens_used})"
            )

            # ================================================================
            # Step 4: Store in vector database
            # ================================================================
            logger.info(f"[{document_id}] Step 4/4: Storing in vector database...")

            # Ensure collection exists
            await self.vector_service.ensure_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                dimension=embeddings_response.dimension,
            )

            # Prepare payloads (metadata for each chunk)
            payloads = [chunk['metadata'] for chunk in chunks]

            # Add chunk content to payloads
            for i, chunk in enumerate(chunks):
                payloads[i]['content'] = chunk['content']

            # Generate IDs for chunks
            chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]

            # Store in Qdrant
            num_stored = await self.vector_service.store_vectors(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors=embeddings,
                payloads=payloads,
                ids=chunk_ids,
            )

            result['storage'] = {
                'num_stored': num_stored,
                'collection': settings.QDRANT_COLLECTION_NAME,
                'chunk_ids': chunk_ids,
            }

            logger.info(f"[{document_id}] Stored {num_stored} vectors in Qdrant")

            # ================================================================
            # Complete
            # ================================================================
            result['status'] = 'completed'
            result['message'] = 'Document processed successfully'

            logger.info(
                f"✓ Document processing complete: {file_path.name} "
                f"({len(chunks)} chunks, {embeddings_response.tokens_used} tokens)"
            )

            return result

        except Exception as e:
            logger.error(f"Document processing failed: {e}", exc_info=True)

            result['status'] = 'failed'
            result['error'] = str(e)

            raise

    async def process_multiple_documents(
        self,
        file_paths: List[Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents.

        Args:
            file_paths: List of file paths
            metadata: Shared metadata for all documents

        Returns:
            List of processing results
        """
        logger.info(f"Processing {len(file_paths)} documents")

        results = []

        for file_path in file_paths:
            try:
                result = await self.process_document(file_path, metadata=metadata)
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")
                results.append({
                    'filename': file_path.name,
                    'status': 'failed',
                    'error': str(e),
                })

        successful = sum(1 for r in results if r['status'] == 'completed')
        logger.info(f"Processed {successful}/{len(file_paths)} documents successfully")

        return results

    async def delete_document(
        self,
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Delete a document from the vector database.

        Args:
            document_id: Document ID

        Returns:
            Deletion result
        """
        logger.info(f"Deleting document: {document_id}")

        try:
            # Search for all chunk IDs for this document
            # Note: This is a simplified version. In production, you'd
            # want to store chunk IDs in a database for efficient lookup.

            # For now, we'll use a filter to find all chunks
            # This assumes chunk IDs follow the pattern: {document_id}_{index}

            # In Qdrant, we can't directly get IDs by pattern,
            # so we'd need to search and then delete
            # This is a limitation we'll address in Phase 2 with Supabase

            logger.warning(
                "Document deletion requires database integration "
                "(will be implemented in Phase 2)"
            )

            return {
                'document_id': document_id,
                'status': 'pending',
                'message': 'Full deletion requires database integration',
            }

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.

        Returns:
            List of supported extensions
        """
        return self.extraction_service.get_supported_formats()

    def validate_file(
        self,
        file_path: Path,
        max_size_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Validate a file before processing.

        Args:
            file_path: Path to file
            max_size_bytes: Maximum file size (defaults to settings)

        Returns:
            Validation result dict

        Raises:
            ValueError: If validation fails
        """
        max_size_bytes = max_size_bytes or settings.MAX_FILE_SIZE

        # Check file exists
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Check file type
        file_type = file_path.suffix.lstrip('.').lower()
        if file_type not in self.get_supported_formats():
            raise ValueError(
                f"Unsupported file type: {file_type}. "
                f"Supported: {', '.join(self.get_supported_formats())}"
            )

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > max_size_bytes:
            raise ValueError(
                f"File too large: {file_size} bytes "
                f"(max: {max_size_bytes} bytes)"
            )

        # Check file is readable
        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        return {
            'valid': True,
            'filename': file_path.name,
            'file_type': file_type,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
        }
