"""
OpenAI Embedding Service implementation.

Provides embedding functionality using OpenAI's embedding models.
"""

import logging
from typing import List, Optional

from openai import AsyncOpenAI, OpenAIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.services.base import BaseEmbeddingService, EmbeddingResponse

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(BaseEmbeddingService):
    """OpenAI embedding service implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize OpenAI embedding service.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Embedding model name (defaults to settings)
            dimension: Embedding dimension (defaults to settings)
            timeout: Request timeout (defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.timeout = timeout or settings.OPENAI_TIMEOUT

        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout,
        )

        logger.info(
            f"Initialized OpenAI Embedding service "
            f"(model: {self.model}, dimension: {self.dimension})"
        )

    @retry(
        retry=retry_if_exception_type(OpenAIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed_texts(
        self,
        texts: List[str],
        **kwargs
    ) -> EmbeddingResponse:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            EmbeddingResponse with embeddings

        Raises:
            OpenAIError: If API call fails
        """
        try:
            # Make API call
            logger.debug(f"Embedding {len(texts)} texts with model: {self.model}")
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                **kwargs
            )

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]

            logger.info(
                f"Generated {len(embeddings)} embeddings "
                f"using {response.usage.total_tokens} tokens"
            )

            return EmbeddingResponse(
                embeddings=embeddings,
                model=response.model,
                dimension=len(embeddings[0]) if embeddings else self.dimension,
                tokens_used=response.usage.total_tokens,
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in OpenAI embedding service: {e}")
            raise

    async def embed_text(
        self,
        text: str,
        **kwargs
    ) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            Embedding vector
        """
        response = await self.embed_texts([text], **kwargs)
        return response.embeddings[0]

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model

    async def validate_connection(self) -> bool:
        """
        Validate connection to OpenAI API.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try a minimal API call
            await self.embed_text("test")
            logger.info("OpenAI embedding connection validated successfully")
            return True

        except Exception as e:
            logger.error(f"OpenAI embedding connection validation failed: {e}")
            return False

    async def batch_embed_with_rate_limit(
        self,
        texts: List[str],
        batch_size: int = 100,
    ) -> List[List[float]]:
        """
        Embed texts in batches to respect rate limits.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1} ({len(batch)} texts)")

            response = await self.embed_texts(batch)
            all_embeddings.extend(response.embeddings)

        logger.info(f"Embedded {len(texts)} texts in batches of {batch_size}")
        return all_embeddings

    async def close(self):
        """Close the client connection."""
        await self.client.close()
        logger.info("OpenAI Embedding service closed")
