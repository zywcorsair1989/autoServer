"""Pydantic schemas for the RAG system."""

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

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    "PasswordChange",
    # Chat schemas
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "ConversationBase",
    "ConversationCreate",
    "ConversationResponse",
    "ConversationDetail",
    "ConversationList",
    "ChatRequest",
    "ChatResponse",
    # Knowledge schemas
    "KnowledgeCollectionBase",
    "KnowledgeCollectionCreate",
    "KnowledgeCollectionResponse",
    "KnowledgeCollectionList",
    "DocumentBase",
    "DocumentResponse",
    "DocumentList",
    "KnowledgeQuery",
    "SourceDocument",
    "KnowledgeQueryResponse",
]