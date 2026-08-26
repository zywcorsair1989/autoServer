"""聊天服务用于对话和消息管理。

这个模块提供管理对话和消息的业务逻辑。
"""

from typing import List, Optional
from uuid import UUID
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message
from app.schemas.chat import ConversationCreate, MessageCreate

logger = logging.getLogger(__name__)


class ChatService:
    """聊天操作的服务类。

    处理对话和消息管理。
    """

    def __init__(self, db: AsyncSession):
        """使用数据库会话初始化聊天服务。

        Args:
            db: 用于数据库操作的 AsyncSession。
        """
        self.db = db

    async def create_conversation(
        self,
        user_id: UUID,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """创建新对话。

        Args:
            user_id: 创建对话的用户 UUID。
            conversation_data: 包含对话数据的 ConversationCreate schema。

        Returns:
            创建的 Conversation 对象。
        """
        conversation = Conversation(
            user_id=user_id,
            title=conversation_data.title
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        logger.info(f"为用户 {user_id} 创建了对话 {conversation.id}")
        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[Conversation]:
        """为特定用户获取对话。

        Args:
            conversation_id: 对话的 UUID。
            user_id: 用户的 UUID。

        Returns:
            如果找到返回 Conversation 对象，否则返回 None。
        """
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Conversation], int]:
        """列出用户的对话并分页。

        Args:
            user_id: 用户的 UUID。
            skip: 要跳过的对话数量。
            limit: 要返回的最大对话数量。

        Returns:
            (对话列表, 总数) 的元组。
        """
        # 获取总数
        count_result = await self.db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # 获取对话
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        conversations = list(result.scalars().all())

        return conversations, total

    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        """删除对话。

        Args:
            conversation_id: 要删除的对话的 UUID。
            user_id: 用户的 UUID。

        Returns:
            如果删除返回 True，如果没有找到返回 False。
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if conversation is None:
            return False

        await self.db.delete(conversation)
        await self.db.commit()

        logger.info(f"删除了对话 {conversation_id}")
        return True

    async def add_message(
        self,
        conversation_id: UUID,
        message_data: MessageCreate
    ) -> Message:
        """向对话添加消息。

        Args:
            conversation_id: 对话的 UUID。
            message_data: 包含消息数据的 MessageCreate schema。

        Returns:
            创建的 Message 对象。

        Raises:
            ValueError: 如果对话不存在。
        """
        # 验证对话是否存在
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"对话 {conversation_id} 未找到")

        # 将 Pydantic SourceDocument 序列化为可存入 JSONB 的字典列表
        # mode="json" 将 UUID 等类型转为字符串，否则 json.dumps 报
        # "Object of type UUID is not JSON serializable"
        sources = (
            [s.model_dump(mode="json") for s in message_data.sources]
            if message_data.sources
            else None
        )

        message = Message(
            conversation_id=conversation_id,
            role=message_data.role,
            content=message_data.content,
            sources=sources
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        logger.debug(
            f"向对话 {conversation_id} 添加了 {message.role} 消息"
        )
        return message

    async def get_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """获取对话的消息并分页。

        Args:
            conversation_id: 对话的 UUID。
            skip: 要跳过的消息数量。
            limit: 要返回的最大消息数量。

        Returns:
            Message 对象列表。
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_conversation_title(
        self,
        conversation_id: UUID,
        user_id: UUID,
        title: str
    ) -> Optional[Conversation]:
        """更新对话标题。

        Args:
            conversation_id: 对话的 UUID。
            user_id: 用户的 UUID。
            title: 对话的新标题。

        Returns:
            如果找到返回更新的 Conversation 对象，否则返回 None。
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if conversation is None:
            return None

        conversation.title = title
        await self.db.commit()
        await self.db.refresh(conversation)

        logger.info(f"更新了对话 {conversation_id} 的标题")
        return conversation

    async def get_conversation_history(
        self,
        conversation_id: UUID
    ) -> List[dict]:
        """获取为 LLM 格式的对话历史。

        Args:
            conversation_id: 对话的 UUID。

        Returns:
            具有 'role' 和 'content' 的消息字典列表。
        """
        messages = await self.get_messages(conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]