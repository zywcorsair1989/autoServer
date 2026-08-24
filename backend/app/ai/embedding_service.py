"""嵌入服务 - 百炼 API 集成"""

import logging
from typing import List
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """使用百炼 API (OpenAI兼容) 的嵌入服务"""

    def __init__(self):
        """使用百炼 API 配置初始化嵌入服务"""
        self.client = AsyncOpenAI(
            api_key=settings.BAILIAN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = settings.BAILIAN_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        logger.info(f"嵌入服务使用模型 {self.model} 初始化")

    async def embed_text(self, text: str) -> List[float]:
        """
        将单个文本嵌入到向量中

        Args:
            text: 要嵌入的文本

        Returns:
            代表嵌入向量的浮点数列表

        Raises:
            Exception: 如果 API 调用失败
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )

            embedding = response.data[0].embedding
            logger.debug(f"生成了 {len(embedding)} 维的嵌入")
            return embedding

        except Exception as e:
            logger.error(f"文本嵌入生成失败: {str(e)}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文本嵌入到向量中

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵛入向量列表

        Raises:
            Exception: 如果 API 调用失败
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
            )

            # 按索引排序以确保正确的顺序
            embeddings = [None] * len(texts)
            for item in response.data:
                embeddings[item.index] = item.embedding

            logger.debug(
                f"生成了 {len(embeddings)} 个嵌入，每个 {len(embeddings[0])} 维"
            )
            return embeddings

        except Exception as e:
            logger.error(f"批处理嵌入生成失败: {str(e)}")
            raise