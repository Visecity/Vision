"""
LLM client wrapper for Vision pixel art generation system.

This module provides a wrapper around the Anthropic API with additional
features like error handling, caching, rate limiting, and streaming support.
"""

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any, Literal

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message, MessageStreamEvent
from redis import Redis
from redis.exceptions import RedisError

from src.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class TokenCounter:
    """Utility for counting and tracking token usage."""

    def __init__(self) -> None:
        """Initialize token counter."""
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """
        Add token usage to counter.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_total_tokens(self) -> int:
        """Get total token count (input + output)."""
        return self.total_input_tokens + self.total_output_tokens

    def reset(self) -> None:
        """Reset token counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def __repr__(self) -> str:
        """String representation of token counter."""
        return (
            f"TokenCounter(input={self.total_input_tokens}, "
            f"output={self.total_output_tokens}, "
            f"total={self.get_total_tokens()})"
        )


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, time_window: float = 60.0) -> None:
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self._calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a call can be made within rate limits."""
        async with self._lock:
            now = time.time()
            # Remove calls outside the time window
            self._calls = [call_time for call_time in self._calls if now - call_time < self.time_window]

            if len(self._calls) >= self.max_calls:
                # Wait until oldest call expires
                sleep_time = self.time_window - (now - self._calls[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, waiting {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    # Recursive call to try again
                    await self.acquire()
            else:
                self._calls.append(now)


class CacheManager:
    """Manages caching of LLM responses using Redis."""

    def __init__(self, redis_client: Redis | None, ttl: int = 3600) -> None:
        """
        Initialize cache manager.

        Args:
            redis_client: Redis client instance (None to disable caching)
            ttl: Cache time-to-live in seconds
        """
        self.redis = redis_client
        self.ttl = ttl
        self._enabled = redis_client is not None

    def _make_key(self, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """
        Create cache key from request parameters.

        Args:
            model: Model name
            messages: Message list
            **kwargs: Additional parameters

        Returns:
            str: Cache key
        """
        # Create deterministic key from request parameters
        cache_dict = {
            "model": model,
            "messages": messages,
            **{k: v for k, v in sorted(kwargs.items())},
        }
        cache_str = json.dumps(cache_dict, sort_keys=True)
        # Use hash for shorter keys
        import hashlib

        key_hash = hashlib.sha256(cache_str.encode()).hexdigest()
        return f"llm_cache:{key_hash}"

    async def get(self, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any] | None:
        """
        Get cached response if available.

        Args:
            model: Model name
            messages: Message list
            **kwargs: Additional parameters

        Returns:
            dict | None: Cached response or None if not found
        """
        if not self._enabled:
            return None

        try:
            key = self._make_key(model, messages, **kwargs)
            cached = self.redis.get(key)  # type: ignore
            if cached:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set(
        self,
        model: str,
        messages: list[dict[str, Any]],
        response: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """
        Cache a response.

        Args:
            model: Model name
            messages: Message list
            response: Response to cache
            **kwargs: Additional parameters
        """
        if not self._enabled:
            return

        try:
            key = self._make_key(model, messages, **kwargs)
            self.redis.setex(key, self.ttl, json.dumps(response))  # type: ignore
            logger.debug(f"Cached response with key: {key}")
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache set error: {e}")


class LLMClient:
    """
    Wrapper for Anthropic API with enhanced features.

    Provides error handling, retries, caching, rate limiting, and token tracking.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        redis_client: Redis | None = None,
    ) -> None:
        """
        Initialize LLM client.

        Args:
            settings: Application settings (uses get_settings() if None)
            redis_client: Redis client for caching (optional)
        """
        self.settings = settings or get_settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)
        self.async_client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)

        # Initialize components
        self.token_counter = TokenCounter()
        self.rate_limiter = RateLimiter(max_calls=50, time_window=60.0)
        self.cache_manager = CacheManager(
            redis_client=redis_client if self.settings.performance.enable_caching else None,
            ttl=self.settings.performance.cache_ttl,
        )

    async def create_message(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Message | AsyncIterator[MessageStreamEvent]:
        """
        Create a message using Claude API with retries and caching.

        Args:
            model: Model name (e.g., 'claude-3-5-sonnet-20241022')
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: Optional system prompt
            stream: Whether to stream the response
            **kwargs: Additional API parameters

        Returns:
            Message | AsyncIterator: API response or stream iterator

        Raises:
            Exception: If all retries fail
        """
        # Check cache (only for non-streaming)
        if not stream:
            cached = await self.cache_manager.get(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                **kwargs,
            )
            if cached:
                return Message(**cached)

        # Apply rate limiting
        await self.rate_limiter.acquire()

        # Retry logic
        max_retries = self.settings.performance.max_retries
        timeout = self.settings.performance.timeout

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"API call attempt {attempt + 1}/{max_retries + 1}")

                if stream:
                    return await self._create_stream(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system,
                        **kwargs,
                    )
                else:
                    response = await asyncio.wait_for(
                        self.async_client.messages.create(
                            model=model,
                            messages=messages,  # type: ignore
                            max_tokens=max_tokens,
                            temperature=temperature,
                            system=system,
                            **kwargs,
                        ),
                        timeout=timeout,
                    )

                    # Track token usage
                    self.token_counter.add_usage(
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                    )

                    # Cache the response
                    await self.cache_manager.set(
                        model=model,
                        messages=messages,
                        response=response.model_dump(),
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system,
                        **kwargs,
                    )

                    return response

            except asyncio.TimeoutError:
                logger.warning(f"API call timeout (attempt {attempt + 1})")
                if attempt == max_retries:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"API call error (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

        raise Exception("All retry attempts failed")

    async def _create_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[MessageStreamEvent]:
        """
        Create a streaming message response.

        Args:
            model: Model name
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: Optional system prompt
            **kwargs: Additional API parameters

        Yields:
            MessageStreamEvent: Stream events from the API
        """
        async with self.async_client.messages.stream(
            model=model,
            messages=messages,  # type: ignore
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            **kwargs,
        ) as stream:
            async for event in stream:
                yield event

            # Track token usage from final message
            if hasattr(stream, "get_final_message"):
                final_message = await stream.get_final_message()
                self.token_counter.add_usage(
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens,
                )

    def get_token_usage(self) -> dict[str, int]:
        """
        Get current token usage statistics.

        Returns:
            dict: Token usage with 'input', 'output', and 'total' keys
        """
        return {
            "input": self.token_counter.total_input_tokens,
            "output": self.token_counter.total_output_tokens,
            "total": self.token_counter.get_total_tokens(),
        }

    def reset_token_counter(self) -> None:
        """Reset token usage counter."""
        self.token_counter.reset()


def create_llm_client(
    settings: Settings | None = None,
    redis_client: Redis | None = None,
) -> LLMClient:
    """
    Factory function to create an LLM client.

    Args:
        settings: Application settings (uses get_settings() if None)
        redis_client: Redis client for caching (optional)

    Returns:
        LLMClient: Configured LLM client instance

    Example:
        >>> client = create_llm_client()
        >>> response = await client.create_message(
        ...     model="claude-3-5-sonnet-20241022",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    return LLMClient(settings=settings, redis_client=redis_client)


# TODO: Phase 3 - Add support for prompt templates and chaining
# TODO: Phase 3 - Add structured output parsing (JSON mode)
# TODO: Phase 3 - Add support for tool/function calling
# TODO: Phase 4 - Add request batching for efficiency
# TODO: Phase 4 - Add more sophisticated retry strategies (exponential backoff, jitter)
# TODO: Phase 4 - Add metrics and monitoring hooks