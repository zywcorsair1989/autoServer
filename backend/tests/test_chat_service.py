"""Tests for the chat service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.chat_service import ChatService
from app.schemas.chat import ConversationCreate, MessageCreate
from app.models.conversation import Conversation, Message


class TestCreateConversation:
    """Tests for creating conversations."""

    @pytest.mark.asyncio
    async def test_create_conversation_success(self):
        """Test successful conversation creation."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        user_id = uuid4()
        conversation_data = ConversationCreate(title="Test Conversation")

        service = ChatService(mock_db)
        conversation = await service.create_conversation(user_id, conversation_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        assert conversation.user_id == user_id
        assert conversation.title == "Test Conversation"

    @pytest.mark.asyncio
    async def test_create_conversation_default_title(self):
        """Test conversation creation with default title."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        user_id = uuid4()
        conversation_data = ConversationCreate()

        service = ChatService(mock_db)
        conversation = await service.create_conversation(user_id, conversation_data)

        assert conversation.title == "New Conversation"


class TestGetConversation:
    """Tests for getting conversations."""

    @pytest.mark.asyncio
    async def test_get_conversation_found(self):
        """Test getting an existing conversation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()
        user_id = uuid4()

        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = conversation_id
        mock_conversation.user_id = user_id
        mock_conversation.title = "Test Conversation"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conversation
        mock_db.execute.return_value = mock_result

        service = ChatService(mock_db)
        result = await service.get_conversation(conversation_id, user_id)

        assert result == mock_conversation

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self):
        """Test getting a non-existent conversation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ChatService(mock_db)
        result = await service.get_conversation(conversation_id, user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_conversation_wrong_user(self):
        """Test getting a conversation belonging to another user."""
        mock_db = AsyncMock()
        conversation_id = uuid4()
        user_id = uuid4()
        other_user_id = uuid4()

        # Mock returns None because user_id doesn't match
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ChatService(mock_db)
        result = await service.get_conversation(conversation_id, other_user_id)

        assert result is None


class TestListConversations:
    """Tests for listing conversations."""

    @pytest.mark.asyncio
    async def test_list_conversations_success(self):
        """Test successful conversation listing."""
        mock_db = AsyncMock()
        user_id = uuid4()

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        # Mock list query
        mock_conversations = [
            MagicMock(spec=Conversation),
            MagicMock(spec=Conversation)
        ]
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_conversations

        # Set up execute to return different results for different calls
        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        service = ChatService(mock_db)
        conversations, total = await service.list_conversations(user_id, skip=0, limit=10)

        assert total == 5
        assert len(conversations) == 2

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self):
        """Test listing conversations when user has none."""
        mock_db = AsyncMock()
        user_id = uuid4()

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        # Mock list query
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        service = ChatService(mock_db)
        conversations, total = await service.list_conversations(user_id)

        assert total == 0
        assert len(conversations) == 0

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self):
        """Test conversation listing with pagination."""
        mock_db = AsyncMock()
        user_id = uuid4()

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 25

        # Mock list query
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        service = ChatService(mock_db)
        conversations, total = await service.list_conversations(user_id, skip=10, limit=10)

        assert total == 25


class TestDeleteConversation:
    """Tests for deleting conversations."""

    @pytest.mark.asyncio
    async def test_delete_conversation_success(self):
        """Test successful conversation deletion."""
        mock_db = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        conversation_id = uuid4()
        user_id = uuid4()

        # Mock get_conversation to return conversation
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = conversation_id

        with patch.object(
            ChatService,
            'get_conversation',
            return_value=mock_conversation
        ):
            service = ChatService(mock_db)
            result = await service.delete_conversation(conversation_id, user_id)

            assert result is True
            mock_db.delete.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self):
        """Test deleting a non-existent conversation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()
        user_id = uuid4()

        with patch.object(
            ChatService,
            'get_conversation',
            return_value=None
        ):
            service = ChatService(mock_db)
            result = await service.delete_conversation(conversation_id, user_id)

            assert result is False
            mock_db.delete.assert_not_called()


class TestAddMessage:
    """Tests for adding messages."""

    @pytest.mark.asyncio
    async def test_add_message_success(self):
        """Test successful message creation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()

        # Mock conversation exists
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = conversation_id

        mock_conv_result = MagicMock()
        mock_conv_result.scalar_one_or_none.return_value = mock_conversation

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute.return_value = mock_conv_result

        service = ChatService(mock_db)
        message_data = MessageCreate(
            role="user",
            content="Hello, this is a test message."
        )

        message = await service.add_message(conversation_id, message_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert message.conversation_id == conversation_id
        assert message.role == "user"
        assert message.content == "Hello, this is a test message."

    @pytest.mark.asyncio
    async def test_add_message_conversation_not_found(self):
        """Test adding message to non-existent conversation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()

        # Mock conversation not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ChatService(mock_db)
        message_data = MessageCreate(role="user", content="Test message")

        with pytest.raises(ValueError) as exc_info:
            await service.add_message(conversation_id, message_data)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_message_assistant_role(self):
        """Test adding assistant message."""
        mock_db = AsyncMock()
        conversation_id = uuid4()

        mock_conversation = MagicMock(spec=Conversation)
        mock_conv_result = MagicMock()
        mock_conv_result.scalar_one_or_none.return_value = mock_conversation

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute.return_value = mock_conv_result

        service = ChatService(mock_db)
        message_data = MessageCreate(
            role="assistant",
            content="This is an assistant response."
        )

        message = await service.add_message(conversation_id, message_data)

        assert message.role == "assistant"


class TestGetMessages:
    """Tests for getting messages."""

    @pytest.mark.asyncio
    async def test_get_messages_success(self):
        """Test getting messages for a conversation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()

        mock_messages = [
            MagicMock(spec=Message),
            MagicMock(spec=Message)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_db.execute.return_value = mock_result

        service = ChatService(mock_db)
        messages = await service.get_messages(conversation_id)

        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_get_messages_pagination(self):
        """Test getting messages with pagination."""
        mock_db = AsyncMock()
        conversation_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = ChatService(mock_db)
        messages = await service.get_messages(conversation_id, skip=10, limit=20)

        assert messages == []


class TestUpdateConversationTitle:
    """Tests for updating conversation title."""

    @pytest.mark.asyncio
    async def test_update_title_success(self):
        """Test successful title update."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        conversation_id = uuid4()
        user_id = uuid4()

        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = conversation_id

        with patch.object(
            ChatService,
            'get_conversation',
            return_value=mock_conversation
        ):
            service = ChatService(mock_db)
            result = await service.update_conversation_title(
                conversation_id, user_id, "New Title"
            )

            assert result == mock_conversation
            assert mock_conversation.title == "New Title"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_title_not_found(self):
        """Test updating title for non-existent conversation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()
        user_id = uuid4()

        with patch.object(
            ChatService,
            'get_conversation',
            return_value=None
        ):
            service = ChatService(mock_db)
            result = await service.update_conversation_title(
                conversation_id, user_id, "New Title"
            )

            assert result is None
            mock_db.commit.assert_not_called()


class TestGetConversationHistory:
    """Tests for getting conversation history."""

    @pytest.mark.asyncio
    async def test_get_history_success(self):
        """Test getting conversation history."""
        mock_db = AsyncMock()
        conversation_id = uuid4()

        # Create mock messages
        msg1 = MagicMock(spec=Message)
        msg1.role = "user"
        msg1.content = "Hello"

        msg2 = MagicMock(spec=Message)
        msg2.role = "assistant"
        msg2.content = "Hi there!"

        with patch.object(
            ChatService,
            'get_messages',
            return_value=[msg1, msg2]
        ):
            service = ChatService(mock_db)
            history = await service.get_conversation_history(conversation_id)

            assert len(history) == 2
            assert history[0] == {"role": "user", "content": "Hello"}
            assert history[1] == {"role": "assistant", "content": "Hi there!"}

    @pytest.mark.asyncio
    async def test_get_history_empty(self):
        """Test getting history for empty conversation."""
        mock_db = AsyncMock()
        conversation_id = uuid4()

        with patch.object(
            ChatService,
            'get_messages',
            return_value=[]
        ):
            service = ChatService(mock_db)
            history = await service.get_conversation_history(conversation_id)

            assert len(history) == 0