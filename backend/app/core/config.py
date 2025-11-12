"""
Configuration management for Financial RAG System.

Uses Pydantic Settings for type-safe, environment-based configuration.
All settings can be overridden via environment variables.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    LOCAL = "local"
    SENTENCE_TRANSFORMERS = "sentence-transformers"


class ChunkStrategy(str, Enum):
    """Text chunking strategies."""
    RECURSIVE = "recursive"
    CHARACTER = "character"
    TOKEN = "token"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ========================================================================
    # Application Settings
    # ========================================================================
    APP_NAME: str = "Financial RAG System"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ========================================================================
    # API Configuration
    # ========================================================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ========================================================================
    # LLM Provider Configuration
    # ========================================================================
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI

    # OpenAI
    OPENAI_API_KEY: str = "sk-placeholder"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TIMEOUT: int = 60

    # Anthropic
    ANTHROPIC_API_KEY: str = "sk-ant-placeholder"
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    ANTHROPIC_TEMPERATURE: float = 0.1
    ANTHROPIC_MAX_TOKENS: int = 2048

    # Local LLM
    LOCAL_LLM_MODEL_PATH: Optional[str] = None
    LOCAL_LLM_MODEL_TYPE: str = "llama"

    # ========================================================================
    # Embedding Provider Configuration
    # ========================================================================
    EMBEDDING_PROVIDER: EmbeddingProvider = EmbeddingProvider.OPENAI

    # OpenAI Embeddings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 3072

    # Local Embeddings
    LOCAL_EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    LOCAL_EMBEDDING_DIMENSION: int = 768

    # ========================================================================
    # Vector Database Configuration
    # ========================================================================
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "financial_documents"
    QDRANT_USE_GRPC: bool = False

    # ========================================================================
    # Document Processing Configuration
    # ========================================================================
    UPLOAD_DIR: Path = Field(default=Path("./uploads"))
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default_factory=lambda: ["pdf", "docx", "xlsx", "txt"]
    )

    @field_validator("UPLOAD_DIR", mode="before")
    @classmethod
    def parse_upload_dir(cls, v):
        """Ensure upload directory exists."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(",")]
        return v

    # Text Chunking
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 128
    CHUNK_STRATEGY: ChunkStrategy = ChunkStrategy.RECURSIVE

    # ========================================================================
    # RAG Configuration
    # ========================================================================
    # Retrieval
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    RERANK_ENABLED: bool = False

    # Response Generation
    STREAM_RESPONSE: bool = False
    INCLUDE_SOURCES: bool = True
    MAX_CONTEXT_LENGTH: int = 4000

    # ========================================================================
    # Performance & Caching (Phase 3)
    # ========================================================================
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600

    # ========================================================================
    # Async Processing (Phase 2)
    # ========================================================================
    CELERY_ENABLED: bool = False
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ========================================================================
    # Monitoring & Logging
    # ========================================================================
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: Optional[str] = None

    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: Path = Field(default=Path("./logs/app.log"))
    LOG_ROTATION: str = "10MB"

    @field_validator("LOG_FILE_PATH", mode="before")
    @classmethod
    def ensure_log_directory(cls, v):
        """Ensure log directory exists."""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    # ========================================================================
    # Development & Testing
    # ========================================================================
    TEST_MODE: bool = False
    SAMPLE_DATA_PATH: Path = Field(default=Path("./test_data"))

    # ========================================================================
    # Computed Properties
    # ========================================================================
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    # ========================================================================
    # Validation Methods
    # ========================================================================
    def validate_llm_config(self) -> None:
        """Validate LLM configuration based on provider."""
        if self.LLM_PROVIDER == LLMProvider.OPENAI:
            if self.OPENAI_API_KEY == "sk-placeholder":
                raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")

        elif self.LLM_PROVIDER == LLMProvider.ANTHROPIC:
            if self.ANTHROPIC_API_KEY == "sk-ant-placeholder":
                raise ValueError("ANTHROPIC_API_KEY must be set when using Anthropic provider")

        elif self.LLM_PROVIDER == LLMProvider.LOCAL:
            if not self.LOCAL_LLM_MODEL_PATH:
                raise ValueError("LOCAL_LLM_MODEL_PATH must be set when using local provider")

    def validate_embedding_config(self) -> None:
        """Validate embedding configuration based on provider."""
        if self.EMBEDDING_PROVIDER == EmbeddingProvider.OPENAI:
            if self.OPENAI_API_KEY == "sk-placeholder":
                raise ValueError("OPENAI_API_KEY must be set when using OpenAI embeddings")

    def validate_config(self) -> None:
        """Validate all configuration."""
        # Skip validation in test mode
        if self.TEST_MODE:
            return

        # Validate based on active providers
        if not self.TEST_MODE:
            try:
                self.validate_llm_config()
                self.validate_embedding_config()
            except ValueError as e:
                if self.is_development:
                    print(f"⚠️  Configuration warning: {e}")
                else:
                    raise


# ============================================================================
# Global Settings Instance
# ============================================================================
settings = Settings()

# Validate configuration on import (only in production)
if settings.is_production:
    settings.validate_config()


# ============================================================================
# Helper Functions
# ============================================================================
def get_settings() -> Settings:
    """
    Get settings instance.

    Use this for dependency injection in FastAPI.
    """
    return settings


def print_config_summary():
    """Print configuration summary (for debugging)."""
    print("\n" + "=" * 70)
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 70)
    print(f"Environment: {settings.ENVIRONMENT.value}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print("-" * 70)
    print(f"LLM Provider: {settings.LLM_PROVIDER.value}")
    if settings.LLM_PROVIDER == LLMProvider.OPENAI:
        print(f"  Model: {settings.OPENAI_MODEL}")
    elif settings.LLM_PROVIDER == LLMProvider.ANTHROPIC:
        print(f"  Model: {settings.ANTHROPIC_MODEL}")
    print("-" * 70)
    print(f"Embedding Provider: {settings.EMBEDDING_PROVIDER.value}")
    if settings.EMBEDDING_PROVIDER == EmbeddingProvider.OPENAI:
        print(f"  Model: {settings.OPENAI_EMBEDDING_MODEL}")
        print(f"  Dimension: {settings.EMBEDDING_DIMENSION}")
    print("-" * 70)
    print(f"Vector DB: Qdrant @ {settings.qdrant_url}")
    print(f"Collection: {settings.QDRANT_COLLECTION_NAME}")
    print("-" * 70)
    print(f"Chunk Size: {settings.CHUNK_SIZE} tokens")
    print(f"Chunk Overlap: {settings.CHUNK_OVERLAP} tokens")
    print(f"Top-K Retrieval: {settings.TOP_K}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test configuration
    print_config_summary()
