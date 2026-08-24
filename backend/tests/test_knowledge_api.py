"""Tests for knowledge API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
import io

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.knowledge import KnowledgeCollection
from app.models.document import Document
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import SourceDocument


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "user"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    return user


@pytest.fixture
def mock_collection(mock_user):
    """Create a mock knowledge collection."""
    collection = MagicMock(spec=KnowledgeCollection)
    collection.id = uuid4()
    collection.user_id = mock_user.id
    collection.name = "Test Collection"
    collection.description = "Test description"
    collection.created_at = datetime.utcnow()
    collection.documents = []
    return collection


@pytest.fixture
def mock_document(mock_collection):
    """Create a mock document."""
    doc = MagicMock(spec=Document)
    doc.id = uuid4()
    doc.collection_id = mock_collection.id
    doc.filename = "test.pdf"
    doc.file_path = "/uploads/test.pdf"
    doc.file_size = 1024
    doc.status = "pending"
    doc.created_at = datetime.utcnow()
    return doc


class TestCreateCollectionEndpoint:
    """Tests for the POST /api/v1/knowledge endpoint."""

    @pytest.mark.asyncio
    async def test_create_collection_success(self, mock_db, mock_user, mock_collection):
        """Test successful collection creation."""
        with patch.object(KnowledgeService, "create_collection", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_collection

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/knowledge",
                json={
                    "name": "Test Collection",
                    "description": "Test description"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Collection"

            app.dependency_overrides.clear()


class TestListCollectionsEndpoint:
    """Tests for the GET /api/v1/knowledge endpoint."""

    @pytest.mark.asyncio
    async def test_list_collections_success(self, mock_db, mock_user, mock_collection):
        """Test successful collection listing."""
        with patch.object(KnowledgeService, "list_collections", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([mock_collection], 1)

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get("/api/v1/knowledge")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["collections"]) == 1

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_collections_empty(self, mock_db, mock_user):
        """Test listing empty collections."""
        with patch.object(KnowledgeService, "list_collections", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([], 0)

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get("/api/v1/knowledge")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["collections"] == []

            app.dependency_overrides.clear()


class TestGetCollectionEndpoint:
    """Tests for the GET /api/v1/knowledge/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_collection_success(self, mock_db, mock_user, mock_collection):
        """Test successful collection retrieval."""
        with patch.object(KnowledgeService, "get_collection", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_collection

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get(f"/api/v1/knowledge/{mock_collection.id}")

            assert response.status_code == 200

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self, mock_db, mock_user):
        """Test getting non-existent collection."""
        with patch.object(KnowledgeService, "get_collection", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get(f"/api/v1/knowledge/{uuid4()}")

            assert response.status_code == 404

            app.dependency_overrides.clear()


class TestDeleteCollectionEndpoint:
    """Tests for the DELETE /api/v1/knowledge/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_collection_success(self, mock_db, mock_user):
        """Test successful collection deletion."""
        with patch.object(KnowledgeService, "delete_collection", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.delete(f"/api/v1/knowledge/{uuid4()}")

            assert response.status_code == 204

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_collection_not_found(self, mock_db, mock_user):
        """Test deleting non-existent collection."""
        with patch.object(KnowledgeService, "delete_collection", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.delete(f"/api/v1/knowledge/{uuid4()}")

            assert response.status_code == 404

            app.dependency_overrides.clear()


class TestUploadDocumentEndpoint:
    """Tests for the POST /api/v1/knowledge/{id}/documents endpoint."""

    @pytest.mark.asyncio
    async def test_upload_document_success(self, mock_db, mock_user, mock_collection, mock_document):
        """Test successful document upload."""
        with patch.object(KnowledgeService, "get_collection", new_callable=AsyncMock) as mock_get, \
             patch.object(KnowledgeService, "add_document", new_callable=AsyncMock) as mock_add:

            mock_get.return_value = mock_collection
            mock_add.return_value = mock_document

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            # Create a test file
            test_file = io.BytesIO(b"test content")
            test_file.name = "test.txt"

            response = client.post(
                f"/api/v1/knowledge/{mock_collection.id}/documents",
                files={"file": ("test.txt", test_file, "text/plain")}
            )

            assert response.status_code == 201

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_document_collection_not_found(self, mock_db, mock_user):
        """Test uploading to non-existent collection."""
        with patch.object(KnowledgeService, "get_collection", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            test_file = io.BytesIO(b"test content")

            response = client.post(
                f"/api/v1/knowledge/{uuid4()}/documents",
                files={"file": ("test.txt", test_file, "text/plain")}
            )

            assert response.status_code == 404

            app.dependency_overrides.clear()


class TestListDocumentsEndpoint:
    """Tests for the GET /api/v1/knowledge/{id}/documents endpoint."""

    @pytest.mark.asyncio
    async def test_list_documents_success(self, mock_db, mock_user, mock_collection, mock_document):
        """Test successful document listing."""
        with patch.object(KnowledgeService, "list_documents", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([mock_document], 1)

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get(f"/api/v1/knowledge/{mock_collection.id}/documents")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1

            app.dependency_overrides.clear()


class TestQueryKnowledgeEndpoint:
    """Tests for the POST /api/v1/knowledge/query endpoint."""

    @pytest.mark.asyncio
    async def test_query_knowledge_success(self, mock_db, mock_user, mock_collection):
        """Test successful knowledge query."""
        mock_sources = [
            SourceDocument(
                document_id=uuid4(),
                filename="test.pdf",
                content="Test content",
                score=0.95
            )
        ]

        with patch.object(KnowledgeService, "search_knowledge", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_sources

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/knowledge/query",
                json={
                    "query": "test query",
                    "collection_id": str(mock_collection.id),
                    "top_k": 5
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test query"
            assert data["total"] == 1

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_query_knowledge_empty_results(self, mock_db, mock_user, mock_collection):
        """Test knowledge query with no results."""
        with patch.object(KnowledgeService, "search_knowledge", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/knowledge/query",
                json={
                    "query": "test query",
                    "collection_id": str(mock_collection.id)
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0

            app.dependency_overrides.clear()