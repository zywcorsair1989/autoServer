"""知识库 API 端点。

这个模块为知识库管理提供 REST API 端点。
"""

from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeCollectionCreate,
    KnowledgeCollectionResponse,
    KnowledgeCollectionList,
    KnowledgeQuery,
    KnowledgeQueryResponse,
    DocumentList,
    DocumentResponse,
    SourceDocument,
)
from app.services.knowledge_service import KnowledgeService
from app.ai.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post(
    "",
    response_model=KnowledgeCollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建知识库",
    description="为当前用户创建新知识库。"
)
async def create_collection(
    collection_data: KnowledgeCollectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeCollectionResponse:
    """创建新知识库。

    Args:
        collection_data: 知识库创建数据。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        创建的知识库。
    """
    service = KnowledgeService(db)
    collection = await service.create_collection(
        current_user.id,
        collection_data
    )
    return collection


@router.get(
    "",
    response_model=KnowledgeCollectionList,
    summary="列出知识库",
    description="列出当前用户的所有知识库。"
)
async def list_collections(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeCollectionList:
    """为当前用户列出知识库。

    Args:
        skip: 要跳过的知识库数量。
        limit: 要返回的最大知识库数量。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        知识库列表和总数。
    """
    service = KnowledgeService(db)
    collections, total = await service.list_collections(
        current_user.id,
        skip=skip,
        limit=limit
    )
    return KnowledgeCollectionList(
        collections=collections,
        total=total
    )


@router.get(
    "/{collection_id}",
    response_model=KnowledgeCollectionResponse,
    summary="获取知识库",
    description="获取特定知识库。"
)
async def get_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeCollectionResponse:
    """获取特定知识库。

    Args:
        collection_id: 知识库的 UUID。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        知识库。
    """
    service = KnowledgeService(db)
    collection = await service.get_collection(
        collection_id,
        current_user.id
    )
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库 {collection_id} 未找到"
        )

    return collection


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识库",
    description="删除知识库及其所有文档。"
)
async def delete_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """删除知识库。

    Args:
        collection_id: 要删除的知识库的 UUID。
        current_user: 当前认证用户。
        db: 数据库会话。

    Raises:
        HTTPException: 如果知识库未找到。
    """
    service = KnowledgeService(db)
    deleted = await service.delete_collection(
        collection_id,
        current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库 {collection_id} 未找到"
        )


@router.post(
    "/query",
    response_model=KnowledgeQueryResponse,
    summary="知识库查询",
    description="在知识库中查询。"
)
async def query_knowledge(
    query: KnowledgeQuery,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeQueryResponse:
    """在知识库中查询。

    Args:
        query: 查询请求。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        查询响应。
    """
    service = RAGService(db)
    result = await service.query(
        query,
        current_user.id
    )
    return result


@router.post(
    "/collections",
    summary="创建知识库集合",
    description="创建知识库集合。"
)
async def create_collection(
    collection_data: KnowledgeCollectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeCollectionResponse:
    """创建知识库集合。

    Args:
        collection_data: 知识库集合创建数据。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        创建的知识库集合。
    """
    service = KnowledgeService(db)
    collection = await service.create_collection(
        current_user.id,
        collection_data
    )
    return collection