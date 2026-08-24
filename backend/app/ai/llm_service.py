"""LLM Service - Bailian API Integration"""

import logging
from typing import List, Union, AsyncIterator, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM Service using Bailian API (OpenAI-compatible)"""

    def __init__(self):
        """Initialize LLM Service with Bailian API configuration"""
        self.client = AsyncOpenAI(
            api_key=settings.BAILIAN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = settings.BAILIAN_LLM_MODEL
        logger.info(f"LLM Service initialized with model: {self.model}")

    async def generate(
        self, messages: List[dict], stream: bool = False, temperature: float = 0.7
    ) -> Union[str, AsyncIterator[str]]:
        """
        Generate response from LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 2.0)

        Returns:
            Generated text string or AsyncIterator for streaming

        Raises:
            Exception: If API call fails
        """
        try:
            formatted_messages: List[ChatCompletionMessageParam] = [
                {"role": msg["role"], "content": msg["content"]} for msg in messages
            ]

            if stream:
                return self._stream_generate(formatted_messages, temperature)
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=temperature,
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Received empty response from LLM")
                logger.debug(f"Generated response: {content[:100]}...")
                return content

        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise

    async def _stream_generate(
        self, messages: List[ChatCompletionMessageParam], temperature: float
    ) -> AsyncIterator[str]:
        """
        Stream generate response from LLM

        Args:
            messages: List of formatted messages
            temperature: Sampling temperature

        Yields:
            Text chunks from the stream
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM streaming failed: {str(e)}")
            raise

    async def stream_generate(
        self, messages: List[dict], temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Public method for streaming generation

        Args:
            messages: List of message dicts
            temperature: Sampling temperature

        Yields:
            Text chunks from the stream
        """
        formatted_messages: List[ChatCompletionMessageParam] = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]
        async for chunk in self._stream_generate(formatted_messages, temperature):
            yield chunk