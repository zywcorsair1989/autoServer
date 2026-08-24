"""Tests for chat API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.services.chat_service import ChatService


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
def mock_conversation(mock_user):
    """Create a mock conversation."""
    conv = MagicMock(spec=Conversation)
    conv.id = uuid4()
    conv.user_id = mock_user.id
    conv.title = "Test Conversation"
    conv.created_at = datetime.utcnow()
    conv.updated_at = datetime.utcnow()
    conv.messages = []
    return conv


@pytest.fixture
def mock_message(mock_conversation):
    """Create a mock message."""
    msg = MagicMock(spec=Message)
    msg.id = uuid4()
    msg.conversation_id = mock_conversation.id
    msg.role = "assistant"
    msg.content = "Test response"
    msg.created_at = datetime.utcnow()
    return msg


class TestCreateConversationEndpoint:
    """Tests for the /api/v1/chat/conversations endpoint."""

    @pytest.mark.asyncio
    async def test_create_conversation_success(self, mock_db, mock_user, mock_conversation):
        """Test successful conversation creation."""
        with patch.object(ChatService, "create_conversation", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_conversation

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/chat/conversations",
                json={"title": "Test Conversation"}
            )

            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Test Conversation"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_conversation_default_title(self, mock_db, mock_user, mock_conversation):
        """Test conversation creation with default title."""
        mock_conversation.title = "New Conversation"
        with patch.object(ChatService, "create_conversation", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_conversation

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/chat/conversations",
                json={}
            )

            assert response.status_code == 201

            app.dependency_overrides.clear()


class TestListConversationsEndpoint:
    """Tests for the GET /api/v1/chat/conversations endpoint."""

    @pytest.mark.asyncio
    async def test_list_conversations_success(self, mock_db, mock_user, mock_conversation):
        """Test successful conversation listing."""
        with patch.object(ChatService, "list_conversations", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([mock_conversation], 1)

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get("/api/v1/chat/conversations")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["conversations"]) == 1

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, mock_db, mock_user):
        """Test listing empty conversations."""
        with patch.object(ChatService, "list_conversations", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([], 0)

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get("/api/v1/chat/conversations")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["conversations"] == []

            app.dependency_overrides.clear()


class TestGetConversationEndpoint:
    """Tests for the GET /api/v1/chat/conversations/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_conversation_success(self, mock_db, mock_user, mock_conversation):
        """Test successful conversation retrieval."""
        with patch.object(ChatService, "get_conversation", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_conversation

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get(f"/api/v1/chat/conversations/{mock_conversation.id}")

            assert response.status_code == 200

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, mock_db, mock_user):
        """Test getting non-existent conversation."""
        with patch.object(ChatService, "get_conversation", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.get(f"/api/v1/chat/conversations/{uuid4()}")

            assert response.status_code == 404

            app.dependency_overrides.clear()


class TestDeleteConversationEndpoint:
    """Tests for the DELETE /api/v1/chat/conversations/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, mock_db, mock_user):
        """Test successful conversation deletion."""
        with patch.object(ChatService, "delete_conversation", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.delete(f"/api/v1/chat/conversations/{uuid4()}")

            assert response.status_code == 204

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, mock_db, mock_user):
        """Test deleting non-existent conversation."""
        with patch.object(ChatService, "delete_conversation", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.delete(f"/api/v1/chat/conversations/{uuid4()}")

            assert response.status_code == 404

            app.dependency_overrides.clear()


class TestChatEndpoint:
    """Tests for the POST /api/v1/chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_create_new_conversation(self, mock_db, mock_user, mock_conversation, mock_message):
        """Test chat with new conversation creation."""
        with patch.object(ChatService, "create_conversation", new_callable=AsyncMock) as mock_create, \
             patch.object(ChatService, "add_message", new_callable=AsyncMock) as mock_add, \
             patch.object(ChatService, "get_conversation_history", new_callable=AsyncMock) as mock_history, \
             patch("app.ai.llm_service.LLMService.generate", new_callable=AsyncMock) as mock_llm:

            mock_create.return_value = mock_conversation
            mock_add.return_value = mock_message
            mock_history.return_value = []
            mock_llm.return_value = "Test response"

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/chat",
                json={"message": "Test message"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_chat_existing_conversation(self, mock_db, mock_user, mock_conversation, mock_message):
        """Test chat with existing conversation."""
        with patch.object(ChatService, "get_conversation", new_callable=AsyncMock) as mock_get, \
             patch.object(ChatService, "add_message", new_callable=AsyncMock) as mock_add, \
             patch.object(ChatService, "get_conversation_history", new_callable=AsyncMock) as mock_history, \
             patch("app.ai.llm_service.LLMService.generate", new_callable=AsyncMock) as mock_llm:

            mock_get.return_value = mock_conversation
            mock_add.return_value = mock_message
            mock_history.return_value = []
            mock_llm.return_value = "Test response"

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "Test message",
                    "conversation_id": str(mock_conversation.id)
                }
            )

            assert response.status_code == 200

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_chat_conversation_not_found(self, mock_db, mock_user):
        """Test chat with non-existent conversation."""
        with patch.object(ChatService, "get_conversation", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "Test message",
                    "conversation_id": str(uuid4())
                }
            )

            assert response.status_code == 404

            app.dependency_overrides.clear()