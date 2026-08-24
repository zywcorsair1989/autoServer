"""Chat service for conversation and message management.

This module provides business logic for managing conversations
and messages in the RAG system.
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
    """Service class for chat operations.

    Handles conversation and message management.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the chat service with a database session.

        Args:
            db: AsyncSession for database operations.
        """
        self.db = db

    async def create_conversation(
        self,
        user_id: UUID,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation.

        Args:
            user_id: UUID of the user creating the conversation.
            conversation_data: ConversationCreate schema with conversation data.

        Returns:
            Created Conversation object.
        """
        conversation = Conversation(
            user_id=user_id,
            title=conversation_data.title
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[Conversation]:
        """Get a conversation by ID for a specific user.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the user.

        Returns:
            Conversation object if found, None otherwise.
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
        """List conversations for a user with pagination.

        Args:
            user_id: UUID of the user.
            skip: Number of conversations to skip.
            limit: Maximum number of conversations to return.

        Returns:
            Tuple of (list of conversations, total count).
        """
        # Get total count
        count_result = await self.db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Get conversations
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
        """Delete a conversation.

        Args:
            conversation_id: UUID of the conversation to delete.
            user_id: UUID of the user.

        Returns:
            True if deleted, False if not found.
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if conversation is None:
            return False

        await self.db.delete(conversation)
        await self.db.commit()

        logger.info(f"Deleted conversation {conversation_id}")
        return True

    async def add_message(
        self,
        conversation_id: UUID,
        message_data: MessageCreate
    ) -> Message:
        """Add a message to a conversation.

        Args:
            conversation_id: UUID of the conversation.
            message_data: MessageCreate schema with message data.

        Returns:
            Created Message object.

        Raises:
            ValueError: If conversation does not exist.
        """
        # Verify conversation exists
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")

        message = Message(
            conversation_id=conversation_id,
            role=message_data.role,
            content=message_data.content
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        logger.debug(
            f"Added {message.role} message to conversation {conversation_id}"
        )
        return message

    async def get_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """Get messages for a conversation with pagination.

        Args:
            conversation_id: UUID of the conversation.
            skip: Number of messages to skip.
            limit: Maximum number of messages to return.

        Returns:
            List of Message objects.
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
        """Update a conversation's title.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the user.
            title: New title for the conversation.

        Returns:
            Updated Conversation object if found, None otherwise.
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if conversation is None:
            return None

        conversation.title = title
        await self.db.commit()
        await self.db.refresh(conversation)

        logger.info(f"Updated title for conversation {conversation_id}")
        return conversation

    async def get_conversation_history(
        self,
        conversation_id: UUID
    ) -> List[dict]:
        """Get conversation history formatted for LLM.

        Args:
            conversation_id: UUID of the conversation.

        Returns:
            List of message dicts with 'role' and 'content'.
        """
        messages = await self.get_messages(conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]