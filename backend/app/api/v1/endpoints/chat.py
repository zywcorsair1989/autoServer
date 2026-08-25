"""聊天 API 端点。

这个模块提供聊天操作的 REST API 端点，
包括对话管理和流式聊天。
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


def _make_title(message: str, max_len: int = 50) -> str:
    """从用户消息生成对话标题（压缩空白，超长截断）。"""
    text = " ".join(message.split())
    if not text:
        return "新对话"
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新对话",
    description="为当前用户创建新对话。"
)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """创建新对话。

    Args:
        conversation_data: 对话创建数据。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        创建的对话。
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
    summary="列出对话",
    description="列出当前用户的所有对话。"
)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationList:
    """列出当前用户的对话。

    Args:
        skip: 要跳过的对话数量。
        limit: 要返回的最大对话数量。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        带有总数的对话列表。
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
    summary="获取对话",
    description="获取特定对话及其消息。"
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationDetail:
    """通过 ID 获取对话。

    Args:
        conversation_id: 对话的 UUID。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        带有消息的对话。

    Raises:
        HTTPException: 如果对话未找到。
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
    summary="删除对话",
    description="删除对话及其所有消息。"
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """删除对话。

    Args:
        conversation_id: 要删除的对话的 UUID。
        current_user: 当前认证用户。
        db: 数据库会话。

    Raises:
        HTTPException: 如果对话未找到。
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
    summary="发送聊天消息",
    description="发送消息并获取响应。可以使用 RAG 获取基于知识的答案。"
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """发送聊天消息并获取响应。

    Args:
        request: 带有消息和选项的聊天请求。
        current_user: 当前认证用户。
        db: 数据库会话。

    Returns:
        带有消息和可选源的聊天响应。

    Raises:
        HTTPException: 如果对话未找到或其他错误。
    """
    chat_service = ChatService(db)

    # 处理对话
    conversation_id = request.conversation_id
    if conversation_id is None:
        # 创建新对话
        from app.schemas.chat import ConversationCreate
        conversation = await chat_service.create_conversation(
            current_user.id,
            ConversationCreate(title=_make_title(request.message))
        )
        conversation_id = conversation.id
    else:
        # 验证对话是否存在
        conversation = await chat_service.get_conversation(
            conversation_id,
            current_user.id
        )
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"对话 {conversation_id} 未找到"
            )

        # 标题仍为默认值时，用首条消息生成话题标题
        if conversation.title == "新对话":
            await chat_service.update_conversation_title(
                conversation_id,
                current_user.id,
                _make_title(request.message)
            )

    # 保存用户消息
    from app.schemas.chat import MessageCreate
    user_message = await chat_service.add_message(
        conversation_id,
        MessageCreate(role="user", content=request.message)
    )

    # 获取响应
    sources = None
    if request.use_knowledge and request.collection_id:
        # 使用 RAG
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
            logger.error(f"RAG 查询失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="处理查询失败"
            )
    else:
        # 直接 LLM 调用
        try:
            llm_service = LLMService()
            history = await chat_service.get_conversation_history(conversation_id)

            # 如果使用对话则添加系统消息
            messages = history if history else []
            if not any(msg["role"] == "system" for msg in messages):
                messages.insert(0, {
                    "role": "system",
                    "content": "你是一个专业的AI助手。"
                })

            response_text = await llm_service.generate(messages)
        except Exception as e:
            logger.error(f"LLM 生成失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="生成回复失败"
            )

    # 保存助手消息
    assistant_message = await chat_service.add_message(
        conversation_id,
        MessageCreate(role="assistant", content=response_text, sources=sources)
    )

    return ChatResponse(
        message=assistant_message,
        sources=sources
    )


@router.post(
    "/stream",
    summary="流式聊天响应",
    description="发送消息并获取流式响应。"
)
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """流式聊天响应。

    Args:
        request: 带有消息和选项的聊天请求。
        current_user: 当前认证用户。
        db: 数据库会话。

    Yields:
        来自响应流的文本块。

    Raises:
        HTTPException: 如果对话未找到或其他错误。
    """
    import json
    from fastapi.responses import StreamingResponse

    chat_service = ChatService(db)

    # 处理对话
    conversation_id = request.conversation_id
    if conversation_id is None:
        from app.schemas.chat import ConversationCreate
        conversation = await chat_service.create_conversation(
            current_user.id,
            ConversationCreate(title=_make_title(request.message))
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

        # 标题仍为默认值时，用首条消息生成话题标题
        if conversation.title == "新对话":
            await chat_service.update_conversation_title(
                conversation_id,
                current_user.id,
                _make_title(request.message)
            )

    # 保存用户消息
    from app.schemas.chat import MessageCreate
    await chat_service.add_message(
        conversation_id,
        MessageCreate(role="user", content=request.message)
    )

    async def generate_stream():
        """生成流式响应。"""
        try:
            llm_service = LLMService()
            history = await chat_service.get_conversation_history(conversation_id)

            messages = history if history else []
            if not any(msg["role"] == "system" for msg in messages):
                messages.insert(0, {
                    "role": "system",
                    "content": "你是一个专业的AI助手。"
                })

            full_response = ""
            async for chunk in llm_service.stream_generate(messages):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # 保存完整响应
            await chat_service.add_message(
                conversation_id,
                MessageCreate(role="assistant", content=full_response)
            )

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"流式传输失败: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )