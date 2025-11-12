"""
Anthropic Claude LLM Service implementation.

Provides LLM functionality using Anthropic's Claude models.
"""

import logging
from typing import List, Optional

from anthropic import AsyncAnthropic, AnthropicError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.services.base import BaseLLMService, LLMResponse, Message

logger = logging.getLogger(__name__)


class AnthropicLLMService(BaseLLMService):
    """Anthropic Claude LLM service implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize Anthropic LLM service.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Model name (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Maximum tokens (defaults to settings)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.temperature = temperature if temperature is not None else settings.ANTHROPIC_TEMPERATURE
        self.max_tokens = max_tokens or settings.ANTHROPIC_MAX_TOKENS

        # Initialize async client
        self.client = AsyncAnthropic(api_key=self.api_key)

        logger.info(f"Initialized Anthropic LLM service with model: {self.model}")

    @retry(
        retry=retry_if_exception_type(AnthropicError),
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
        Generate response using Anthropic Claude.

        Args:
            messages: Conversation messages
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            AnthropicError: If API call fails
        """
        try:
            # Separate system message from conversation
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Make API call
            logger.debug(f"Calling Anthropic API with model: {self.model}")
            response = await self.client.messages.create(
                model=self.model,
                messages=conversation_messages,
                system=system_message,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )

            # Extract response
            content = response.content[0].text if response.content else ""
            stop_reason = response.stop_reason

            # Calculate tokens (Anthropic doesn't return token count directly)
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            logger.info(
                f"Generated response with {tokens_used} tokens "
                f"(stop_reason: {stop_reason})"
            )

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
                finish_reason=stop_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            )

        except AnthropicError as e:
            logger.error(f"Anthropic API error: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in Anthropic LLM service: {e}")
            raise

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model

    async def validate_connection(self) -> bool:
        """
        Validate connection to Anthropic API.

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
            logger.info("Anthropic connection validated successfully")
            return True

        except Exception as e:
            logger.error(f"Anthropic connection validation failed: {e}")
            return False

    async def close(self):
        """Close the client connection."""
        await self.client.close()
        logger.info("Anthropic LLM service closed")
