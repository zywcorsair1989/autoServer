"""Chat API endpoints.

This module provides REST API endpoints for chat operations,
including conversation management and streaming chat.
"""

from typing import Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetail,
    ConversationList,
    ChatRequest,
    ChatResponse,
    MessageResponse,
)
from app.services.chat_service import ChatService
from app.services.rag_service import RAGService
from app.ai.llm_service import LLMService
from app.ai.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Create a new conversation for the current user."
)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """Create a new conversation.

    Args:
        conversation_data: Conversation creation data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Created conversation.
    """
    service = ChatService(db)
    conversation = await service.create_conversation(
        current_user.id,
        conversation_data
    )
    return conversation


@router.get(
    "/conversations",
    response_model=ConversationList,
    summary="List conversations",
    description="List all conversations for the current user."
)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationList:
    """List conversations for the current user.

    Args:
        skip: Number of conversations to skip.
        limit: Maximum number of conversations to return.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        List of conversations with total count.
    """
    service = ChatService(db)
    conversations, total = await service.list_conversations(
        current_user.id,
        skip=skip,
        limit=limit
    )
    return ConversationList(
        conversations=conversations,
        total=total
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation",
    description="Get a specific conversation with its messages."
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationDetail:
    """Get a conversation by ID.

    Args:
        conversation_id: UUID of the conversation.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Conversation with messages.

    Raises:
        HTTPException: If conversation not found.
    """
    service = ChatService(db)
    conversation = await service.get_conversation(conversation_id, current_user.id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 未找到"
        )

    return conversation


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation and all its messages."
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a conversation.

    Args:
        conversation_id: UUID of the conversation to delete.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException: If conversation not found.
    """
    service = ChatService(db)
    deleted = await service.delete_conversation(conversation_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 未找到"
        )


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="Send a message and get a response. Can use RAG for knowledge-based answers."
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """Send a chat message and get a response.

    Args:
        request: Chat request with message and options.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Chat response with message and optional sources.

    Raises:
        HTTPException: If conversation not found or other error.
    """
    chat_service = ChatService(db)

    # Handle conversation
    conversation_id = request.conversation_id
    if conversation_id is None:
        # Create new conversation
        from app.schemas.chat import ConversationCreate
        conversation = await chat_service.create_conversation(
            current_user.id,
            ConversationCreate(title=request.message[:50] + "...")
        )
        conversation_id = conversation.id
    else:
        # Verify conversation exists
        conversation = await chat_service.get_conversation(
            conversation_id,
            current_user.id
        )
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"对话 {conversation_id} 未找到"
            )

    # Save user message
    from app.schemas.chat import MessageCreate
    user_message = await chat_service.add_message(
        conversation_id,
        MessageCreate(role="user", content=request.message)
    )

    # Get response
    sources = None
    if request.use_knowledge and request.collection_id:
        # Use RAG
        try:
            embedding_service = EmbeddingService()
            llm_service = LLMService()
            rag_service = RAGService(
                db=db,
                llm_service=llm_service,
                embedding_service=embedding_service
            )

            response_text, sources = await rag_service.query(
                query=request.message,
                collection_id=request.collection_id,
                user_id=current_user.id
            )
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="处理查询失败"
            )
    else:
        # Direct LLM call
        try:
            llm_service = LLMService()
            history = await chat_service.get_conversation_history(conversation_id)

            # Add system message if using conversation
            messages = history if history else []
            if not any(msg["role"] == "system" for msg in messages):
                messages.insert(0, {
                    "role": "system",
                    "content": "You are a helpful AI assistant."
                })

            response_text = await llm_service.generate(messages)
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="生成回复失败"
            )

    # Save assistant message
    assistant_message = await chat_service.add_message(
        conversation_id,
        MessageCreate(role="assistant", content=response_text)
    )

    return ChatResponse(
        message=assistant_message,
        sources=sources
    )


@router.post(
    "/stream",
    summary="Stream chat response",
    description="Send a message and get a streaming response."
)
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Stream a chat response.

    Args:
        request: Chat request with message and options.
        current_user: Current authenticated user.
        db: Database session.

    Yields:
        Text chunks from the response stream.

    Raises:
        HTTPException: If conversation not found or other error.
    """
    import json
    from fastapi.responses import StreamingResponse

    chat_service = ChatService(db)

    # Handle conversation
    conversation_id = request.conversation_id
    if conversation_id is None:
        from app.schemas.chat import ConversationCreate
        conversation = await chat_service.create_conversation(
            current_user.id,
            ConversationCreate(title=request.message[:50] + "...")
        )
        conversation_id = conversation.id
    else:
        conversation = await chat_service.get_conversation(
            conversation_id,
            current_user.id
        )
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"对话 {conversation_id} 未找到"
            )

    # Save user message
    from app.schemas.chat import MessageCreate
    await chat_service.add_message(
        conversation_id,
        MessageCreate(role="user", content=request.message)
    )

    async def generate_stream():
        """Generate streaming response."""
        try:
            llm_service = LLMService()
            history = await chat_service.get_conversation_history(conversation_id)

            messages = history if history else []
            if not any(msg["role"] == "system" for msg in messages):
                messages.insert(0, {
                    "role": "system",
                    "content": "You are a helpful AI assistant."
                })

            full_response = ""
            async for chunk in llm_service.stream_generate(messages):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # Save complete response
            await chat_service.add_message(
                conversation_id,
                MessageCreate(role="assistant", content=full_response)
            )

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Streaming failed: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )