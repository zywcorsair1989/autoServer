"""Document and DocumentChunk models for the RAG system."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Document(Base):
    """Document model for uploaded files."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    collection_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="processing"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships - use lazy="selectin" for async compatibility
    collection = relationship(
        "KnowledgeCollection",
        back_populates="documents",
        lazy="selectin"
    )
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index('ix_documents_collection_id', 'collection_id'),
        Index('ix_documents_status', 'status'),
    )

    def __repr__(self) -> str:
        return f"<Document {self.filename}>"


class DocumentChunk(Base):
    """Document chunk model for storing text chunks with embeddings."""

    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    embedding: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    chunk_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships - use lazy="selectin" for async compatibility
    document = relationship(
        "Document",
        back_populates="chunks",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index('ix_document_chunks_document_id', 'document_id'),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk {self.id}>"