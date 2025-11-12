"""
Qdrant Vector Database Service implementation.

Provides vector storage and search functionality using Qdrant.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from qdrant_client.http import models

from app.core.config import settings
from app.services.base import BaseVectorService

logger = logging.getLogger(__name__)


class QdrantVectorService(BaseVectorService):
    """Qdrant vector database service implementation."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        use_grpc: Optional[bool] = None,
    ):
        """
        Initialize Qdrant service.

        Args:
            host: Qdrant host (defaults to settings)
            port: Qdrant port (defaults to settings)
            api_key: Qdrant API key (defaults to settings)
            use_grpc: Use gRPC instead of HTTP (defaults to settings)
        """
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.use_grpc = use_grpc if use_grpc is not None else settings.QDRANT_USE_GRPC

        # Initialize async client
        self.client = AsyncQdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
            prefer_grpc=self.use_grpc,
        )

        logger.info(
            f"Initialized Qdrant service at {self.host}:{self.port} "
            f"(gRPC: {self.use_grpc})"
        )

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance: Distance = Distance.COSINE,
        **kwargs
    ) -> None:
        """
        Create a vector collection.

        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            distance: Distance metric (COSINE, EUCLID, DOT)
            **kwargs: Additional Qdrant-specific parameters
        """
        try:
            # Check if collection exists
            exists = await self.collection_exists(collection_name)
            if exists:
                logger.info(f"Collection '{collection_name}' already exists")
                return

            # Create collection
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=distance,
                ),
                **kwargs
            )

            logger.info(
                f"Created collection '{collection_name}' "
                f"(dimension: {dimension}, distance: {distance.value})"
            )

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    async def store_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> int:
        """
        Store vectors with payloads in collection.

        Args:
            collection_name: Name of the collection
            vectors: List of vectors
            payloads: List of payload dicts (metadata)
            ids: Optional list of IDs (generates UUIDs if not provided)

        Returns:
            Number of vectors stored

        Raises:
            ValueError: If lengths don't match
        """
        if len(vectors) != len(payloads):
            raise ValueError("Number of vectors and payloads must match")

        if ids and len(ids) != len(vectors):
            raise ValueError("Number of IDs must match number of vectors")

        try:
            # Generate IDs if not provided
            if not ids:
                ids = [str(uuid4()) for _ in range(len(vectors))]

            # Create points
            points = [
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
                for point_id, vector, payload in zip(ids, vectors, payloads)
            ]

            # Upsert points
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            logger.info(f"Stored {len(points)} vectors in '{collection_name}'")
            return len(points)

        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
            raise

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filters: Metadata filters

        Returns:
            List of search results with payload and score
        """
        try:
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filters.items()
                ]
                qdrant_filter = Filter(must=conditions)

            # Search
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=qdrant_filter,
            )

            # Format results
            formatted_results = [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results
            ]

            logger.info(
                f"Found {len(formatted_results)} results in '{collection_name}' "
                f"(top_k: {top_k})"
            )

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise

    async def delete_vectors(
        self,
        collection_name: str,
        ids: List[str],
    ) -> None:
        """
        Delete vectors by IDs.

        Args:
            collection_name: Name of the collection
            ids: List of vector IDs to delete
        """
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=ids,
                ),
            )

            logger.info(f"Deleted {len(ids)} vectors from '{collection_name}'")

        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise

    async def collection_exists(
        self,
        collection_name: str,
    ) -> bool:
        """
        Check if collection exists.

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists, False otherwise
        """
        try:
            collections = await self.client.get_collections()
            return collection_name in [c.name for c in collections.collections]

        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

    async def get_collection_info(
        self,
        collection_name: str,
    ) -> Dict[str, Any]:
        """
        Get collection information.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection info dict
        """
        try:
            info = await self.client.get_collection(collection_name)

            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "config": {
                    "dimension": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance.value,
                }
            }

        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            raise

    async def validate_connection(self) -> bool:
        """
        Validate connection to Qdrant.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to get collections
            await self.client.get_collections()
            logger.info("Qdrant connection validated successfully")
            return True

        except Exception as e:
            logger.error(f"Qdrant connection validation failed: {e}")
            return False

    async def ensure_collection(
        self,
        collection_name: str,
        dimension: int,
    ) -> None:
        """
        Ensure collection exists, create if not.

        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
        """
        exists = await self.collection_exists(collection_name)
        if not exists:
            await self.create_collection(collection_name, dimension)
            logger.info(f"Created collection: {collection_name}")
        else:
            logger.debug(f"Collection already exists: {collection_name}")
