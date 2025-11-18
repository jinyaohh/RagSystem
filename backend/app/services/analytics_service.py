"""
Analytics Service

Service layer for analytics data collection and retrieval.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from app.core.config import settings
from app.models.analytics import (
    DailyActivity,
    DocumentTypeStats,
    MostQueriedDocument,
    PopularQuery,
    PopularQueriesResponse,
    ProcessingStatsResponse,
    QueryLogCreate,
    StepPerformance,
    SystemMetricCreate,
    SystemOverview,
    TypePerformance,
    UserActivityResponse,
    UserAnalyticsStats,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, supabase_service):
        """Initialize analytics service with Supabase service."""
        self.supabase = supabase_service
        self.client = supabase_service.client if supabase_service else None

    # ========================================================================
    # Query Logging
    # ========================================================================

    async def log_query(self, query_log: QueryLogCreate) -> bool:
        """
        Log a query for analytics.

        Args:
            query_log: Query log data

        Returns:
            Success status
        """
        try:
            if not self.client:
                logger.warning("Supabase client not available, skipping query log")
                return False

            data = query_log.dict()
            data["user_id"] = str(data["user_id"])
            if data.get("document_ids"):
                data["document_ids"] = [str(doc_id) for doc_id in data["document_ids"]]

            result = self.client.table("query_logs").insert(data).execute()

            if result.data:
                logger.info(f"Logged query for user {query_log.user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            return False

    async def log_system_metric(self, metric: SystemMetricCreate) -> bool:
        """
        Log a system metric.

        Args:
            metric: Metric data

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            data = metric.dict()
            result = self.client.table("system_metrics").insert(data).execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Failed to log system metric: {e}")
            return False

    # ========================================================================
    # User Analytics
    # ========================================================================

    async def get_user_stats(self, user_id: UUID, days: int = 30) -> UserAnalyticsStats:
        """
        Get analytics statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            User analytics statistics
        """
        try:
            if not self.client:
                return UserAnalyticsStats()

            # Call the database function
            result = self.client.rpc(
                "get_user_analytics",
                {"p_user_id": str(user_id), "p_days": days}
            ).execute()

            if not result.data or len(result.data) == 0:
                return UserAnalyticsStats()

            data = result.data[0]

            # Get documents by type
            docs_result = self.client.table("documents").select(
                "file_type"
            ).eq("user_id", str(user_id)).execute()

            doc_types = DocumentTypeStats()
            if docs_result.data:
                for doc in docs_result.data:
                    file_type = doc.get("file_type", "").lower()
                    if file_type == "application/pdf":
                        doc_types.pdf += 1
                    elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                        doc_types.docx += 1
                    elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                        doc_types.xlsx += 1
                    elif file_type == "text/plain":
                        doc_types.txt += 1

            # Get most queried documents
            most_queried = []
            if data.get("most_queried_doc_id"):
                most_queried.append(MostQueriedDocument(
                    document_id=UUID(data["most_queried_doc_id"]),
                    filename=data.get("most_queried_doc_name", "Unknown"),
                    query_count=data.get("most_queried_doc_count", 0)
                ))

            return UserAnalyticsStats(
                total_documents=data.get("total_documents", 0),
                total_queries=data.get("total_queries", 0),
                successful_queries=data.get("successful_queries", 0),
                failed_queries=data.get("failed_queries", 0),
                total_storage_bytes=data.get("total_storage_bytes", 0),
                avg_query_time_ms=float(data.get("avg_response_time_ms", 0)),
                documents_by_type=doc_types,
                queries_last_30_days=data.get("total_queries", 0),
                most_queried_documents=most_queried
            )

        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return UserAnalyticsStats()

    async def get_user_activity(
        self,
        user_id: UUID,
        period: str = "30d"
    ) -> UserActivityResponse:
        """
        Get user activity over time.

        Args:
            user_id: User ID
            period: Time period (7d, 30d, 90d, 1y)

        Returns:
            User activity data
        """
        try:
            if not self.client:
                return UserActivityResponse(period=period, daily_queries=[], daily_uploads=[])

            # Parse period
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(period, 30)

            # Call database function
            result = self.client.rpc(
                "get_user_daily_activity",
                {"p_user_id": str(user_id), "p_days": days}
            ).execute()

            daily_queries = []
            daily_uploads = []

            if result.data:
                for row in result.data:
                    activity_date = datetime.fromisoformat(row["activity_date"]).date()
                    daily_queries.append(DailyActivity(
                        date=activity_date,
                        count=row.get("query_count", 0)
                    ))
                    daily_uploads.append(DailyActivity(
                        date=activity_date,
                        count=row.get("upload_count", 0)
                    ))

            return UserActivityResponse(
                period=period,
                daily_queries=daily_queries,
                daily_uploads=daily_uploads
            )

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return UserActivityResponse(period=period, daily_queries=[], daily_uploads=[])

    async def get_popular_queries(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> PopularQueriesResponse:
        """
        Get most popular queries for a user.

        Args:
            user_id: User ID
            limit: Number of results

        Returns:
            Popular queries
        """
        try:
            if not self.client:
                return PopularQueriesResponse(queries=[])

            # Query for popular questions
            result = self.client.from_("query_logs").select(
                "question, response_time_ms"
            ).eq(
                "user_id", str(user_id)
            ).eq(
                "status", "success"
            ).order("created_at", desc=True).limit(1000).execute()

            if not result.data:
                return PopularQueriesResponse(queries=[])

            # Aggregate by question
            question_stats: Dict[str, Dict] = {}
            for row in result.data:
                question = row["question"]
                if question not in question_stats:
                    question_stats[question] = {
                        "count": 0,
                        "total_time": 0
                    }
                question_stats[question]["count"] += 1
                question_stats[question]["total_time"] += row.get("response_time_ms", 0)

            # Convert to sorted list
            queries = []
            for question, stats in sorted(
                question_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:limit]:
                queries.append(PopularQuery(
                    question=question,
                    count=stats["count"],
                    avg_response_time_ms=stats["total_time"] / stats["count"]
                ))

            return PopularQueriesResponse(queries=queries)

        except Exception as e:
            logger.error(f"Failed to get popular queries: {e}")
            return PopularQueriesResponse(queries=[])

    # ========================================================================
    # System Analytics
    # ========================================================================

    async def get_system_overview(self) -> SystemOverview:
        """
        Get system-wide overview statistics.

        Returns:
            System overview data
        """
        try:
            if not self.client:
                return SystemOverview(
                    total_users=0,
                    active_users_30d=0,
                    total_documents=0,
                    total_queries=0,
                    total_storage_gb=0.0,
                    avg_query_latency_ms=0.0,
                    success_rate_percent=0.0
                )

            # Call database function
            result = self.client.rpc("get_system_overview").execute()

            if not result.data or len(result.data) == 0:
                return SystemOverview(
                    total_users=0,
                    active_users_30d=0,
                    total_documents=0,
                    total_queries=0,
                    total_storage_gb=0.0,
                    avg_query_latency_ms=0.0,
                    success_rate_percent=0.0
                )

            data = result.data[0]

            return SystemOverview(
                total_users=data.get("total_users", 0),
                active_users_30d=data.get("active_users_30d", 0),
                total_documents=data.get("total_documents", 0),
                total_queries=data.get("total_queries", 0),
                total_storage_gb=data.get("total_storage_bytes", 0) / (1024**3),
                avg_query_latency_ms=float(data.get("avg_query_latency_ms", 0)),
                success_rate_percent=float(data.get("success_rate_percent", 0))
            )

        except Exception as e:
            logger.error(f"Failed to get system overview: {e}")
            return SystemOverview(
                total_users=0,
                active_users_30d=0,
                total_documents=0,
                total_queries=0,
                total_storage_gb=0.0,
                avg_query_latency_ms=0.0,
                success_rate_percent=0.0
            )

    # ========================================================================
    # Processing Analytics
    # ========================================================================

    async def get_processing_stats(self) -> ProcessingStatsResponse:
        """
        Get document processing statistics.

        Returns:
            Processing statistics
        """
        try:
            if not self.client:
                return ProcessingStatsResponse(
                    avg_processing_time_ms=0.0,
                    total_processed=0,
                    processing_by_step={},
                    processing_by_type={}
                )

            # Get overall stats
            overall_result = self.client.table("processing_analytics").select(
                "duration_ms"
            ).execute()

            total_processed = len(overall_result.data) if overall_result.data else 0
            avg_processing_time_ms = 0.0
            if total_processed > 0:
                total_time = sum(row.get("duration_ms", 0) for row in overall_result.data)
                avg_processing_time_ms = total_time / total_processed

            # Get stats by step using view
            step_result = self.client.from_("processing_performance_by_step").select("*").execute()

            processing_by_step = {}
            if step_result.data:
                for row in step_result.data:
                    processing_by_step[row["step"]] = StepPerformance(
                        avg_ms=float(row.get("avg_duration_ms", 0)),
                        min_ms=float(row.get("min_duration_ms", 0)),
                        max_ms=float(row.get("max_duration_ms", 0)),
                        p50_ms=float(row.get("p50_duration_ms", 0)),
                        p95_ms=float(row.get("p95_duration_ms", 0)),
                        p99_ms=float(row.get("p99_duration_ms", 0)),
                        success_rate=float(row.get("success_rate_percent", 0))
                    )

            # Get stats by document type
            # Join with documents table to get file types
            type_result = self.client.table("processing_analytics").select(
                "duration_ms, documents(file_type)"
            ).execute()

            type_stats: Dict[str, Dict] = {}
            if type_result.data:
                for row in type_result.data:
                    doc_info = row.get("documents")
                    if doc_info:
                        file_type = doc_info.get("file_type", "unknown")
                        # Simplify type name
                        if "pdf" in file_type.lower():
                            type_name = "pdf"
                        elif "word" in file_type.lower():
                            type_name = "docx"
                        elif "excel" in file_type.lower() or "sheet" in file_type.lower():
                            type_name = "xlsx"
                        elif "text" in file_type.lower():
                            type_name = "txt"
                        else:
                            type_name = "other"

                        if type_name not in type_stats:
                            type_stats[type_name] = {"total_time": 0, "count": 0}

                        type_stats[type_name]["total_time"] += row.get("duration_ms", 0)
                        type_stats[type_name]["count"] += 1

            processing_by_type = {}
            for type_name, stats in type_stats.items():
                if stats["count"] > 0:
                    processing_by_type[type_name] = TypePerformance(
                        avg_ms=stats["total_time"] / stats["count"],
                        count=stats["count"]
                    )

            return ProcessingStatsResponse(
                avg_processing_time_ms=avg_processing_time_ms,
                total_processed=total_processed,
                processing_by_step=processing_by_step,
                processing_by_type=processing_by_type
            )

        except Exception as e:
            logger.error(f"Failed to get processing stats: {e}")
            return ProcessingStatsResponse(
                avg_processing_time_ms=0.0,
                total_processed=0,
                processing_by_step={},
                processing_by_type={}
            )

    # ========================================================================
    # Health Check
    # ========================================================================

    def health_check(self) -> Dict:
        """
        Check analytics service health.

        Returns:
            Health status dictionary
        """
        try:
            if not self.client:
                return {
                    "status": "disabled",
                    "message": "Analytics not configured"
                }

            # Simple query to check connection
            result = self.client.table("query_logs").select("id").limit(1).execute()

            return {
                "status": "healthy",
                "tables": ["query_logs", "system_metrics", "processing_analytics"]
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
