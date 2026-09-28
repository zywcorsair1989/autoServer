"""RAG 系统的文档和文档块模型。"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.core.database import Base


class Document(Base):
    """上传文件的文档模型。"""

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

    # 关系 - 使用 lazy="selectin" 以兼容异步
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
    """存储带有嵌入向量的文本块的文档块模型。"""

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
    embedding: Mapped[list] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION),
        nullable=True
    )
    # 修正：数据库中的字段是 metadata，但在 Python 中应使用 chunk_metadata
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata",  # 修正：映射到数据库中的 metadata 字段
        JSONB,
        nullable=True,
        default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # 关系 - 使用 lazy="selectin" 以兼容异步
    document = relationship(
        "Document",
        back_populates="chunks",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index('ix_document_chunks_document_id', 'document_id'),
        Index(
            'ix_document_chunks_embedding',
            embedding,
            postgresql_using='hnsw',
            # pgvector 的 vector 类型没有默认 opclass，必须显式指定，
            # 且需与检索使用的 cosine_distance(<=>) 保持一致
            postgresql_ops={'embedding': 'vector_cosine_ops'},
            postgresql_with={'m': 16, 'ef_construction': 64},
        ),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk {self.id}>"