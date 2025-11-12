"""
Query API endpoints for RAG system.

Handles natural language queries against uploaded documents.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.rag import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])

# Initialize RAG service
rag_service = RAGService()


# ============================================================================
# Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for queries."""
    question: str = Field(..., min_length=1, description="Question to ask about documents")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")
    include_sources: Optional[bool] = Field(None, description="Include source citations")
    document_ids: Optional[List[str]] = Field(None, description="Filter by specific document IDs")


class QueryResponse(BaseModel):
    """Response model for queries."""
    question: str
    answer: str
    status: str
    response_time_ms: int
    retrieval_stats: Optional[dict] = None
    llm_stats: Optional[dict] = None
    sources: Optional[List[dict]] = None
    num_sources: Optional[int] = None
    error: Optional[str] = None


class MultiQueryRequest(BaseModel):
    """Request model for multiple queries."""
    questions: List[str] = Field(..., min_items=1, max_items=10)
    top_k: Optional[int] = None
    include_sources: Optional[bool] = None


class SummarizeRequest(BaseModel):
    """Request model for document summarization."""
    document_id: str
    max_length: Optional[int] = Field(None, ge=50, le=1000, description="Max words in summary")


class CompareRequest(BaseModel):
    """Request model for document comparison."""
    query: str
    document_id_a: str
    document_id_b: str
    label_a: Optional[str] = Field("Document A", description="Label for first document")
    label_b: Optional[str] = Field("Document B", description="Label for second document")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
) -> QueryResponse:
    """
    Query documents with natural language.

    Performs RAG (Retrieval-Augmented Generation) to answer questions
    based on uploaded documents.

    Args:
        request: Query request with question and optional parameters

    Returns:
        Answer with sources and statistics

    Examples:
        ```json
        {
            "question": "What was the total revenue in Q4 2023?",
            "top_k": 5,
            "include_sources": true
        }
        ```
    """
    try:
        logger.info(f"Received query: '{request.question[:100]}...'")

        # Build filters if document_ids provided
        filters = None
        if request.document_ids:
            # Note: Proper multi-value filtering will be implemented in Phase 2
            logger.info(f"Filtering by document IDs: {request.document_ids}")
            # For now, we'll search across all documents

        # Execute RAG query
        result = await rag_service.query(
            question=request.question,
            top_k=request.top_k,
            filters=filters,
            include_sources=request.include_sources,
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/batch", response_model=List[QueryResponse])
async def query_batch(
    request: MultiQueryRequest,
) -> List[QueryResponse]:
    """
    Process multiple queries in batch.

    Useful for asking multiple questions about the same documents.

    Args:
        request: Batch query request

    Returns:
        List of query responses
    """
    try:
        logger.info(f"Received batch query: {len(request.questions)} questions")

        results = await rag_service.multi_query(
            questions=request.questions,
            top_k=request.top_k,
            include_sources=request.include_sources,
        )

        return [QueryResponse(**result) for result in results]

    except Exception as e:
        logger.error(f"Batch query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch query failed: {str(e)}"
        )


@router.post("/summarize")
async def summarize_document(
    request: SummarizeRequest,
) -> dict:
    """
    Generate a summary of a document.

    Args:
        request: Summarization request

    Returns:
        Document summary
    """
    try:
        logger.info(f"Summarizing document: {request.document_id}")

        result = await rag_service.summarize_document(
            document_id=request.document_id,
            max_length=request.max_length,
        )

        if result['status'] == 'failed':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if 'not found' in result.get('error', '').lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Summarization failed')
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )


@router.post("/compare")
async def compare_documents(
    request: CompareRequest,
) -> dict:
    """
    Compare information from two documents.

    Args:
        request: Comparison request

    Returns:
        Comparison result
    """
    try:
        logger.info(
            f"Comparing documents: {request.document_id_a} vs {request.document_id_b}"
        )

        result = await rag_service.compare_documents(
            query=request.query,
            document_id_a=request.document_id_a,
            document_id_b=request.document_id_b,
            label_a=request.label_a,
            label_b=request.label_b,
        )

        if result['status'] == 'failed':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if 'not found' in result.get('error', '').lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Comparison failed')
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )


@router.get("/info")
async def get_query_service_info() -> dict:
    """
    Get information about query service configuration.

    Returns:
        Service configuration details
    """
    return rag_service.get_service_info()
