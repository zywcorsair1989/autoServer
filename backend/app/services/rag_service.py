"""RAG Service for complete RAG pipeline.

This module provides the main RAG pipeline that combines:
- Embedding generation
- Vector search
- Optional reranking
- LLM response generation
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
    """RAG Service for end-to-end retrieval-augmented generation."""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        rerank_service: Optional[RerankService] = None
    ):
        """Initialize RAG Service.

        Args:
            db: AsyncSession for database operations.
            llm_service: LLM service for response generation.
            embedding_service: Embedding service for vector operations.
            rerank_service: Optional rerank service for result reranking.
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
        """Execute a RAG query.

        Args:
            query: The user's question.
            collection_id: UUID of the knowledge collection to search.
            user_id: UUID of the user making the query.
            top_k: Number of documents to retrieve.
            rerank: Whether to rerank results.
            temperature: LLM temperature for generation.

        Returns:
            Tuple of (response text, list of source documents).

        Raises:
            ValueError: If collection not found or other error.
        """
        logger.info(f"RAG query from user {user_id}: {query[:50]}...")

        # Step 1: Retrieve relevant documents
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
            # No relevant documents found
            logger.warning(f"No documents found for query in collection {collection_id}")
            response = await self.llm_service.generate(
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": query}
                ],
                temperature=temperature
            )
            return response, None

        # Step 2: Optional reranking
        if rerank and self.rerank_service:
            documents = [source.content for source in sources]
            reranked = await self.rerank_service.rerank(query, documents, top_n=top_k)

            # Reorder sources based on reranking
            reranked_sources = []
            for item in reranked:
                idx = item["index"]
                source = sources[idx]
                source.score = item["relevance_score"]
                reranked_sources.append(source)
            sources = reranked_sources

        # Step 3: Build context from retrieved documents
        context = self._build_context(sources)

        # Step 4: Generate response using LLM
        system_prompt = self._build_system_prompt(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        response = await self.llm_service.generate(
            messages=messages,
            temperature=temperature
        )

        logger.info(f"RAG query completed with {len(sources)} sources")
        return response, sources

    def _build_context(self, sources: List[SourceDocument]) -> str:
        """Build context string from source documents.

        Args:
            sources: List of source documents.

        Returns:
            Context string for the LLM.
        """
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[Document {i}] {source.filename}\n"
                f"{source.content}\n"
            )

        return "\n".join(context_parts)

    def _build_system_prompt(self, context: str) -> str:
        """Build system prompt with context.

        Args:
            context: Context string from retrieved documents.

        Returns:
            System prompt for the LLM.
        """
        return (
            "You are a helpful AI assistant. Use the following context to "
            "answer the user's question. If the answer is not in the context, "
            "say so honestly. Always cite which document(s) you used.\n\n"
            f"Context:\n{context}"
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
        """Execute a RAG query with conversation history.

        Args:
            query: The user's question.
            collection_id: UUID of the knowledge collection.
            user_id: UUID of the user.
            conversation_history: List of previous messages.
            top_k: Number of documents to retrieve.
            rerank: Whether to rerank results.
            temperature: LLM temperature.

        Returns:
            Tuple of (response text, list of source documents).
        """
        # Retrieve documents
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

        # Build context
        context = self._build_context(sources) if sources else ""
        system_prompt = self._build_system_prompt(context) if context else (
            "You are a helpful AI assistant."
        )

        # Build messages with history
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": query})

        # Generate response
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
        """Execute a RAG query with streaming response.

        Args:
            query: The user's question.
            collection_id: UUID of the knowledge collection.
            user_id: UUID of the user.
            top_k: Number of documents to retrieve.
            rerank: Whether to rerank results.
            temperature: LLM temperature.

        Yields:
            Text chunks from the response.
        """
        # Retrieve documents
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

        # Build context and system prompt
        context = self._build_context(sources) if sources else ""
        system_prompt = self._build_system_prompt(context) if context else (
            "You are a helpful AI assistant."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # Stream response
        async for chunk in self.llm_service.stream_generate(messages, temperature):
            yield chunk