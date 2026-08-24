"""Pydantic schemas for chat and conversation management."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Message schemas
class MessageBase(BaseModel):
    """Base message schema with common fields."""

    role: str = Field(..., min_length=1, max_length=20)
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    """Schema for creating a message."""

    pass


class MessageResponse(MessageBase):
    """Schema for message response data."""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# Conversation schemas
class ConversationBase(BaseModel):
    """Base conversation schema with common fields."""

    title: str = Field(default="New Conversation", min_length=1, max_length=200)


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""

    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response data."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationResponse):
    """Schema for conversation with messages."""

    messages: List[MessageResponse] = []


class ConversationList(BaseModel):
    """Schema for list of conversations."""

    conversations: List[ConversationResponse]
    total: int


# Chat API schemas
class ChatRequest(BaseModel):
    """Schema for chat API request."""

    message: str = Field(..., min_length=1)
    conversation_id: Optional[UUID] = None
    use_knowledge: bool = False
    collection_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    """Schema for chat API response."""

    message: MessageResponse
    sources: Optional[List["SourceDocument"]] = None


# Import forward reference
from app.schemas.knowledge import SourceDocument

# Update forward references
ChatResponse.model_rebuild()