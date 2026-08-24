"""Knowledge collection API endpoints.

This module provides REST API endpoints for knowledge collection management.
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
    summary="Create a knowledge collection",
    description="Create a new knowledge collection for the current user."
)
async def create_collection(
    collection_data: KnowledgeCollectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeCollectionResponse:
    """Create a new knowledge collection.

    Args:
        collection_data: Collection creation data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Created knowledge collection.
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
    summary="List knowledge collections",
    description="List all knowledge collections for the current user."
)
async def list_collections(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeCollectionList:
    """List knowledge collections for the current user.

    Args:
        skip: Number of collections to skip.
        limit: Maximum number of collections to return.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        List of knowledge collections with total count.
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
    summary="Get a knowledge collection",
    description="Get a specific knowledge collection by ID."
)
async def get_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeCollectionResponse:
    """Get a knowledge collection by ID.

    Args:
        collection_id: UUID of the collection.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Knowledge collection.

    Raises:
        HTTPException: If collection not found.
    """
    service = KnowledgeService(db)
    collection = await service.get_collection(collection_id, current_user.id)

    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge collection {collection_id} not found"
        )

    return collection


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a knowledge collection",
    description="Delete a knowledge collection and all its documents."
)
async def delete_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a knowledge collection.

    Args:
        collection_id: UUID of the collection to delete.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException: If collection not found.
    """
    service = KnowledgeService(db)
    deleted = await service.delete_collection(collection_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge collection {collection_id} not found"
        )


@router.post(
    "/{collection_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Upload a document to a knowledge collection."
)
async def upload_document(
    collection_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Upload a document to a knowledge collection.

    Args:
        collection_id: UUID of the collection.
        file: Uploaded file.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Created document.

    Raises:
        HTTPException: If collection not found or file type not supported.
    """
    import os

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
        )

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )

    service = KnowledgeService(db)

    # Verify collection exists
    collection = await service.get_collection(collection_id, current_user.id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge collection {collection_id} not found"
        )

    # Save file
    upload_dir = os.path.join("uploads", str(collection_id))
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create document record
    document = await service.add_document(
        collection_id,
        current_user.id,
        file.filename,
        file_path,
        file_size
    )

    return document


@router.get(
    "/{collection_id}/documents",
    response_model=DocumentList,
    summary="List documents",
    description="List all documents in a knowledge collection."
)
async def list_documents(
    collection_id: UUID,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentList:
    """List documents in a knowledge collection.

    Args:
        collection_id: UUID of the collection.
        skip: Number of documents to skip.
        limit: Maximum number of documents to return.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        List of documents with total count.

    Raises:
        HTTPException: If collection not found.
    """
    service = KnowledgeService(db)
    documents, total = await service.list_documents(
        collection_id,
        current_user.id,
        skip=skip,
        limit=limit
    )

    return DocumentList(
        documents=documents,
        total=total
    )


@router.post(
    "/{collection_id}/documents/{document_id}/process",
    summary="Process a document",
    description="Process an uploaded document to extract text and generate embeddings."
)
async def process_document(
    collection_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Process a document for RAG.

    Args:
        collection_id: UUID of the collection.
        document_id: UUID of the document to process.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Success message with chunk count.

    Raises:
        HTTPException: If document or collection not found, or processing fails.
    """
    service = KnowledgeService(db, embedding_service=EmbeddingService())

    # Verify collection ownership
    collection = await service.get_collection(collection_id, current_user.id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge collection {collection_id} not found"
        )

    try:
        success = await service.process_document(document_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        return {"message": "Document processed successfully", "document_id": str(document_id)}

    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.delete(
    "/{collection_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description="Delete a document from a knowledge collection."
)
async def delete_document(
    collection_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a document.

    Args:
        collection_id: UUID of the collection.
        document_id: UUID of the document to delete.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException: If document not found.
    """
    service = KnowledgeService(db)

    # Verify collection ownership
    collection = await service.get_collection(collection_id, current_user.id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge collection {collection_id} not found"
        )

    deleted = await service.delete_document(document_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )


@router.post(
    "/query",
    response_model=KnowledgeQueryResponse,
    summary="Query knowledge base",
    description="Search for relevant documents in a knowledge collection."
)
async def query_knowledge(
    query: KnowledgeQuery,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> KnowledgeQueryResponse:
    """Query the knowledge base.

    Args:
        query: Knowledge query with search parameters.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Query response with matching documents.

    Raises:
        HTTPException: If collection not found or query fails.
    """
    service = KnowledgeService(db, embedding_service=EmbeddingService())

    try:
        sources = await service.search_knowledge(query, current_user.id)

        return KnowledgeQueryResponse(
            query=query.query,
            sources=sources,
            total=len(sources)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Knowledge query failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge base: {str(e)}"
        )