"""Embedding Service - Bailian API Integration"""

import logging
from typing import List
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding Service using Bailian API (OpenAI-compatible)"""

    def __init__(self):
        """Initialize Embedding Service with Bailian API configuration"""
        self.client = AsyncOpenAI(
            api_key=settings.BAILIAN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = settings.BAILIAN_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        logger.info(f"Embedding Service initialized with model: {self.model}")

    async def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text into a vector

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            Exception: If API call fails
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed for text: {str(e)}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts into vectors

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If API call fails
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
            )

            # Sort by index to ensure correct order
            embeddings = [None] * len(texts)
            for item in response.data:
                embeddings[item.index] = item.embedding

            logger.debug(
                f"Generated {len(embeddings)} embeddings, each with {len(embeddings[0])} dimensions"
            )
            return embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise