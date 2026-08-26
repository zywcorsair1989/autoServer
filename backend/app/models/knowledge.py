"""RAG 系统的知识库集合模型。"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeCollection(Base):
    """知识库集合模型，用于组织文档。"""

    __tablename__ = "knowledge_collections"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # 公共知识库：所有用户可检索（如"食尚订产品文档"），仅所有者可管理
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # 关系 - 使用 lazy="selectin" 以兼容异步
    user = relationship(
        "User",
        back_populates="knowledge_collections",
        lazy="selectin"
    )
    documents = relationship(
        "Document",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index('ix_knowledge_collections_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeCollection {self.name}>"