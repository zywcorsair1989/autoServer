"""Tests for Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenData,
    PasswordChange,
)
from app.schemas.chat import (
    MessageBase,
    MessageCreate,
    MessageResponse,
    ConversationBase,
    ConversationCreate,
    ConversationResponse,
    ConversationDetail,
    ConversationList,
    ChatRequest,
    ChatResponse,
)
from app.schemas.knowledge import (
    KnowledgeCollectionBase,
    KnowledgeCollectionCreate,
    KnowledgeCollectionResponse,
    KnowledgeCollectionList,
    DocumentBase,
    DocumentResponse,
    DocumentList,
    KnowledgeQuery,
    SourceDocument,
    KnowledgeQueryResponse,
)


# ============================================
# User Schema Tests
# ============================================

class TestUserBase:
    """Tests for UserBase schema."""

    def test_valid_user_base(self):
        """Test creating UserBase with valid data."""
        user = UserBase(username="testuser", email="test@example.com")
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_username_too_short(self):
        """Test that short username raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username="ab", email="test@example.com")
        assert "String should have at least 3 characters" in str(exc_info.value)

    def test_username_too_long(self):
        """Test that long username raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username="a" * 51, email="test@example.com")
        assert "String should have at most 50 characters" in str(exc_info.value)

    def test_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username="testuser", email="invalid-email")
        assert "not a valid email address" in str(exc_info.value)


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_valid_user_create(self):
        """Test creating UserCreate with valid data."""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="Password123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "Password123"

    def test_password_too_short(self):
        """Test that short password raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="Short1"
            )
        assert "String should have at least 8 characters" in str(exc_info.value)

    def test_password_no_uppercase(self):
        """Test that password without uppercase raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="password123"
            )
        assert "at least one uppercase letter" in str(exc_info.value)

    def test_password_no_lowercase(self):
        """Test that password without lowercase raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="PASSWORD123"
            )
        assert "at least one lowercase letter" in str(exc_info.value)

    def test_password_no_digit(self):
        """Test that password without digit raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="PasswordOnly"
            )
        assert "at least one digit" in str(exc_info.value)


class TestUserUpdate:
    """Tests for UserUpdate schema."""

    def test_valid_user_update(self):
        """Test creating UserUpdate with valid data."""
        update = UserUpdate(username="newusername")
        assert update.username == "newusername"
        assert update.email is None
        assert update.role is None

    def test_partial_update(self):
        """Test partial update with only some fields."""
        update = UserUpdate(email="new@example.com")
        assert update.username is None
        assert update.email == "new@example.com"


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_valid_user_response(self):
        """Test creating UserResponse with valid data."""
        user_id = uuid4()
        now = datetime.utcnow()
        user = UserResponse(
            id=user_id,
            username="testuser",
            email="test@example.com",
            role="user",
            is_active=True,
            created_at=now,
            updated_at=now
        )
        assert user.id == user_id
        assert user.username == "testuser"
        assert user.role == "user"
        assert user.is_active is True


class TestUserLogin:
    """Tests for UserLogin schema."""

    def test_valid_login(self):
        """Test creating UserLogin with valid data."""
        login = UserLogin(username="testuser", password="password123")
        assert login.username == "testuser"
        assert login.password == "password123"

    def test_empty_username(self):
        """Test that empty username raises validation error."""
        with pytest.raises(ValidationError):
            UserLogin(username="", password="password123")

    def test_empty_password(self):
        """Test that empty password raises validation error."""
        with pytest.raises(ValidationError):
            UserLogin(username="testuser", password="")


class TestToken:
    """Tests for Token schema."""

    def test_valid_token(self):
        """Test creating Token with valid data."""
        token = Token(access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        assert token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert token.token_type == "bearer"


class TestTokenData:
    """Tests for TokenData schema."""

    def test_valid_token_data(self):
        """Test creating TokenData with valid data."""
        user_id = uuid4()
        token_data = TokenData(user_id=user_id, username="testuser", role="user")
        assert token_data.user_id == user_id
        assert token_data.username == "testuser"

    def test_empty_token_data(self):
        """Test creating TokenData with no data."""
        token_data = TokenData()
        assert token_data.user_id is None
        assert token_data.username is None


class TestPasswordChange:
    """Tests for PasswordChange schema."""

    def test_valid_password_change(self):
        """Test creating PasswordChange with valid data."""
        change = PasswordChange(current_password="OldPassword1", new_password="NewPassword1")
        assert change.current_password == "OldPassword1"
        assert change.new_password == "NewPassword1"

    def test_new_password_validation(self):
        """Test that new password is validated."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(current_password="OldPassword1", new_password="weak")
        assert "at least 8 characters" in str(exc_info.value)


# ============================================
# Chat Schema Tests
# ============================================

class TestMessageBase:
    """Tests for MessageBase schema."""

    def test_valid_message_base(self):
        """Test creating MessageBase with valid data."""
        message = MessageBase(role="user", content="Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_role_too_long(self):
        """Test that long role raises validation error."""
        with pytest.raises(ValidationError):
            MessageBase(role="a" * 21, content="Hello")

    def test_empty_content(self):
        """Test that empty content raises validation error."""
        with pytest.raises(ValidationError):
            MessageBase(role="user", content="")


class TestMessageCreate:
    """Tests for MessageCreate schema."""

    def test_valid_message_create(self):
        """Test creating MessageCreate with valid data."""
        message = MessageCreate(role="user", content="Hello!")
        assert message.role == "user"
        assert message.content == "Hello!"


class TestMessageResponse:
    """Tests for MessageResponse schema."""

    def test_valid_message_response(self):
        """Test creating MessageResponse with valid data."""
        msg_id = uuid4()
        conv_id = uuid4()
        now = datetime.utcnow()
        message = MessageResponse(
            id=msg_id,
            conversation_id=conv_id,
            role="user",
            content="Hello!",
            created_at=now
        )
        assert message.id == msg_id
        assert message.conversation_id == conv_id


class TestConversationBase:
    """Tests for ConversationBase schema."""

    def test_valid_conversation_base(self):
        """Test creating ConversationBase with valid data."""
        conv = ConversationBase(title="My Chat")
        assert conv.title == "My Chat"

    def test_default_title(self):
        """Test default title value."""
        conv = ConversationBase()
        assert conv.title == "New Conversation"


class TestConversationCreate:
    """Tests for ConversationCreate schema."""

    def test_valid_conversation_create(self):
        """Test creating ConversationCreate with valid data."""
        conv = ConversationCreate(title="New Chat")
        assert conv.title == "New Chat"


class TestConversationResponse:
    """Tests for ConversationResponse schema."""

    def test_valid_conversation_response(self):
        """Test creating ConversationResponse with valid data."""
        conv_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        conv = ConversationResponse(
            id=conv_id,
            user_id=user_id,
            title="My Chat",
            created_at=now,
            updated_at=now
        )
        assert conv.id == conv_id
        assert conv.user_id == user_id


class TestConversationDetail:
    """Tests for ConversationDetail schema."""

    def test_valid_conversation_detail(self):
        """Test creating ConversationDetail with valid data."""
        conv_id = uuid4()
        user_id = uuid4()
        msg_id = uuid4()
        now = datetime.utcnow()
        message = MessageResponse(
            id=msg_id,
            conversation_id=conv_id,
            role="user",
            content="Hello!",
            created_at=now
        )
        conv = ConversationDetail(
            id=conv_id,
            user_id=user_id,
            title="My Chat",
            created_at=now,
            updated_at=now,
            messages=[message]
        )
        assert conv.id == conv_id
        assert len(conv.messages) == 1


class TestConversationList:
    """Tests for ConversationList schema."""

    def test_valid_conversation_list(self):
        """Test creating ConversationList with valid data."""
        conv_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        conv = ConversationResponse(
            id=conv_id,
            user_id=user_id,
            title="Chat 1",
            created_at=now,
            updated_at=now
        )
        conv_list = ConversationList(conversations=[conv], total=1)
        assert len(conv_list.conversations) == 1
        assert conv_list.total == 1


class TestChatRequest:
    """Tests for ChatRequest schema."""

    def test_valid_chat_request(self):
        """Test creating ChatRequest with valid data."""
        request = ChatRequest(message="What is AI?")
        assert request.message == "What is AI?"
        assert request.conversation_id is None
        assert request.use_knowledge is False

    def test_chat_request_with_collection(self):
        """Test ChatRequest with knowledge collection."""
        conv_id = uuid4()
        coll_id = uuid4()
        request = ChatRequest(
            message="What is AI?",
            conversation_id=conv_id,
            use_knowledge=True,
            collection_id=coll_id
        )
        assert request.use_knowledge is True
        assert request.collection_id == coll_id


class TestChatResponse:
    """Tests for ChatResponse schema."""

    def test_valid_chat_response(self):
        """Test creating ChatResponse with valid data."""
        msg_id = uuid4()
        conv_id = uuid4()
        now = datetime.utcnow()
        message = MessageResponse(
            id=msg_id,
            conversation_id=conv_id,
            role="assistant",
            content="AI is...",
            created_at=now
        )
        response = ChatResponse(message=message, sources=None)
        assert response.message.role == "assistant"
        assert response.sources is None


# ============================================
# Knowledge Schema Tests
# ============================================

class TestKnowledgeCollectionBase:
    """Tests for KnowledgeCollectionBase schema."""

    def test_valid_collection_base(self):
        """Test creating KnowledgeCollectionBase with valid data."""
        collection = KnowledgeCollectionBase(name="My Collection", description="Test collection")
        assert collection.name == "My Collection"
        assert collection.description == "Test collection"

    def test_collection_base_no_description(self):
        """Test KnowledgeCollectionBase without description."""
        collection = KnowledgeCollectionBase(name="My Collection")
        assert collection.name == "My Collection"
        assert collection.description is None


class TestKnowledgeCollectionCreate:
    """Tests for KnowledgeCollectionCreate schema."""

    def test_valid_collection_create(self):
        """Test creating KnowledgeCollectionCreate with valid data."""
        collection = KnowledgeCollectionCreate(name="New Collection")
        assert collection.name == "New Collection"


class TestKnowledgeCollectionResponse:
    """Tests for KnowledgeCollectionResponse schema."""

    def test_valid_collection_response(self):
        """Test creating KnowledgeCollectionResponse with valid data."""
        coll_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        collection = KnowledgeCollectionResponse(
            id=coll_id,
            user_id=user_id,
            name="My Collection",
            description="Test",
            created_at=now
        )
        assert collection.id == coll_id
        assert collection.user_id == user_id


class TestKnowledgeCollectionList:
    """Tests for KnowledgeCollectionList schema."""

    def test_valid_collection_list(self):
        """Test creating KnowledgeCollectionList with valid data."""
        coll_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        collection = KnowledgeCollectionResponse(
            id=coll_id,
            user_id=user_id,
            name="Collection 1",
            created_at=now
        )
        coll_list = KnowledgeCollectionList(collections=[collection], total=1)
        assert len(coll_list.collections) == 1
        assert coll_list.total == 1


class TestDocumentBase:
    """Tests for DocumentBase schema."""

    def test_valid_document_base(self):
        """Test creating DocumentBase with valid data."""
        doc = DocumentBase(filename="test.pdf", file_size=1024)
        assert doc.filename == "test.pdf"
        assert doc.file_size == 1024


class TestDocumentResponse:
    """Tests for DocumentResponse schema."""

    def test_valid_document_response(self):
        """Test creating DocumentResponse with valid data."""
        doc_id = uuid4()
        coll_id = uuid4()
        now = datetime.utcnow()
        doc = DocumentResponse(
            id=doc_id,
            collection_id=coll_id,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            status="completed",
            created_at=now
        )
        assert doc.id == doc_id
        assert doc.status == "completed"


class TestDocumentList:
    """Tests for DocumentList schema."""

    def test_valid_document_list(self):
        """Test creating DocumentList with valid data."""
        doc_id = uuid4()
        coll_id = uuid4()
        now = datetime.utcnow()
        doc = DocumentResponse(
            id=doc_id,
            collection_id=coll_id,
            filename="doc1.pdf",
            file_path="/uploads/doc1.pdf",
            file_size=2048,
            status="completed",
            created_at=now
        )
        doc_list = DocumentList(documents=[doc], total=1)
        assert len(doc_list.documents) == 1
        assert doc_list.total == 1


class TestKnowledgeQuery:
    """Tests for KnowledgeQuery schema."""

    def test_valid_knowledge_query(self):
        """Test creating KnowledgeQuery with valid data."""
        coll_id = uuid4()
        query = KnowledgeQuery(query="What is AI?", collection_id=coll_id)
        assert query.query == "What is AI?"
        assert query.collection_id == coll_id
        assert query.top_k == 5
        assert query.rerank is False

    def test_knowledge_query_custom_top_k(self):
        """Test KnowledgeQuery with custom top_k."""
        coll_id = uuid4()
        query = KnowledgeQuery(query="What is AI?", collection_id=coll_id, top_k=10, rerank=True)
        assert query.top_k == 10
        assert query.rerank is True

    def test_knowledge_query_top_k_bounds(self):
        """Test KnowledgeQuery top_k validation."""
        coll_id = uuid4()
        with pytest.raises(ValidationError):
            KnowledgeQuery(query="What is AI?", collection_id=coll_id, top_k=0)
        with pytest.raises(ValidationError):
            KnowledgeQuery(query="What is AI?", collection_id=coll_id, top_k=25)


class TestSourceDocument:
    """Tests for SourceDocument schema."""

    def test_valid_source_document(self):
        """Test creating SourceDocument with valid data."""
        doc_id = uuid4()
        source = SourceDocument(
            document_id=doc_id,
            filename="test.pdf",
            content="AI is...",
            score=0.95,
            metadata={"page": 1}
        )
        assert source.document_id == doc_id
        assert source.score == 0.95
        assert source.metadata == {"page": 1}


class TestKnowledgeQueryResponse:
    """Tests for KnowledgeQueryResponse schema."""

    def test_valid_query_response(self):
        """Test creating KnowledgeQueryResponse with valid data."""
        doc_id = uuid4()
        source = SourceDocument(
            document_id=doc_id,
            filename="test.pdf",
            content="AI is...",
            score=0.95
        )
        response = KnowledgeQueryResponse(
            query="What is AI?",
            sources=[source],
            total=1
        )
        assert response.query == "What is AI?"
        assert len(response.sources) == 1
        assert response.total == 1


# ============================================
# Integration Tests
# ============================================

class TestSchemaIntegration:
    """Integration tests for schema relationships."""

    def test_chat_response_with_sources(self):
        """Test ChatResponse with source documents."""
        msg_id = uuid4()
        conv_id = uuid4()
        doc_id = uuid4()
        now = datetime.utcnow()

        message = MessageResponse(
            id=msg_id,
            conversation_id=conv_id,
            role="assistant",
            content="Based on the documents, AI is...",
            created_at=now
        )

        source = SourceDocument(
            document_id=doc_id,
            filename="ai-guide.pdf",
            content="AI is a field of computer science...",
            score=0.92
        )

        response = ChatResponse(message=message, sources=[source])
        assert len(response.sources) == 1
        assert response.sources[0].filename == "ai-guide.pdf"

    def test_conversation_detail_with_messages(self):
        """Test ConversationDetail with multiple messages."""
        conv_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()

        messages = [
            MessageResponse(
                id=uuid4(),
                conversation_id=conv_id,
                role="user",
                content="What is AI?",
                created_at=now
            ),
            MessageResponse(
                id=uuid4(),
                conversation_id=conv_id,
                role="assistant",
                content="AI is...",
                created_at=now
            )
        ]

        conv = ConversationDetail(
            id=conv_id,
            user_id=user_id,
            title="AI Discussion",
            created_at=now,
            updated_at=now,
            messages=messages
        )
        assert len(conv.messages) == 2


# ============================================
# Edge Cases and Error Handling
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_strings_rejected(self):
        """Test that empty strings are rejected where required."""
        with pytest.raises(ValidationError):
            UserBase(username="", email="test@example.com")

        with pytest.raises(ValidationError):
            MessageBase(role="", content="Hello")

    def test_whitespace_in_strings(self):
        """Test handling of whitespace in strings."""
        user = UserBase(username="  testuser  ", email="test@example.com")
        assert user.username == "  testuser  "  # Pydantic doesn't strip by default

    def test_special_characters_in_username(self):
        """Test special characters in username."""
        user = UserBase(username="test_user-123", email="test@example.com")
        assert user.username == "test_user-123"

    def test_unicode_in_content(self):
        """Test unicode characters in message content."""
        message = MessageBase(role="user", content="你好世界 🌍")
        assert message.content == "你好世界 🌍"

    def test_very_long_content(self):
        """Test very long content strings."""
        long_content = "AI is " * 1000
        message = MessageBase(role="assistant", content=long_content)
        assert len(message.content) == len(long_content)