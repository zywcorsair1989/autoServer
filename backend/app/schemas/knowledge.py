"""Pydantic schemas for knowledge collection and document management."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Knowledge Collection schemas
class KnowledgeCollectionBase(BaseModel):
    """Base knowledge collection schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class KnowledgeCollectionCreate(KnowledgeCollectionBase):
    """Schema for creating a knowledge collection."""

    pass


class KnowledgeCollectionResponse(KnowledgeCollectionBase):
    """Schema for knowledge collection response data."""

    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeCollectionList(BaseModel):
    """Schema for list of knowledge collections."""

    collections: List[KnowledgeCollectionResponse]
    total: int


# Document schemas
class DocumentBase(BaseModel):
    """Base document schema with common fields."""

    filename: str
    file_size: int


class DocumentResponse(DocumentBase):
    """Schema for document response data."""

    id: UUID
    collection_id: UUID
    file_path: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    """Schema for list of documents."""

    documents: List[DocumentResponse]
    total: int


# Knowledge Query schemas
class KnowledgeQuery(BaseModel):
    """Schema for knowledge query request."""

    query: str = Field(..., min_length=1)
    collection_id: UUID
    top_k: int = Field(default=5, ge=1, le=20)
    rerank: bool = False


class SourceDocument(BaseModel):
    """Schema for source document in query response."""

    document_id: UUID
    filename: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeQueryResponse(BaseModel):
    """Schema for knowledge query response."""

    query: str
    sources: List[SourceDocument]
    total: int