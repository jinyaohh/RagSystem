"""
Retrieval service for RAG pipeline.

Handles vector search and re-ranking of results.
"""

import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.services.factory import get_embedding_service, get_vector_service

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for retrieving relevant document chunks."""

    def __init__(
        self,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ):
        """
        Initialize retrieval service.

        Args:
            top_k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
        """
        self.top_k = top_k or settings.TOP_K
        self.similarity_threshold = similarity_threshold or settings.SIMILARITY_THRESHOLD

        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()

        logger.info(
            f"Initialized RetrievalService "
            f"(top_k: {self.top_k}, threshold: {self.similarity_threshold})"
        )

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Search query
            top_k: Override default top_k
            filters: Metadata filters (e.g., {'document_id': '123'})

        Returns:
            List of retrieved chunks with scores
        """
        top_k = top_k or self.top_k

        logger.info(f"Retrieving chunks for query: '{query[:100]}...'")

        # ================================================================
        # Step 1: Embed query
        # ================================================================
        query_embedding = await self.embedding_service.embed_text(query)

        logger.debug(f"Generated query embedding (dimension: {len(query_embedding)})")

        # ================================================================
        # Step 2: Search vector database
        # ================================================================
        results = await self.vector_service.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=self.similarity_threshold,
            filters=filters,
        )

        logger.info(f"Retrieved {len(results)} chunks")

        # ================================================================
        # Step 3: Format results
        # ================================================================
        formatted_results = []

        for result in results:
            formatted_result = {
                'id': result['id'],
                'score': result['score'],
                'content': result['payload'].get('content', ''),
                'metadata': {
                    k: v for k, v in result['payload'].items()
                    if k != 'content'
                },
            }
            formatted_results.append(formatted_result)

        # ================================================================
        # Step 4: Re-ranking (optional, Phase 2)
        # ================================================================
        if settings.RERANK_ENABLED:
            logger.debug("Re-ranking enabled (not yet implemented)")
            # TODO: Implement re-ranking in Phase 2
            pass

        return formatted_results

    async def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        context_window: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks with surrounding context.

        Retrieves adjacent chunks for better context.

        Args:
            query: Search query
            top_k: Number of main results
            context_window: Number of adjacent chunks to include

        Returns:
            Retrieved chunks with context
        """
        # First, do standard retrieval
        main_results = await self.retrieve(query, top_k)

        if context_window == 0 or not main_results:
            return main_results

        logger.info(f"Adding context window of {context_window} chunks")

        # TODO: Implement context window retrieval
        # This requires knowing chunk adjacency, which we'll track in Phase 2
        # For now, return main results

        return main_results

    async def hybrid_search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining dense and sparse retrieval.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Retrieved chunks
        """
        # TODO: Implement hybrid search in Phase 2
        # For now, use dense vector search only
        logger.debug("Hybrid search not yet implemented, using dense search")

        return await self.retrieve(query, top_k)

    def get_retrieval_statistics(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about retrieval results.

        Args:
            results: Retrieval results

        Returns:
            Statistics dict
        """
        if not results:
            return {
                'num_results': 0,
                'avg_score': 0,
                'min_score': 0,
                'max_score': 0,
            }

        scores = [r['score'] for r in results]

        return {
            'num_results': len(results),
            'avg_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'above_threshold': sum(
                1 for s in scores
                if s >= self.similarity_threshold
            ),
        }
