"""Pydantic 模式，用于知识库集合和文档管理。"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# 知识库集合模式
class KnowledgeCollectionBase(BaseModel):
    """带常用字段的知识库集合基础模式。"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class KnowledgeCollectionCreate(KnowledgeCollectionBase):
    """创建知识库集合的模式。"""

    pass


class KnowledgeCollectionResponse(KnowledgeCollectionBase):
    """知识库集合响应数据的模式。"""

    id: UUID
    user_id: UUID
    is_public: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeCollectionList(BaseModel):
    """知识库集合列表的模式。"""

    collections: List[KnowledgeCollectionResponse]
    total: int


# 文档模式
class DocumentBase(BaseModel):
    """带常用字段的文档基础模式。"""

    filename: str
    file_size: int


class DocumentResponse(DocumentBase):
    """文档响应数据的模式。"""

    id: UUID
    collection_id: UUID
    file_path: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    """文档列表的模式。"""

    documents: List[DocumentResponse]
    total: int


# 知识库查询模式
class KnowledgeQuery(BaseModel):
    """知识库查询请求的模式。"""

    query: str = Field(..., min_length=1)
    collection_id: UUID
    top_k: int = Field(default=5, ge=1, le=20)
    rerank: bool = False


class SourceDocument(BaseModel):
    """查询响应中源文档的模式。"""

    document_id: UUID
    filename: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeQueryResponse(BaseModel):
    """知识库查询响应的模式。"""

    query: str
    sources: List[SourceDocument]
    total: int