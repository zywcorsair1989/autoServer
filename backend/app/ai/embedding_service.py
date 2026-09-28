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

    def _warn_if_dimension_mismatch(self, embedding: List[float]) -> None:
        """向量维度与 EMBEDDING_DIMENSION 不符时给出明确提示。

        不符时 pgvector 只会在很深的调用栈里报 "expected N dimensions"，
        这里先把可操作的线索打到日志里。
        """
        actual = len(embedding)
        if actual != self.dimension:
            logger.warning(
                f"嵌入维度不匹配：模型 {self.model} 返回 {actual} 维，"
                f"而 EMBEDDING_DIMENSION={self.dimension}。"
                f"请修正 backend/.env 中的 EMBEDDING_DIMENSION，"
                f"并执行 migrations/003_embedding_to_pgvector.sql 重建向量列。"
            )

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
            self._warn_if_dimension_mismatch(embedding)
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
            嵌入向量列表

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

            if embeddings and embeddings[0]:
                self._warn_if_dimension_mismatch(embeddings[0])
            logger.debug(
                f"生成了 {len(embeddings)} 个嵌入，每个 {len(embeddings[0])} 维"
            )
            return embeddings

        except Exception as e:
            logger.error(f"批处理嵌入生成失败: {str(e)}")
            raise