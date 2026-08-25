"""对话和消息模型，用于 RAG 系统。"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Conversation(Base):
    """对话模型，用于聊天会话。"""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="新对话"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 关系 - 使用 lazy="selectin" 以兼容异步
    user = relationship(
        "User",
        back_populates="conversations",
        lazy="selectin"
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="selectin"
    )

    # 索引
    __table_args__ = (
        Index('ix_conversations_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.title}>"


class Message(Base):
    """单个聊天消息的模型。"""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    sources: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # 关系 - 使用 lazy="selectin" 以兼容异步
    conversation = relationship(
        "Conversation",
        back_populates="messages",
        lazy="selectin"
    )

    # 索引
    __table_args__ = (
        Index('ix_messages_conversation_id', 'conversation_id'),
    )

    def __repr__(self) -> str:
        return f"<Message {self.role}: {self.content[:50]}...>"