"""
OpenAI LLM Service implementation.

Provides LLM functionality using OpenAI's GPT models.
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
from app.services.base import BaseLLMService, LLMResponse, Message

logger = logging.getLogger(__name__)


class OpenAILLMService(BaseLLMService):
    """OpenAI LLM service implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize OpenAI LLM service.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model name (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Maximum tokens (defaults to settings)
            timeout: Request timeout (defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        self.max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS
        self.timeout = timeout or settings.OPENAI_TIMEOUT

        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout,
        )

        logger.info(f"Initialized OpenAI LLM service with model: {self.model}")

    @retry(
        retry=retry_if_exception_type(OpenAIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using OpenAI GPT.

        Args:
            messages: Conversation messages
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            OpenAIError: If API call fails
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            # Make API call
            logger.debug(f"Calling OpenAI API with model: {self.model}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )

            # Extract response
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            logger.info(
                f"Generated response with {response.usage.total_tokens} tokens "
                f"(finish_reason: {finish_reason})"
            )

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=response.usage.total_tokens,
                finish_reason=finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                }
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in OpenAI LLM service: {e}")
            raise

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
            test_messages = [Message(role="user", content="test")]
            response = await self.generate(
                messages=test_messages,
                max_tokens=5
            )
            logger.info("OpenAI connection validated successfully")
            return True

        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (approximate).

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        # For accurate counting, use tiktoken library
        return len(text) // 4

    async def close(self):
        """Close the client connection."""
        await self.client.close()
        logger.info("OpenAI LLM service closed")
