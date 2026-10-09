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
        temperature: float = 0.7,
        score_ratio_threshold: float = 0.5
    ) -> Tuple[str, Optional[List[SourceDocument]]]:
        """执行 RAG 查询。

        Args:
            query: 用户的问题。
            collection_id: 要搜索的知识库集合的 UUID。
            user_id: 进行查询的用户的 UUID。
            top_k: 要检索的文档数量上限。
            rerank: 是否重排结果。
            temperature: 生成的 LLM 温度。
            score_ratio_threshold: 自适应阈值：rerank 后仅保留
                分数 ≥ 最高分 × 此比例的来源（只在开启 rerank 时生效）。
                相关内容多时返回满 top_k 条，少时自动只返回 1~2 条，
                避免无关内容被硬塞进上下文。rerank 分数是请求内相对分，
                故用相对比例而非绝对阈值。

        Returns:
            (回復文本, 源文档列表) 的元组。

        Raises:
            ValueError: 如果集合未找到或其他错误。
        """
        logger.info(f"来自用户 {user_id} 的 RAG 查询: {query[:50]}...")

        # 步骤 1: 检索相关文档
        # 当启用 rerank 时，检索更多候选以避免遗漏相关内容
        retrieval_k = top_k * 3 if rerank else top_k
        knowledge_query = KnowledgeQuery(
            query=query,
            collection_id=collection_id,
            top_k=retrieval_k,
            rerank=rerank
        )

        sources = await self.knowledge_service.search_knowledge(
            knowledge_query,
            user_id
        )

        if not sources:
            # 检索无结果：兜底让 LLM 基于通用知识回答（联网搜索已关闭，不会去网上查）
            # 系统提示词强调"不要编造"，避免模型编造不存在的功能/操作
            logger.warning(f"在集合 {collection_id} 中未找到查询的文档，启用兜底")
            response = await self.llm_service.generate(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个专业的AI助手。请基于通用知识回答用户问题。"
                            "如果问题涉及具体系统的功能或操作步骤而你不确定，"
                            "请明确告知用户'该问题需要查阅产品文档确认'，"
                            "不要编造操作步骤或文档中可能不存在的功能。"
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                temperature=temperature,
            )
            return response, None

        # 步骤 2: 可选重排
        if rerank and self.rerank_service:
            documents = [source.content for source in sources]
            # 多要一倍候选（top_k*2），为自适应阈值过滤留出淘汰空间
            reranked = await self.rerank_service.rerank(
                query, documents, top_n=min(top_k * 2, len(documents))
            )

            # 根据重排结果重新排序源
            reranked_sources = []
            for item in reranked:
                idx = item["index"]
                source = sources[idx]
                source.score = item["relevance_score"]
                reranked_sources.append(source)

            # 自适应阈值：只保留分数 ≥ 最高分 × score_ratio_threshold 的来源。
            # 最高分自身必然保留；无相关内容时（最高分也极低）则至少保留第 1 条，
            # 走“上下文没有答案”的回答路径而不是空上下文。
            if reranked_sources:
                best_score = reranked_sources[0].score
                threshold = best_score * score_ratio_threshold
                kept = [
                    s for s in reranked_sources[:top_k]
                    if s.score >= threshold
                ]
                dropped = len(reranked_sources[:top_k]) - len(kept)
                if dropped:
                    logger.info(
                        f"自适应阈值过滤：rerank 候选 {len(reranked_sources)} 条，"
                        f"阈值 {threshold:.3f}，淘汰 {dropped} 条低相关来源"
                    )
                sources = kept

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
            "4. 保持专业严谨的回答风格\n"
            "5. 上下文中形如 [图片: 文件名] 的标记表示该位置有配图（会展示给用户），"
            "涉及操作步骤或界面功能时可提示用户展开引用来源查看配图\n\n"
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
        # 检索文档 - 启用 rerank 时检索更多候选
        retrieval_k = top_k * 3 if rerank else top_k
        knowledge_query = KnowledgeQuery(
            query=query,
            collection_id=collection_id,
            top_k=retrieval_k,
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
        # 检索文档 - 启用 rerank 时检索更多候选
        retrieval_k = top_k * 3 if rerank else top_k
        knowledge_query = KnowledgeQuery(
            query=query,
            collection_id=collection_id,
            top_k=retrieval_k,
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