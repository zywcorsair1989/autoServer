"""RAG 服务，提供完整的 RAG 管道。

这个模块提供结合了以下功能的主要 RAG 管道：
- 嵛入向量生成
- 向量搜索
- 可选的重排
- LLM 回复生成
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_service import LLMService
from app.ai.embedding_service import EmbeddingService
from app.ai.rerank_service import RerankService
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import KnowledgeQuery, SourceDocument

logger = logging.getLogger(__name__)


class RAGService:
    """端到端检索増强生成的 RAG 服务。"""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        rerank_service: Optional[RerankService] = None
    ):
        """初始化 RAG 服务。

        Args:
            db: 用于数据库操作的 AsyncSession。
            llm_service: 用于回復生成的 LLM 服务。
            embedding_service: 用于向量操作的嵌入服务。
            rerank_service: 可选的用于结果重排的重排服务。
        """
        self.db = db
        self.llm_service = llm_service or LLMService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.rerank_service = rerank_service
        self.knowledge_service = KnowledgeService(
            db=db,
            embedding_service=self.embedding_service
        )

    async def query(
        self,
        query: str,
        collection_id: UUID,
        user_id: UUID,
        top_k: int = 5,
        rerank: bool = False,
        temperature: float = 0.7
    ) -> Tuple[str, Optional[List[SourceDocument]]]:
        """执行 RAG 查询。

        Args:
            query: 用户的问题。
            collection_id: 要搜索的知识库集合的 UUID。
            user_id: 进行查询的用户的 UUID。
            top_k: 要检索的文档数量。
            rerank: 是否重排结果。
            temperature: 生成的 LLM 温度。

        Returns:
            (回復文本, 源文档列表) 的元组。

        Raises:
            ValueError: 如果集合未找到或其他错误。
        """
        logger.info(f"来自用户 {user_id} 的 RAG 查询: {query[:50]}...")

        # 步骤 1: 检索相关文档
        knowledge_query = KnowledgeQuery(
            query=query,
            collection_id=collection_id,
            top_k=top_k,
            rerank=rerank
        )

        sources = await self.knowledge_service.search_knowledge(
            knowledge_query,
            user_id
        )

        if not sources:
            # 未找到相关文档
            logger.warning(f"在集合 {collection_id} 中未找到查询的文档")
            response = await self.llm_service.generate(
                messages=[
                    {"role": "system", "content": "你是一个专业的AI助手。"},
                    {"role": "user", "content": query}
                ],
                temperature=temperature
            )
            return response, None

        # 步骤 2: 可选重排
        if rerank and self.rerank_service:
            documents = [source.content for source in sources]
            reranked = await self.rerank_service.rerank(query, documents, top_n=top_k)

            # 根据重排结果重新排序源
            reranked_sources = []
            for item in reranked:
                idx = item["index"]
                source = sources[idx]
                source.score = item["relevance_score"]
                reranked_sources.append(source)
            sources = reranked_sources

        # 步骤 3: 从检索的文档建立上下文
        context = self._build_context(sources)

        # 步骤 4: 使用 LLM 生成回復
        system_prompt = self._build_system_prompt(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        response = await self.llm_service.generate(
            messages=messages,
            temperature=temperature
        )

        logger.info(f"RAG 查询完成，包含 {len(sources)} 个源")
        return response, sources

    def _build_context(self, sources: List[SourceDocument]) -> str:
        """从源文档建立上下文字符串。

        Args:
            sources: 源文档列表。

        Returns:
            LLM 的上下文字符串。
        """
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[文档 {i}] {source.filename}\n{source.content}\n"
            )

        return "\n".join(context_parts)

    def _build_system_prompt(self, context: str) -> str:
        """使用上下文建立系统提示。

        Args:
            context: 来检索文档的上下文字符串。

        Returns:
            LLM 的系统提示。
        """
        return (
            "你是一个专业的AI助手。请根据提供的上下文文档回答用户问题。\n\n"
            "要求：\n"
            "1. 必须基于上下文文档中的事实回答，不要编造信息\n"
            "2. 如果上下文中没有答案，请明确告知用户\n"
            "3. 引用时使用 [文档名] 格式标注来源\n"
            "4. 保持专业严谨的回答风格\n\n"
            f"上下文：\n{context}"
        )

    async def query_with_history(
        self,
        query: str,
        collection_id: UUID,
        user_id: UUID,
        conversation_history: List[dict],
        top_k: int = 5,
        rerank: bool = False,
        temperature: float = 0.7
    ) -> Tuple[str, Optional[List[SourceDocument]]]:
        """执行带对话历史的 RAG 查询。

        Args:
            query: 用户的问题。
            collection_id: 知识库集合的 UUID。
            user_id: 用户的 UUID。
            conversation_history: 前一个消息的列表。
            top_k: 要检索的文档数量。
            rerank: 是否重排结果。
            temperature: LLM 温度。

        Returns:
            (回復文本, 源文档列表) 的元组。
        """
        # 检索文档
        knowledge_query = KnowledgeQuery(
            query=query,
            collection_id=collection_id,
            top_k=top_k,
            rerank=rerank
        )

        sources = await self.knowledge_service.search_knowledge(
            knowledge_query,
            user_id
        )

        # 建立上下文
        context = self._build_context(sources) if sources else ""
        system_prompt = self._build_system_prompt(context) if context else (
            "你是一个专业的AI助手。"
        )

        # 使用历史建立消息
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": query})

        # 生成回復
        response = await self.llm_service.generate(
            messages=messages,
            temperature=temperature
        )

        return response, sources

    async def stream_query(
        self,
        query: str,
        collection_id: UUID,
        user_id: UUID,
        top_k: int = 5,
        rerank: bool = False,
        temperature: float = 0.7
    ):
        """执行带流式回復的 RAG 查询。

        Args:
            query: 用户的问题。
            collection_id: 知识库集合的 UUID。
            user_id: 用户的 UUID。
            top_k: 要检索的文档数量。
            rerank: 是否重排结果。
            temperature: LLM 温度。

        Yields:
            来自回復的文本块。
        """
        # 检索文档
        knowledge_query = KnowledgeQuery(
            query=query,
            collection_id=collection_id,
            top_k=top_k,
            rerank=rerank
        )

        sources = await self.knowledge_service.search_knowledge(
            knowledge_query,
            user_id
        )

        # 建立上下文和系统提示
        context = self._build_context(sources) if sources else ""
        system_prompt = self._build_system_prompt(context) if context else (
            "你是一个专业的AI助手。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # 流式回復
        async for chunk in self.llm_service.stream_generate(messages, temperature):
            yield chunk