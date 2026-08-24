"""Knowledge service for knowledge base management.

This module provides business logic for managing knowledge collections,
documents, and document chunks in the RAG system.
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge import KnowledgeCollection
from app.models.document import Document, DocumentChunk
from app.schemas.knowledge import (
    KnowledgeCollectionCreate,
    KnowledgeQuery,
    SourceDocument,
)
from app.utils.document_processor import DocumentProcessor
from app.ai.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service class for knowledge management operations.

    Handles knowledge collections, documents, and vector search.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """Initialize the knowledge service.

        Args:
            db: AsyncSession for database operations.
            embedding_service: Optional embedding service for vector operations.
        """
        self.db = db
        self.embedding_service = embedding_service
        self.document_processor = DocumentProcessor()

    # ==================== Collection Management ====================

    async def create_collection(
        self,
        user_id: UUID,
        collection_data: KnowledgeCollectionCreate
    ) -> KnowledgeCollection:
        """Create a new knowledge collection.

        Args:
            user_id: UUID of the user creating the collection.
            collection_data: Collection creation data.

        Returns:
            Created KnowledgeCollection object.
        """
        collection = KnowledgeCollection(
            user_id=user_id,
            name=collection_data.name,
            description=collection_data.description
        )

        self.db.add(collection)
        await self.db.commit()
        await self.db.refresh(collection)

        logger.info(f"Created knowledge collection {collection.id} for user {user_id}")
        return collection

    async def get_collection(
        self,
        collection_id: UUID,
        user_id: UUID
    ) -> Optional[KnowledgeCollection]:
        """Get a knowledge collection by ID.

        Args:
            collection_id: UUID of the collection.
            user_id: UUID of the user.

        Returns:
            KnowledgeCollection if found and owned by user, None otherwise.
        """
        result = await self.db.execute(
            select(KnowledgeCollection)
            .options(selectinload(KnowledgeCollection.documents))
            .where(
                KnowledgeCollection.id == collection_id,
                KnowledgeCollection.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_collections(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[KnowledgeCollection], int]:
        """List knowledge collections for a user.

        Args:
            user_id: UUID of the user.
            skip: Number of collections to skip.
            limit: Maximum number of collections to return.

        Returns:
            Tuple of (list of collections, total count).
        """
        # Get total count
        count_result = await self.db.execute(
            select(func.count(KnowledgeCollection.id))
            .where(KnowledgeCollection.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Get collections
        result = await self.db.execute(
            select(KnowledgeCollection)
            .where(KnowledgeCollection.user_id == user_id)
            .order_by(KnowledgeCollection.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        collections = list(result.scalars().all())

        return collections, total

    async def delete_collection(
        self,
        collection_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a knowledge collection and all its documents.

        Args:
            collection_id: UUID of the collection to delete.
            user_id: UUID of the user.

        Returns:
            True if deleted, False if not found.
        """
        collection = await self.get_collection(collection_id, user_id)

        if collection is None:
            return False

        await self.db.delete(collection)
        await self.db.commit()

        logger.info(f"Deleted knowledge collection {collection_id}")
        return True

    # ==================== Document Management ====================

    async def add_document(
        self,
        collection_id: UUID,
        user_id: UUID,
        filename: str,
        file_path: str,
        file_size: int
    ) -> Document:
        """Add a document to a collection.

        Args:
            collection_id: UUID of the collection.
            user_id: UUID of the user.
            filename: Name of the file.
            file_path: Path where the file is stored.
            file_size: Size of the file in bytes.

        Returns:
            Created Document object.

        Raises:
            ValueError: If collection not found or not owned by user.
        """
        # Verify collection exists and belongs to user
        collection = await self.get_collection(collection_id, user_id)
        if collection is None:
            raise ValueError(f"Collection {collection_id} not found")

        document = Document(
            collection_id=collection_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            status="pending"
        )

        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Added document {document.id} to collection {collection_id}")
        return document

    async def get_document(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: UUID of the document.
            user_id: UUID of the user.

        Returns:
            Document if found and owned by user, None otherwise.
        """
        # Join with collection to verify ownership
        result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .join(KnowledgeCollection)
            .where(
                Document.id == document_id,
                KnowledgeCollection.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        collection_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Document], int]:
        """List documents in a collection.

        Args:
            collection_id: UUID of the collection.
            user_id: UUID of the user.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            Tuple of (list of documents, total count).
        """
        # Verify collection ownership
        collection = await self.get_collection(collection_id, user_id)
        if collection is None:
            return [], 0

        # Get total count
        count_result = await self.db.execute(
            select(func.count(Document.id))
            .where(Document.collection_id == collection_id)
        )
        total = count_result.scalar() or 0

        # Get documents
        result = await self.db.execute(
            select(Document)
            .where(Document.collection_id == collection_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = list(result.scalars().all())

        return documents, total

    async def delete_document(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a document and its chunks.

        Args:
            document_id: UUID of the document to delete.
            user_id: UUID of the user.

        Returns:
            True if deleted, False if not found.
        """
        document = await self.get_document(document_id, user_id)

        if document is None:
            return False

        # Delete file from storage
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        await self.db.delete(document)
        await self.db.commit()

        logger.info(f"Deleted document {document_id}")
        return True

    # ==================== Document Processing ====================

    async def process_document(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> bool:
        """Process a document: extract text, chunk, and generate embeddings.

        Args:
            document_id: UUID of the document to process.
            user_id: UUID of the user.

        Returns:
            True if processed successfully, False otherwise.

        Raises:
            ValueError: If embedding service not configured.
        """
        if self.embedding_service is None:
            raise ValueError("Embedding service not configured")

        document = await self.get_document(document_id, user_id)
        if document is None:
            logger.error(f"Document {document_id} not found")
            return False

        try:
            # Update status to processing
            document.status = "processing"
            await self.db.commit()

            # Process the document
            processed = self.document_processor.process_file(
                document.file_path,
                metadata={'document_id': str(document_id)}
            )

            # Generate embeddings for each chunk
            chunk_texts = [chunk.content for chunk in processed.chunks]
            embeddings = await self.embedding_service.embed_batch(chunk_texts)

            # Create document chunks
            for i, chunk in enumerate(processed.chunks):
                # Convert embedding list to JSON string for storage
                embedding_json = json.dumps(embeddings[i])

                doc_chunk = DocumentChunk(
                    document_id=document_id,
                    content=chunk.content,
                    embedding=embedding_json,
                    chunk_metadata={
                        'index': chunk.index,
                        'start_char': chunk.start_char,
                        'end_char': chunk.end_char,
                    }
                )
                self.db.add(doc_chunk)

            # Update document status
            document.status = "completed"
            await self.db.commit()

            logger.info(
                f"Processed document {document_id}: "
                f"{len(processed.chunks)} chunks created"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {str(e)}")
            document.status = "failed"
            await self.db.commit()
            raise

    # ==================== Vector Search ====================

    async def search_knowledge(
        self,
        query: KnowledgeQuery,
        user_id: UUID
    ) -> List[SourceDocument]:
        """Search for relevant documents in a knowledge collection.

        Args:
            query: KnowledgeQuery with search parameters.
            user_id: UUID of the user.

        Returns:
            List of SourceDocument objects ordered by relevance.

        Raises:
            ValueError: If embedding service not configured.
        """
        if self.embedding_service is None:
            raise ValueError("Embedding service not configured")

        # Verify collection ownership
        collection = await self.get_collection(query.collection_id, user_id)
        if collection is None:
            raise ValueError(f"Collection {query.collection_id} not found")

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query.query)

        # Get all chunks in the collection
        result = await self.db.execute(
            select(DocumentChunk)
            .join(Document)
            .where(Document.collection_id == query.collection_id)
            .options(selectinload(DocumentChunk.document))
        )
        chunks = list(result.scalars().all())

        if not chunks:
            return []

        # Calculate similarity scores
        scored_chunks = []
        for chunk in chunks:
            if chunk.embedding:
                chunk_embedding = json.loads(chunk.embedding)
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                scored_chunks.append((chunk, similarity))

        # Sort by similarity (descending)
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Get top_k results
        top_results = scored_chunks[:query.top_k]

        # Format results
        sources = []
        for chunk, score in top_results:
            sources.append(SourceDocument(
                document_id=chunk.document_id,
                filename=chunk.document.filename,
                content=chunk.content,
                score=score,
                metadata=chunk.chunk_metadata
            ))

        logger.info(
            f"Found {len(sources)} results for query in collection {query.collection_id}"
        )
        return sources

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Cosine similarity score.
        """
        import math

        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def get_document_chunks(
        self,
        document_id: UUID
    ) -> List[DocumentChunk]:
        """Get all chunks for a document.

        Args:
            document_id: UUID of the document.

        Returns:
            List of DocumentChunk objects.
        """
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.created_at)
        )
        return list(result.scalars().all())