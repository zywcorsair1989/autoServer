"""Tests for the knowledge service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json
import os

from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import (
    KnowledgeCollectionCreate,
    KnowledgeQuery,
    SourceDocument,
)
from app.models.knowledge import KnowledgeCollection
from app.models.document import Document, DocumentChunk


class TestCreateCollection:
    """Tests for creating knowledge collections."""

    @pytest.mark.asyncio
    async def test_create_collection_success(self):
        """Test successful collection creation."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        user_id = uuid4()
        collection_data = KnowledgeCollectionCreate(
            name="Test Collection",
            description="Test description"
        )

        service = KnowledgeService(mock_db)
        collection = await service.create_collection(user_id, collection_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        assert collection.user_id == user_id
        assert collection.name == "Test Collection"
        assert collection.description == "Test description"

    @pytest.mark.asyncio
    async def test_create_collection_minimal(self):
        """Test collection creation with minimal data."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        user_id = uuid4()
        collection_data = KnowledgeCollectionCreate(name="Minimal Collection")

        service = KnowledgeService(mock_db)
        collection = await service.create_collection(user_id, collection_data)

        assert collection.name == "Minimal Collection"
        assert collection.description is None


class TestGetCollection:
    """Tests for getting knowledge collections."""

    @pytest.mark.asyncio
    async def test_get_collection_found(self):
        """Test getting an existing collection."""
        mock_db = AsyncMock()
        collection_id = uuid4()
        user_id = uuid4()

        mock_collection = MagicMock(spec=KnowledgeCollection)
        mock_collection.id = collection_id
        mock_collection.user_id = user_id
        mock_collection.name = "Test Collection"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_collection
        mock_db.execute.return_value = mock_result

        service = KnowledgeService(mock_db)
        result = await service.get_collection(collection_id, user_id)

        assert result == mock_collection

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self):
        """Test getting a non-existent collection."""
        mock_db = AsyncMock()
        collection_id = uuid4()
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = KnowledgeService(mock_db)
        result = await service.get_collection(collection_id, user_id)

        assert result is None


class TestListCollections:
    """Tests for listing knowledge collections."""

    @pytest.mark.asyncio
    async def test_list_collections_success(self):
        """Test successful collection listing."""
        mock_db = AsyncMock()
        user_id = uuid4()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3

        mock_collections = [
            MagicMock(spec=KnowledgeCollection),
            MagicMock(spec=KnowledgeCollection)
        ]
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_collections

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        service = KnowledgeService(mock_db)
        collections, total = await service.list_collections(user_id, skip=0, limit=10)

        assert total == 3
        assert len(collections) == 2

    @pytest.mark.asyncio
    async def test_list_collections_empty(self):
        """Test listing collections when user has none."""
        mock_db = AsyncMock()
        user_id = uuid4()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        service = KnowledgeService(mock_db)
        collections, total = await service.list_collections(user_id)

        assert total == 0
        assert len(collections) == 0


class TestDeleteCollection:
    """Tests for deleting knowledge collections."""

    @pytest.mark.asyncio
    async def test_delete_collection_success(self):
        """Test successful collection deletion."""
        mock_db = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        collection_id = uuid4()
        user_id = uuid4()

        mock_collection = MagicMock(spec=KnowledgeCollection)
        mock_collection.id = collection_id

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=mock_collection
        ):
            service = KnowledgeService(mock_db)
            result = await service.delete_collection(collection_id, user_id)

            assert result is True
            mock_db.delete.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_collection_not_found(self):
        """Test deleting a non-existent collection."""
        mock_db = AsyncMock()
        collection_id = uuid4()
        user_id = uuid4()

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=None
        ):
            service = KnowledgeService(mock_db)
            result = await service.delete_collection(collection_id, user_id)

            assert result is False
            mock_db.delete.assert_not_called()


class TestAddDocument:
    """Tests for adding documents."""

    @pytest.mark.asyncio
    async def test_add_document_success(self):
        """Test successful document addition."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        collection_id = uuid4()
        user_id = uuid4()

        mock_collection = MagicMock(spec=KnowledgeCollection)
        mock_collection.id = collection_id

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=mock_collection
        ):
            service = KnowledgeService(mock_db)
            document = await service.add_document(
                collection_id,
                user_id,
                "test.pdf",
                "/path/to/test.pdf",
                1024
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            assert document.collection_id == collection_id
            assert document.filename == "test.pdf"
            assert document.status == "pending"

    @pytest.mark.asyncio
    async def test_add_document_collection_not_found(self):
        """Test adding document to non-existent collection."""
        mock_db = AsyncMock()
        collection_id = uuid4()
        user_id = uuid4()

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=None
        ):
            service = KnowledgeService(mock_db)

            with pytest.raises(ValueError) as exc_info:
                await service.add_document(
                    collection_id,
                    user_id,
                    "test.pdf",
                    "/path/to/test.pdf",
                    1024
                )

            assert "not found" in str(exc_info.value)


class TestGetDocument:
    """Tests for getting documents."""

    @pytest.mark.asyncio
    async def test_get_document_found(self):
        """Test getting an existing document."""
        mock_db = AsyncMock()
        document_id = uuid4()
        user_id = uuid4()

        mock_document = MagicMock(spec=Document)
        mock_document.id = document_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        mock_db.execute.return_value = mock_result

        service = KnowledgeService(mock_db)
        result = await service.get_document(document_id, user_id)

        assert result == mock_document

    @pytest.mark.asyncio
    async def test_get_document_not_found(self):
        """Test getting a non-existent document."""
        mock_db = AsyncMock()
        document_id = uuid4()
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = KnowledgeService(mock_db)
        result = await service.get_document(document_id, user_id)

        assert result is None


class TestListDocuments:
    """Tests for listing documents."""

    @pytest.mark.asyncio
    async def test_list_documents_success(self):
        """Test successful document listing."""
        mock_db = AsyncMock()
        collection_id = uuid4()
        user_id = uuid4()

        mock_collection = MagicMock(spec=KnowledgeCollection)
        mock_collection.id = collection_id

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        mock_documents = [
            MagicMock(spec=Document),
            MagicMock(spec=Document)
        ]
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_documents

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=mock_collection
        ):
            mock_db.execute.side_effect = [mock_count_result, mock_list_result]

            service = KnowledgeService(mock_db)
            documents, total = await service.list_documents(
                collection_id, user_id, skip=0, limit=10
            )

            assert total == 5
            assert len(documents) == 2

    @pytest.mark.asyncio
    async def test_list_documents_collection_not_found(self):
        """Test listing documents when collection not found."""
        mock_db = AsyncMock()
        collection_id = uuid4()
        user_id = uuid4()

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=None
        ):
            service = KnowledgeService(mock_db)
            documents, total = await service.list_documents(collection_id, user_id)

            assert total == 0
            assert len(documents) == 0


class TestDeleteDocument:
    """Tests for deleting documents."""

    @pytest.mark.asyncio
    async def test_delete_document_success(self):
        """Test successful document deletion."""
        mock_db = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        document_id = uuid4()
        user_id = uuid4()

        mock_document = MagicMock(spec=Document)
        mock_document.id = document_id
        mock_document.file_path = "/path/to/nonexistent.pdf"

        with patch.object(
            KnowledgeService,
            'get_document',
            return_value=mock_document
        ):
            service = KnowledgeService(mock_db)
            result = await service.delete_document(document_id, user_id)

            assert result is True
            mock_db.delete.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self):
        """Test deleting a non-existent document."""
        mock_db = AsyncMock()
        document_id = uuid4()
        user_id = uuid4()

        with patch.object(
            KnowledgeService,
            'get_document',
            return_value=None
        ):
            service = KnowledgeService(mock_db)
            result = await service.delete_document(document_id, user_id)

            assert result is False
            mock_db.delete.assert_not_called()


class TestProcessDocument:
    """Tests for processing documents."""

    @pytest.mark.asyncio
    async def test_process_document_no_embedding_service(self):
        """Test processing document without embedding service."""
        mock_db = AsyncMock()
        document_id = uuid4()
        user_id = uuid4()

        service = KnowledgeService(mock_db, embedding_service=None)

        with pytest.raises(ValueError) as exc_info:
            await service.process_document(document_id, user_id)

        assert "Embedding service not configured" in str(exc_info.value)


class TestSearchKnowledge:
    """Tests for knowledge search."""

    @pytest.mark.asyncio
    async def test_search_knowledge_no_embedding_service(self):
        """Test searching knowledge without embedding service."""
        mock_db = AsyncMock()
        user_id = uuid4()
        query = KnowledgeQuery(
            query="test query",
            collection_id=uuid4()
        )

        service = KnowledgeService(mock_db, embedding_service=None)

        with pytest.raises(ValueError) as exc_info:
            await service.search_knowledge(query, user_id)

        assert "Embedding service not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_knowledge_collection_not_found(self):
        """Test searching in non-existent collection."""
        mock_db = AsyncMock()
        mock_embedding = AsyncMock()
        user_id = uuid4()
        query = KnowledgeQuery(
            query="test query",
            collection_id=uuid4()
        )

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=None
        ):
            service = KnowledgeService(mock_db, embedding_service=mock_embedding)

            with pytest.raises(ValueError) as exc_info:
                await service.search_knowledge(query, user_id)

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_knowledge_empty_collection(self):
        """Test searching in empty collection."""
        mock_db = AsyncMock()
        mock_embedding = AsyncMock()
        user_id = uuid4()
        collection_id = uuid4()
        query = KnowledgeQuery(
            query="test query",
            collection_id=collection_id
        )

        mock_collection = MagicMock(spec=KnowledgeCollection)
        mock_collection.id = collection_id

        # Mock empty chunks query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        with patch.object(
            KnowledgeService,
            'get_collection',
            return_value=mock_collection
        ):
            mock_embedding.embed_text = AsyncMock(return_value=[0.1] * 1536)
            mock_db.execute.return_value = mock_result

            service = KnowledgeService(mock_db, embedding_service=mock_embedding)
            results = await service.search_knowledge(query, user_id)

            assert results == []


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_cosine_similarity_identical_vectors(self):
        """Test similarity of identical vectors."""
        mock_db = AsyncMock()
        service = KnowledgeService(mock_db)

        vec = [1.0, 2.0, 3.0]
        similarity = service._cosine_similarity(vec, vec)

        assert similarity == pytest.approx(1.0, rel=1e-5)

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors."""
        mock_db = AsyncMock()
        service = KnowledgeService(mock_db)

        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = service._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(0.0, abs=1e-5)

    def test_cosine_similarity_different_lengths(self):
        """Test similarity of vectors with different lengths."""
        mock_db = AsyncMock()
        service = KnowledgeService(mock_db)

        vec1 = [1.0, 2.0]
        vec2 = [1.0, 2.0, 3.0]
        similarity = service._cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_cosine_similarity_zero_vector(self):
        """Test similarity with zero vector."""
        mock_db = AsyncMock()
        service = KnowledgeService(mock_db)

        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        similarity = service._cosine_similarity(vec1, vec2)

        assert similarity == 0.0