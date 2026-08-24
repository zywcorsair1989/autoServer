"""Tests for database models."""

import pytest
from datetime import datetime
from uuid import UUID

from app.models import User, Conversation, Message, KnowledgeCollection, Document, DocumentChunk


class TestUserModel:
    """Tests for User model."""

    def test_user_instantiation(self):
        """Test that User model can be instantiated with all fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            role="user",
            is_active=True
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_123"
        assert user.role == "user"
        assert user.is_active is True

    def test_user_id_field_type(self):
        """Test that User id field accepts UUID values."""
        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )
        assert isinstance(user.id, UUID)
        assert str(user.id) == "12345678-1234-5678-1234-567812345678"

    def test_user_required_fields(self):
        """Test that User model has required fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            role="admin",
            is_active=False
        )
        assert user.role == "admin"
        assert user.is_active is False

    def test_user_repr(self):
        """Test User model string representation."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )
        assert "testuser" in str(user)

    def test_user_table_name(self):
        """Test User model table name."""
        assert User.__tablename__ == "users"

    def test_user_indexes(self):
        """Test User model has proper indexes."""
        # Check that indexes are defined
        assert hasattr(User, '__table_args__')


class TestConversationModel:
    """Tests for Conversation model."""

    def test_conversation_instantiation(self):
        """Test that Conversation model can be instantiated."""
        conversation = Conversation(
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            title="Test Conversation"
        )
        assert conversation.title == "Test Conversation"
        assert isinstance(conversation.user_id, UUID)

    def test_conversation_id_field_type(self):
        """Test that Conversation id field accepts UUID values."""
        conversation = Conversation(
            id=UUID("12345678-1234-5678-1234-567812345679"),
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            title="Test Conversation"
        )
        assert isinstance(conversation.id, UUID)

    def test_conversation_repr(self):
        """Test Conversation model string representation."""
        conversation = Conversation(
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            title="Test Conversation"
        )
        assert "Test Conversation" in str(conversation)

    def test_conversation_table_name(self):
        """Test Conversation model table name."""
        assert Conversation.__tablename__ == "conversations"


class TestMessageModel:
    """Tests for Message model."""

    def test_message_instantiation(self):
        """Test that Message model can be instantiated."""
        message = Message(
            conversation_id=UUID("12345678-1234-5678-1234-567812345678"),
            role="user",
            content="Hello, world!"
        )
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert isinstance(message.conversation_id, UUID)

    def test_message_roles(self):
        """Test Message model accepts valid roles."""
        for role in ["user", "assistant"]:
            message = Message(
                conversation_id=UUID("12345678-1234-5678-1234-567812345678"),
                role=role,
                content="Test content"
            )
            assert message.role == role

    def test_message_id_field_type(self):
        """Test that Message id field accepts UUID values."""
        message = Message(
            id=UUID("12345678-1234-5678-1234-567812345680"),
            conversation_id=UUID("12345678-1234-5678-1234-567812345678"),
            role="user",
            content="Hello, world!"
        )
        assert isinstance(message.id, UUID)

    def test_message_repr(self):
        """Test Message model string representation."""
        message = Message(
            conversation_id=UUID("12345678-1234-5678-1234-567812345678"),
            role="user",
            content="This is a test message content"
        )
        assert "user" in str(message)

    def test_message_table_name(self):
        """Test Message model table name."""
        assert Message.__tablename__ == "messages"


class TestKnowledgeCollectionModel:
    """Tests for KnowledgeCollection model."""

    def test_knowledge_collection_instantiation(self):
        """Test that KnowledgeCollection model can be instantiated."""
        collection = KnowledgeCollection(
            name="Test Collection",
            description="Test description",
            user_id=UUID("12345678-1234-5678-1234-567812345678")
        )
        assert collection.name == "Test Collection"
        assert collection.description == "Test description"
        assert isinstance(collection.user_id, UUID)

    def test_knowledge_collection_optional_description(self):
        """Test KnowledgeCollection model with None description."""
        collection = KnowledgeCollection(
            name="Test Collection",
            description=None,
            user_id=UUID("12345678-1234-5678-1234-567812345678")
        )
        assert collection.name == "Test Collection"

    def test_knowledge_collection_id_field_type(self):
        """Test that KnowledgeCollection id field accepts UUID values."""
        collection = KnowledgeCollection(
            id=UUID("12345678-1234-5678-1234-567812345681"),
            name="Test Collection",
            user_id=UUID("12345678-1234-5678-1234-567812345678")
        )
        assert isinstance(collection.id, UUID)

    def test_knowledge_collection_repr(self):
        """Test KnowledgeCollection model string representation."""
        collection = KnowledgeCollection(
            name="Test Collection",
            user_id=UUID("12345678-1234-5678-1234-567812345678")
        )
        assert "Test Collection" in str(collection)

    def test_knowledge_collection_table_name(self):
        """Test KnowledgeCollection model table name."""
        assert KnowledgeCollection.__tablename__ == "knowledge_collections"


class TestDocumentModel:
    """Tests for Document model."""

    def test_document_instantiation(self):
        """Test that Document model can be instantiated."""
        document = Document(
            collection_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024
        )
        assert document.filename == "test.pdf"
        assert document.file_path == "/uploads/test.pdf"
        assert document.file_size == 1024

    def test_document_with_status(self):
        """Test Document model with different statuses."""
        for status in ["processing", "completed", "failed"]:
            document = Document(
                collection_id=UUID("12345678-1234-5678-1234-567812345678"),
                filename="test.pdf",
                file_path="/uploads/test.pdf",
                file_size=1024,
                status=status
            )
            assert document.status == status

    def test_document_id_field_type(self):
        """Test that Document id field accepts UUID values."""
        document = Document(
            id=UUID("12345678-1234-5678-1234-567812345682"),
            collection_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024
        )
        assert isinstance(document.id, UUID)

    def test_document_repr(self):
        """Test Document model string representation."""
        document = Document(
            collection_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024
        )
        assert "test.pdf" in str(document)

    def test_document_table_name(self):
        """Test Document model table name."""
        assert Document.__tablename__ == "documents"


class TestDocumentChunkModel:
    """Tests for DocumentChunk model."""

    def test_document_chunk_instantiation(self):
        """Test that DocumentChunk model can be instantiated."""
        chunk = DocumentChunk(
            document_id=UUID("12345678-1234-5678-1234-567812345678"),
            content="This is a test chunk content"
        )
        assert chunk.content == "This is a test chunk content"
        assert isinstance(chunk.document_id, UUID)

    def test_document_chunk_with_metadata(self):
        """Test DocumentChunk model with custom metadata."""
        chunk = DocumentChunk(
            document_id=UUID("12345678-1234-5678-1234-567812345678"),
            content="Test content",
            chunk_metadata={"page": 1, "position": 0}
        )
        assert chunk.chunk_metadata["page"] == 1
        assert chunk.chunk_metadata["position"] == 0

    def test_document_chunk_with_embedding(self):
        """Test DocumentChunk model with embedding."""
        chunk = DocumentChunk(
            document_id=UUID("12345678-1234-5678-1234-567812345678"),
            content="Test content",
            embedding="[0.1, 0.2, 0.3]"
        )
        assert chunk.embedding == "[0.1, 0.2, 0.3]"

    def test_document_chunk_id_field_type(self):
        """Test that DocumentChunk id field accepts UUID values."""
        chunk = DocumentChunk(
            id=UUID("12345678-1234-5678-1234-567812345683"),
            document_id=UUID("12345678-1234-5678-1234-567812345678"),
            content="Test content"
        )
        assert isinstance(chunk.id, UUID)

    def test_document_chunk_repr(self):
        """Test DocumentChunk model string representation."""
        chunk = DocumentChunk(
            document_id=UUID("12345678-1234-5678-1234-567812345678"),
            content="Test content"
        )
        assert "DocumentChunk" in str(chunk)

    def test_document_chunk_table_name(self):
        """Test DocumentChunk model table name."""
        assert DocumentChunk.__tablename__ == "document_chunks"


class TestModelRelationships:
    """Tests for model relationships."""

    def test_user_has_conversations_relationship(self):
        """Test User model has conversations relationship."""
        assert hasattr(User, 'conversations')

    def test_user_has_knowledge_collections_relationship(self):
        """Test User model has knowledge_collections relationship."""
        assert hasattr(User, 'knowledge_collections')

    def test_conversation_has_user_relationship(self):
        """Test Conversation model has user relationship."""
        assert hasattr(Conversation, 'user')

    def test_conversation_has_messages_relationship(self):
        """Test Conversation model has messages relationship."""
        assert hasattr(Conversation, 'messages')

    def test_message_has_conversation_relationship(self):
        """Test Message model has conversation relationship."""
        assert hasattr(Message, 'conversation')

    def test_knowledge_collection_has_user_relationship(self):
        """Test KnowledgeCollection model has user relationship."""
        assert hasattr(KnowledgeCollection, 'user')

    def test_knowledge_collection_has_documents_relationship(self):
        """Test KnowledgeCollection model has documents relationship."""
        assert hasattr(KnowledgeCollection, 'documents')

    def test_document_has_collection_relationship(self):
        """Test Document model has collection relationship."""
        assert hasattr(Document, 'collection')

    def test_document_has_chunks_relationship(self):
        """Test Document model has chunks relationship."""
        assert hasattr(Document, 'chunks')

    def test_document_chunk_has_document_relationship(self):
        """Test DocumentChunk model has document relationship."""
        assert hasattr(DocumentChunk, 'document')