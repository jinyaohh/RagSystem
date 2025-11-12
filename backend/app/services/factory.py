"""
Service factory for creating configurable service instances.

Provides factory functions to instantiate services based on configuration.
"""

import logging
from typing import Optional

from app.core.config import settings, LLMProvider, EmbeddingProvider
from app.services.base import BaseLLMService, BaseEmbeddingService, BaseVectorService

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Service Factory
# ============================================================================

def create_llm_service(
    provider: Optional[LLMProvider] = None,
    **kwargs
) -> BaseLLMService:
    """
    Create LLM service based on configuration.

    Args:
        provider: LLM provider (defaults to settings)
        **kwargs: Additional arguments passed to service

    Returns:
        BaseLLMService instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider or settings.LLM_PROVIDER

    logger.info(f"Creating LLM service with provider: {provider.value}")

    if provider == LLMProvider.OPENAI:
        from app.services.llm.openai_service import OpenAILLMService
        return OpenAILLMService(**kwargs)

    elif provider == LLMProvider.ANTHROPIC:
        from app.services.llm.anthropic_service import AnthropicLLMService
        return AnthropicLLMService(**kwargs)

    elif provider == LLMProvider.LOCAL:
        # TODO: Implement local LLM service
        raise NotImplementedError("Local LLM provider not yet implemented")

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# ============================================================================
# Embedding Service Factory
# ============================================================================

def create_embedding_service(
    provider: Optional[EmbeddingProvider] = None,
    **kwargs
) -> BaseEmbeddingService:
    """
    Create embedding service based on configuration.

    Args:
        provider: Embedding provider (defaults to settings)
        **kwargs: Additional arguments passed to service

    Returns:
        BaseEmbeddingService instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider or settings.EMBEDDING_PROVIDER

    logger.info(f"Creating Embedding service with provider: {provider.value}")

    if provider == EmbeddingProvider.OPENAI:
        from app.services.embeddings.openai_service import OpenAIEmbeddingService
        return OpenAIEmbeddingService(**kwargs)

    elif provider in [EmbeddingProvider.LOCAL, EmbeddingProvider.SENTENCE_TRANSFORMERS]:
        # TODO: Implement local embedding service
        raise NotImplementedError("Local embedding provider not yet implemented")

    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


# ============================================================================
# Vector Service Factory
# ============================================================================

def create_vector_service(**kwargs) -> BaseVectorService:
    """
    Create vector database service.

    Currently only supports Qdrant.

    Args:
        **kwargs: Additional arguments passed to service

    Returns:
        BaseVectorService instance
    """
    logger.info("Creating Vector DB service (Qdrant)")

    from app.services.vector.qdrant_service import QdrantVectorService
    return QdrantVectorService(**kwargs)


# ============================================================================
# Singleton Instances (lazy initialization)
# ============================================================================

_llm_service: Optional[BaseLLMService] = None
_embedding_service: Optional[BaseEmbeddingService] = None
_vector_service: Optional[BaseVectorService] = None


def get_llm_service() -> BaseLLMService:
    """
    Get singleton LLM service instance.

    Returns:
        BaseLLMService instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = create_llm_service()
        logger.info("Initialized singleton LLM service")
    return _llm_service


def get_embedding_service() -> BaseEmbeddingService:
    """
    Get singleton embedding service instance.

    Returns:
        BaseEmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = create_embedding_service()
        logger.info("Initialized singleton Embedding service")
    return _embedding_service


def get_vector_service() -> BaseVectorService:
    """
    Get singleton vector service instance.

    Returns:
        BaseVectorService instance
    """
    global _vector_service
    if _vector_service is None:
        _vector_service = create_vector_service()
        logger.info("Initialized singleton Vector DB service")
    return _vector_service


async def cleanup_services():
    """
    Cleanup all service instances.

    Call this on application shutdown.
    """
    global _llm_service, _embedding_service, _vector_service

    if _llm_service:
        await _llm_service.close()
        _llm_service = None

    if _embedding_service:
        await _embedding_service.close()
        _embedding_service = None

    # Vector service doesn't need async cleanup
    _vector_service = None

    logger.info("All services cleaned up")
