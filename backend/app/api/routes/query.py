"""
Query API endpoints for RAG system.

Handles natural language queries against uploaded documents.
"""

import logging
import time
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.core.config import settings
from app.middleware.auth import get_current_user_optional
from app.models.analytics import QueryLogCreate
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.rag import RAGService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])

# Initialize RAG service
rag_service = RAGService()


def get_analytics_service(
    supabase: SupabaseService = Depends(lambda: SupabaseService() if settings.AUTH_ENABLED else None)
) -> Optional[AnalyticsService]:
    """Get analytics service instance."""
    if not settings.AUTH_ENABLED or not supabase:
        return None
    return AnalyticsService(supabase)


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
    current_user: Optional[User] = Depends(get_current_user_optional),
    analytics: Optional[AnalyticsService] = Depends(get_analytics_service),
) -> QueryResponse:
    """
    Query documents with natural language.

    Performs RAG (Retrieval-Augmented Generation) to answer questions
    based on uploaded documents.

    Args:
        request: Query request with question and optional parameters
        current_user: Optional authenticated user (for analytics)
        analytics: Optional analytics service (for query logging)

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
    start_time = time.time()
    status_code = "success"
    error_message = None

    try:
        logger.info(f"Received query: '{request.question[:100]}...'")

        # Build filters if document_ids provided
        filters = None
        document_uuids = []
        if request.document_ids:
            logger.info(f"Filtering by document IDs: {request.document_ids}")
            # Convert to UUIDs for analytics
            try:
                document_uuids = [UUID(doc_id) for doc_id in request.document_ids]
            except ValueError:
                logger.warning("Invalid document IDs provided for filtering")

        # Execute RAG query
        result = await rag_service.query(
            question=request.question,
            top_k=request.top_k,
            filters=filters,
            include_sources=request.include_sources,
        )

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log query for analytics (if enabled and user is authenticated)
        if analytics and current_user:
            try:
                query_log = QueryLogCreate(
                    user_id=current_user.id,
                    question=request.question,
                    answer_length=len(result.get("answer", "")),
                    response_time_ms=response_time_ms,
                    num_sources=result.get("num_sources", 0),
                    document_ids=document_uuids if document_uuids else None,
                    status="success",
                    tokens_used=result.get("llm_stats", {}).get("tokens_used"),
                    model=result.get("llm_stats", {}).get("model"),
                )
                await analytics.log_query(query_log)
                logger.debug("Query logged to analytics")
            except Exception as e:
                # Don't fail the request if analytics logging fails
                logger.warning(f"Failed to log query analytics: {e}")

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        error_message = str(e)
        status_code = "failed"

        # Log failed query for analytics (if enabled and user is authenticated)
        if analytics and current_user:
            try:
                response_time_ms = int((time.time() - start_time) * 1000)
                query_log = QueryLogCreate(
                    user_id=current_user.id,
                    question=request.question,
                    answer_length=0,
                    response_time_ms=response_time_ms,
                    num_sources=0,
                    document_ids=None,
                    status="failed",
                    error_message=error_message,
                )
                await analytics.log_query(query_log)
            except Exception as analytics_error:
                logger.warning(f"Failed to log failed query analytics: {analytics_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/batch", response_model=List[QueryResponse])
async def query_batch(
    request: MultiQueryRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    analytics: Optional[AnalyticsService] = Depends(get_analytics_service),
) -> List[QueryResponse]:
    """
    Process multiple queries in batch.

    Useful for asking multiple questions about the same documents.

    Args:
        request: Batch query request
        current_user: Optional authenticated user (for analytics)
        analytics: Optional analytics service (for query logging)

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

        # Log each query in the batch (if enabled and user is authenticated)
        if analytics and current_user:
            for i, result in enumerate(results):
                try:
                    query_log = QueryLogCreate(
                        user_id=current_user.id,
                        question=request.questions[i],
                        answer_length=len(result.get("answer", "")),
                        response_time_ms=result.get("response_time_ms", 0),
                        num_sources=result.get("num_sources", 0),
                        document_ids=None,
                        status="success" if result.get("status") == "success" else "failed",
                        error_message=result.get("error") if result.get("status") == "failed" else None,
                        tokens_used=result.get("llm_stats", {}).get("tokens_used"),
                        model=result.get("llm_stats", {}).get("model"),
                    )
                    await analytics.log_query(query_log)
                except Exception as e:
                    logger.warning(f"Failed to log batch query {i} analytics: {e}")

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
