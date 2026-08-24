"""重排服务 - 百炼 API 集成"""

import logging
from typing import List, Dict
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class RerankService:
    """使用百炼 API 的重排服务"""

    def __init__(self):
        """使用百炼 API 配置初始化重排服务"""
        self.api_key = settings.BAILIAN_API_KEY
        self.model = settings.BAILIAN_RERANK_MODEL
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/rerank"
        logger.info(f"重排服务使用模型 {self.model} 初始化")

    async def rerank(
        self, query: str, documents: List[str], top_n: int = 5
    ) -> List[Dict]:
        """
        根据与查询的相关性重排文档

        Args:
            query: 搜索查询
            documents: 要重排的文档列表
            top_n: 要返回的顶部结果数量

        Returns:
            带 'index', 'document', 和 'relevance_score' 的字典列表

        Raises:
            Exception: 如果 API 调用失败
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": {
                            "query": query,
                            "documents": documents,
                        },
                        "parameters": {
                            "top_n": min(top_n, len(documents)),
                        },
                    },
                )

                response.raise_for_status()
                result = response.json()

                # 解析和格式化结果
                reranked_results = []
                for item in result["output"]["results"]:
                    reranked_results.append(
                        {
                            "index": item["index"],
                            "document": documents[item["index"]],
                            "relevance_score": item["relevance_score"],
                        }
                    )

                logger.debug(
                    f"重排了 {len(documents)} 个文档，返回顶部 {len(reranked_results)} 个"
                )
                return reranked_results

        except httpx.HTTPStatusError as e:
            logger.error(f"重排 API HTTP 错误: {e.response.status_code}")
            raise Exception(f"重排 API 失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"重排失败: {str(e)}")
            raise

    async def rerank_with_scores(
        self, query: str, documents: List[str], top_n: int = 5
    ) -> List[tuple]:
        """
        重排文档并返回 (索引, 得分, 文档) 元组

        Args:
            query: 搜索查询
            documents: 要重排的文档列表
            top_n: 要返回的顶部结果数量

        Returns:
            (索引, 相关得分, 文档) 元组列表
        """
        results = await self.rerank(query, documents, top_n)
        return [
            (item["index"], item["relevance_score"], item["document"])
            for item in results
        ]