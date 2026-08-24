"""Tests for RAG Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.rag_service import RAGService
from app.schemas.knowledge import SourceDocument


class TestRAGService:
    """Tests for RAG Service."""

    @pytest.mark.asyncio
    async def test_query_no_documents_found(self):
        """Test RAG query when no documents are found."""
        mock_db = AsyncMock()
        mock_llm = AsyncMock()
        mock_embedding = AsyncMock()
        mock_llm.generate = AsyncMock(return_value="I don't have information about that.")

        service = RAGService(
            db=mock_db,
            llm_service=mock_llm,
            embedding_service=mock_embedding
        )

        with patch.object(
            service.knowledge_service,
            'search_knowledge',
            return_value=[]
        ):
            response, sources = await service.query(
                query="test query",
                collection_id=uuid4(),
                user_id=uuid4()
            )

            assert sources is None
            assert response == "I don't have information about that."

    @pytest.mark.asyncio
    async def test_query_with_documents(self):
        """Test RAG query with found documents."""
        mock_db = AsyncMock()
        mock_llm = AsyncMock()
        mock_embedding = AsyncMock()

        collection_id = uuid4()
        document_id = uuid4()

        mock_sources = [
            SourceDocument(
                document_id=document_id,
                filename="test.pdf",
                content="Test content for RAG",
                score=0.95
            )
        ]

        mock_llm.generate = AsyncMock(return_value="Based on the document, here is the answer.")

        service = RAGService(
            db=mock_db,
            llm_service=mock_llm,
            embedding_service=mock_embedding
        )

        with patch.object(
            service.knowledge_service,
            'search_knowledge',
            return_value=mock_sources
        ):
            response, sources = await service.query(
                query="test query",
                collection_id=collection_id,
                user_id=uuid4()
            )

            assert len(sources) == 1
            assert sources[0].filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_build_context(self):
        """Test context building from sources."""
        mock_db = AsyncMock()
        service = RAGService(mock_db)

        sources = [
            SourceDocument(
                document_id=uuid4(),
                filename="doc1.pdf",
                content="Content from document 1",
                score=0.9
            ),
            SourceDocument(
                document_id=uuid4(),
                filename="doc2.pdf",
                content="Content from document 2",
                score=0.8
            )
        ]

        context = service._build_context(sources)

        assert "[Document 1]" in context
        assert "doc1.pdf" in context
        assert "[Document 2]" in context
        assert "doc2.pdf" in context

    @pytest.mark.asyncio
    async def test_build_system_prompt(self):
        """Test system prompt building."""
        mock_db = AsyncMock()
        service = RAGService(mock_db)

        context = "Test context content"
        prompt = service._build_system_prompt(context)

        assert "helpful AI assistant" in prompt
        assert context in prompt
        assert "cite" in prompt.lower()

    @pytest.mark.asyncio
    async def test_query_with_history(self):
        """Test RAG query with conversation history."""
        mock_db = AsyncMock()
        mock_llm = AsyncMock()
        mock_embedding = AsyncMock()

        mock_llm.generate = AsyncMock(return_value="Response with history")

        service = RAGService(
            db=mock_db,
            llm_service=mock_llm,
            embedding_service=mock_embedding
        )

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]

        with patch.object(
            service.knowledge_service,
            'search_knowledge',
            return_value=[]
        ):
            response, sources = await service.query_with_history(
                query="Follow-up question",
                collection_id=uuid4(),
                user_id=uuid4(),
                conversation_history=history
            )

            assert response == "Response with history"

    @pytest.mark.asyncio
    async def test_stream_query(self):
        """Test streaming RAG query."""
        mock_db = AsyncMock()
        mock_llm = AsyncMock()
        mock_embedding = AsyncMock()

        # Mock streaming generator
        async def mock_stream(*args, **kwargs):
            for chunk in ["Hello", " ", "world", "!"]:
                yield chunk

        mock_llm.stream_generate = mock_stream

        service = RAGService(
            db=mock_db,
            llm_service=mock_llm,
            embedding_service=mock_embedding
        )

        with patch.object(
            service.knowledge_service,
            'search_knowledge',
            return_value=[]
        ):
            chunks = []
            async for chunk in service.stream_query(
                query="test query",
                collection_id=uuid4(),
                user_id=uuid4()
            ):
                chunks.append(chunk)

            assert chunks == ["Hello", " ", "world", "!"]


class TestRAGServiceInitialization:
    """Tests for RAG Service initialization."""

    def test_init_with_services(self):
        """Test initialization with provided services."""
        mock_db = AsyncMock()
        mock_llm = MagicMock()
        mock_embedding = MagicMock()

        service = RAGService(
            db=mock_db,
            llm_service=mock_llm,
            embedding_service=mock_embedding
        )

        assert service.llm_service == mock_llm
        assert service.embedding_service == mock_embedding

    def test_init_creates_default_services(self):
        """Test initialization creates default services."""
        mock_db = AsyncMock()

        service = RAGService(mock_db)

        assert service.llm_service is not None
        assert service.embedding_service is not None