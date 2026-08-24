"""Rerank Service - Bailian API Integration"""

import logging
from typing import List, Dict
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class RerankService:
    """Rerank Service using Bailian API"""

    def __init__(self):
        """Initialize Rerank Service with Bailian API configuration"""
        self.api_key = settings.BAILIAN_API_KEY
        self.model = settings.BAILIAN_RERANK_MODEL
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/rerank"
        logger.info(f"Rerank Service initialized with model: {self.model}")

    async def rerank(
        self, query: str, documents: List[str], top_n: int = 5
    ) -> List[Dict]:
        """
        Rerank documents based on relevance to query

        Args:
            query: Search query
            documents: List of documents to rerank
            top_n: Number of top results to return

        Returns:
            List of dicts with 'index', 'document', and 'relevance_score'

        Raises:
            Exception: If API call fails
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

                # Parse and format results
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
                    f"Reranked {len(documents)} documents, returning top {len(reranked_results)}"
                )
                return reranked_results

        except httpx.HTTPStatusError as e:
            logger.error(f"Rerank API HTTP error: {e.response.status_code}")
            raise Exception(f"Rerank API failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Rerank failed: {str(e)}")
            raise

    async def rerank_with_scores(
        self, query: str, documents: List[str], top_n: int = 5
    ) -> List[tuple]:
        """
        Rerank documents and return as tuples of (index, score, document)

        Args:
            query: Search query
            documents: List of documents to rerank
            top_n: Number of top results to return

        Returns:
            List of tuples (index, relevance_score, document)
        """
        results = await self.rerank(query, documents, top_n)
        return [
            (item["index"], item["relevance_score"], item["document"])
            for item in results
        ]