"""
Text chunking service for splitting documents into manageable pieces.

Supports multiple chunking strategies for optimal retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
import re

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
)

from app.core.config import settings, ChunkStrategy

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for chunking text documents."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: Optional[ChunkStrategy] = None,
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Size of each chunk in characters/tokens
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy to use
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.strategy = strategy or settings.CHUNK_STRATEGY

        # Initialize splitters
        self._init_splitters()

        logger.info(
            f"Initialized ChunkingService "
            f"(strategy: {self.strategy.value}, "
            f"size: {self.chunk_size}, overlap: {self.chunk_overlap})"
        )

    def _init_splitters(self):
        """Initialize text splitters for different strategies."""
        # Recursive splitter (default, best for most cases)
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence ends
                "! ",
                "? ",
                "; ",
                ": ",
                ", ",
                " ",     # Words
                "",      # Characters
            ],
            keep_separator=True,
        )

        # Character splitter (simple split)
        self.character_splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separator="\n\n",
            keep_separator=True,
        )

        # Token splitter (splits by tokens, more precise)
        self.token_splitter = TokenTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        strategy: Optional[ChunkStrategy] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
            strategy: Override default chunking strategy

        Returns:
            List of chunks with metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        strategy = strategy or self.strategy
        metadata = metadata or {}

        logger.info(
            f"Chunking text ({len(text)} characters) "
            f"using {strategy.value} strategy"
        )

        # Select splitter based on strategy
        if strategy == ChunkStrategy.RECURSIVE:
            splitter = self.recursive_splitter
        elif strategy == ChunkStrategy.CHARACTER:
            splitter = self.character_splitter
        elif strategy == ChunkStrategy.TOKEN:
            splitter = self.token_splitter
        else:
            logger.warning(f"Unknown strategy {strategy}, using recursive")
            splitter = self.recursive_splitter

        # Split text
        text_chunks = splitter.split_text(text)

        # Create chunk objects with metadata
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = {
                'content': chunk_text,
                'metadata': {
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(text_chunks),
                    'chunk_size': len(chunk_text),
                    'chunking_strategy': strategy.value,
                }
            }
            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} chunks")

        return chunks

    async def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents.

        Args:
            documents: List of documents with 'text' and 'metadata' fields

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []

        for doc in documents:
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})

            chunks = await self.chunk_text(text, metadata)
            all_chunks.extend(chunks)

        logger.info(
            f"Chunked {len(documents)} documents into {len(all_chunks)} chunks"
        )

        return all_chunks

    def estimate_chunks(self, text: str) -> int:
        """
        Estimate number of chunks for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated number of chunks
        """
        # Rough estimation
        text_length = len(text)
        effective_chunk_size = self.chunk_size - self.chunk_overlap

        if effective_chunk_size <= 0:
            return 1

        estimated = (text_length - self.chunk_size) // effective_chunk_size + 1
        return max(1, estimated)

    async def chunk_with_metadata_preservation(
        self,
        text: str,
        page_markers: Optional[List[int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk text while preserving page information.

        Useful for PDFs where page numbers matter for citations.

        Args:
            text: Text to chunk
            page_markers: Character positions where pages start
            metadata: Base metadata

        Returns:
            Chunks with page information
        """
        if not page_markers:
            # No page markers, use standard chunking
            return await self.chunk_text(text, metadata)

        chunks = []

        # Split by pages first
        pages = self._split_by_pages(text, page_markers)

        for page_num, page_text in pages:
            # Chunk each page
            page_metadata = {
                **(metadata or {}),
                'page_number': page_num,
            }

            page_chunks = await self.chunk_text(page_text, page_metadata)
            chunks.extend(page_chunks)

        logger.info(f"Created {len(chunks)} chunks across {len(pages)} pages")

        return chunks

    def _split_by_pages(
        self,
        text: str,
        page_markers: List[int],
    ) -> List[tuple[int, str]]:
        """
        Split text by page markers.

        Args:
            text: Full text
            page_markers: Character positions of page starts

        Returns:
            List of (page_number, page_text) tuples
        """
        pages = []

        for i, start_pos in enumerate(page_markers):
            page_num = i + 1

            # Get end position (next marker or end of text)
            end_pos = page_markers[i + 1] if i + 1 < len(page_markers) else len(text)

            page_text = text[start_pos:end_pos]
            pages.append((page_num, page_text))

        return pages

    async def smart_chunk_with_context(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        context_lines: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Smart chunking that includes context from adjacent chunks.

        Adds a few lines from previous/next chunks for better context.

        Args:
            text: Text to chunk
            metadata: Metadata
            context_lines: Number of context lines to include

        Returns:
            Chunks with context
        """
        # First, do standard chunking
        chunks = await self.chunk_text(text, metadata)

        if len(chunks) <= 1:
            return chunks

        # Add context to each chunk
        for i, chunk in enumerate(chunks):
            context_before = ""
            context_after = ""

            # Add context from previous chunk
            if i > 0:
                prev_lines = chunks[i - 1]['content'].split('\n')
                context_before = '\n'.join(prev_lines[-context_lines:])

            # Add context from next chunk
            if i < len(chunks) - 1:
                next_lines = chunks[i + 1]['content'].split('\n')
                context_after = '\n'.join(next_lines[:context_lines])

            # Update chunk with context
            chunk['metadata']['context_before'] = context_before
            chunk['metadata']['context_after'] = context_after

        logger.info(f"Added context to {len(chunks)} chunks")

        return chunks

    def get_chunk_statistics(
        self,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about chunks.

        Args:
            chunks: List of chunks

        Returns:
            Statistics dict
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
            }

        chunk_sizes = [len(chunk['content']) for chunk in chunks]

        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'total_characters': sum(chunk_sizes),
        }
