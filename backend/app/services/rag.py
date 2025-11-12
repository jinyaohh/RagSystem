"""
Complete RAG (Retrieval-Augmented Generation) service.

Orchestrates the full RAG pipeline: retrieve, prompt, generate.
"""

import logging
import time
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.services.retrieval import RetrievalService
from app.services.prompts import PromptService
from app.services.factory import get_llm_service

logger = logging.getLogger(__name__)


class RAGService:
    """Complete RAG service orchestrating retrieval and generation."""

    def __init__(self):
        """Initialize RAG service."""
        self.retrieval_service = RetrievalService()
        self.prompt_service = PromptService()
        self.llm_service = get_llm_service()

        logger.info("Initialized RAGService")

    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_sources: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Execute complete RAG query.

        Args:
            question: User's question
            top_k: Number of chunks to retrieve
            filters: Metadata filters for retrieval
            include_sources: Include source citations

        Returns:
            Query result with answer and sources
        """
        start_time = time.time()
        include_sources = include_sources if include_sources is not None else settings.INCLUDE_SOURCES

        logger.info(f"Processing RAG query: '{question[:100]}...'")

        result = {
            'question': question,
            'status': 'processing',
        }

        try:
            # ================================================================
            # Step 1: Retrieve relevant chunks
            # ================================================================
            logger.debug("Step 1/3: Retrieving relevant chunks...")

            retrieved_chunks = await self.retrieval_service.retrieve(
                query=question,
                top_k=top_k,
                filters=filters,
            )

            if not retrieved_chunks:
                logger.warning("No relevant chunks found")
                return {
                    **result,
                    'status': 'completed',
                    'answer': "I couldn't find any relevant information in the documents to answer your question. Please try rephrasing your question or upload more documents.",
                    'sources': [],
                    'retrieval_stats': {
                        'num_chunks': 0,
                        'avg_score': 0,
                    }
                }

            retrieval_stats = self.retrieval_service.get_retrieval_statistics(retrieved_chunks)

            logger.info(
                f"Retrieved {len(retrieved_chunks)} chunks "
                f"(avg score: {retrieval_stats['avg_score']:.3f})"
            )

            # ================================================================
            # Step 2: Create prompt with context
            # ================================================================
            logger.debug("Step 2/3: Creating prompt...")

            messages = self.prompt_service.create_rag_prompt(
                question=question,
                retrieved_chunks=retrieved_chunks,
            )

            # ================================================================
            # Step 3: Generate answer with LLM
            # ================================================================
            logger.debug("Step 3/3: Generating answer...")

            llm_response = await self.llm_service.generate(messages=messages)

            answer = llm_response.content

            logger.info(
                f"Generated answer ({llm_response.tokens_used} tokens, "
                f"finish_reason: {llm_response.finish_reason})"
            )

            # ================================================================
            # Format response
            # ================================================================
            elapsed_time = time.time() - start_time

            result = {
                'question': question,
                'answer': answer,
                'status': 'completed',
                'response_time_ms': int(elapsed_time * 1000),
                'retrieval_stats': retrieval_stats,
                'llm_stats': {
                    'model': llm_response.model,
                    'tokens_used': llm_response.tokens_used,
                    'finish_reason': llm_response.finish_reason,
                },
            }

            # Add sources if requested
            if include_sources:
                result['sources'] = self.prompt_service.format_sources(retrieved_chunks)
                result['num_sources'] = len(retrieved_chunks)

            logger.info(
                f"✓ RAG query completed in {elapsed_time:.2f}s "
                f"({llm_response.tokens_used} tokens)"
            )

            return result

        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)

            elapsed_time = time.time() - start_time

            return {
                **result,
                'status': 'failed',
                'error': str(e),
                'response_time_ms': int(elapsed_time * 1000),
            }

    async def multi_query(
        self,
        questions: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process multiple queries.

        Args:
            questions: List of questions
            **kwargs: Additional arguments for query()

        Returns:
            List of query results
        """
        logger.info(f"Processing {len(questions)} queries")

        results = []

        for question in questions:
            result = await self.query(question, **kwargs)
            results.append(result)

        successful = sum(1 for r in results if r['status'] == 'completed')
        logger.info(f"Completed {successful}/{len(questions)} queries")

        return results

    async def query_with_filters(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        date_range: Optional[tuple] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query with specific filters.

        Args:
            question: User's question
            document_ids: Filter by document IDs
            date_range: Filter by date range (start, end)
            **kwargs: Additional arguments

        Returns:
            Query result
        """
        filters = {}

        if document_ids:
            # Note: Qdrant filtering by list requires proper setup
            # This is simplified for Phase 1
            logger.info(f"Filtering by document IDs: {document_ids}")
            # In Phase 2, we'll implement proper multi-value filtering

        if date_range:
            logger.info(f"Filtering by date range: {date_range}")
            # Implement date filtering in Phase 2

        return await self.query(question, filters=filters, **kwargs)

    async def summarize_document(
        self,
        document_id: str,
        max_length: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate summary of a document.

        Args:
            document_id: Document ID to summarize
            max_length: Maximum summary length in words

        Returns:
            Summary result
        """
        logger.info(f"Summarizing document: {document_id}")

        try:
            # Retrieve all chunks for the document
            chunks = await self.retrieval_service.retrieve(
                query="",  # Empty query to get all chunks
                top_k=100,  # Get many chunks
                filters={'document_id': document_id},
            )

            if not chunks:
                return {
                    'status': 'failed',
                    'error': 'Document not found or has no content',
                }

            # Combine chunk contents
            full_text = "\n\n".join(chunk['content'] for chunk in chunks)

            # Create summarization prompt
            messages = self.prompt_service.create_summarization_prompt(
                text=full_text,
                max_length=max_length,
            )

            # Generate summary
            llm_response = await self.llm_service.generate(messages=messages)

            return {
                'document_id': document_id,
                'summary': llm_response.content,
                'status': 'completed',
                'num_chunks': len(chunks),
                'tokens_used': llm_response.tokens_used,
            }

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {
                'document_id': document_id,
                'status': 'failed',
                'error': str(e),
            }

    async def compare_documents(
        self,
        query: str,
        document_id_a: str,
        document_id_b: str,
        label_a: str = "Document A",
        label_b: str = "Document B",
    ) -> Dict[str, Any]:
        """
        Compare information from two documents.

        Args:
            query: Comparison question
            document_id_a: First document ID
            document_id_b: Second document ID
            label_a: Label for first document
            label_b: Label for second document

        Returns:
            Comparison result
        """
        logger.info(f"Comparing documents: {document_id_a} vs {document_id_b}")

        try:
            # Retrieve chunks from both documents
            chunks_a = await self.retrieval_service.retrieve(
                query=query,
                filters={'document_id': document_id_a},
            )

            chunks_b = await self.retrieval_service.retrieve(
                query=query,
                filters={'document_id': document_id_b},
            )

            if not chunks_a or not chunks_b:
                return {
                    'status': 'failed',
                    'error': 'One or both documents not found or have no relevant content',
                }

            # Create comparison prompt
            messages = self.prompt_service.create_comparison_prompt(
                query=query,
                chunks_a=chunks_a,
                chunks_b=chunks_b,
                label_a=label_a,
                label_b=label_b,
            )

            # Generate comparison
            llm_response = await self.llm_service.generate(messages=messages)

            return {
                'query': query,
                'comparison': llm_response.content,
                'status': 'completed',
                'documents': {
                    document_id_a: {
                        'label': label_a,
                        'num_chunks': len(chunks_a),
                    },
                    document_id_b: {
                        'label': label_b,
                        'num_chunks': len(chunks_b),
                    },
                },
                'tokens_used': llm_response.tokens_used,
            }

        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
            }

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about RAG service configuration.

        Returns:
            Service configuration info
        """
        return {
            'retrieval': {
                'top_k': self.retrieval_service.top_k,
                'similarity_threshold': self.retrieval_service.similarity_threshold,
            },
            'llm': {
                'provider': settings.LLM_PROVIDER.value,
                'model': self.llm_service.get_model_name(),
            },
            'embedding': {
                'provider': settings.EMBEDDING_PROVIDER.value,
                'model': self.retrieval_service.embedding_service.get_model_name(),
                'dimension': self.retrieval_service.embedding_service.get_dimension(),
            },
            'settings': {
                'include_sources': settings.INCLUDE_SOURCES,
                'max_context_length': settings.MAX_CONTEXT_LENGTH,
                'stream_response': settings.STREAM_RESPONSE,
            },
        }
