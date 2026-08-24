"""Pydantic 模式，用于聊天和对话管理。"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# 消息模式
class MessageBase(BaseModel):
    """带常用字段的消息基础模式。"""

    role: str = Field(..., min_length=1, max_length=20)
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    """创建消息的模式。"""

    pass


class MessageResponse(MessageBase):
    """消息响应数据的模式。"""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# 对话模式
class ConversationBase(BaseModel):
    """带常用字段的对话基础模式。"""

    title: str = Field(default="新对话", min_length=1, max_length=200)


class ConversationCreate(ConversationBase):
    """创建对话的模式。"""

    pass


class ConversationResponse(ConversationBase):
    """对话响应数据的模式。"""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationResponse):
    """带消息的对话模式。"""

    messages: List[MessageResponse] = []


class ConversationList(BaseModel):
    """对话列表的模式。"""

    conversations: List[ConversationResponse]
    total: int


# 聊天 API 模式
class ChatRequest(BaseModel):
    """聊天 API 请求的模式。"""

    message: str = Field(..., min_length=1)
    conversation_id: Optional[UUID] = None
    use_knowledge: bool = False
    collection_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    """聊天 API 响应的模式。"""

    message: MessageResponse
    sources: Optional[List["SourceDocument"]] = None


# 导入前向引用
from app.schemas.knowledge import SourceDocument

# 更新前向引用
ChatResponse.model_rebuild()