"""
Base service interfaces for Financial RAG System.

Provides abstract base classes for flexible, swappable services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


# ============================================================================
# Data Models
# ============================================================================

class LLMResponse(BaseModel):
    """Response from LLM service."""
    content: str
    model: str
    tokens_used: int
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}


class EmbeddingResponse(BaseModel):
    """Response from embedding service."""
    embeddings: List[List[float]]
    model: str
    dimension: int
    tokens_used: int


class Message(BaseModel):
    """Chat message."""
    role: str  # system, user, assistant
    content: str


# ============================================================================
# Abstract Service Interfaces
# ============================================================================

class BaseLLMService(ABC):
    """Abstract base class for LLM services."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from LLM.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connection to LLM service."""
        pass


class BaseEmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    async def embed_texts(
        self,
        texts: List[str],
        **kwargs
    ) -> EmbeddingResponse:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed
            **kwargs: Additional provider-specific arguments

        Returns:
            EmbeddingResponse with embeddings
        """
        pass

    @abstractmethod
    async def embed_text(
        self,
        text: str,
        **kwargs
    ) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed
            **kwargs: Additional provider-specific arguments

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connection to embedding service."""
        pass


class BaseVectorService(ABC):
    """Abstract base class for vector database services."""

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        **kwargs
    ) -> None:
        """Create a collection."""
        pass

    @abstractmethod
    async def store_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> int:
        """Store vectors with payloads."""
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def delete_vectors(
        self,
        collection_name: str,
        ids: List[str],
    ) -> None:
        """Delete vectors by IDs."""
        pass

    @abstractmethod
    async def collection_exists(
        self,
        collection_name: str,
    ) -> bool:
        """Check if collection exists."""
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connection to vector database."""
        pass
