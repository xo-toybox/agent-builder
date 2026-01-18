"""Repository for persisting builder wizard conversations.

v0.0.3: Enables wizard state to survive server restarts.
        Uses plain dicts instead of LangChain message types.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.persistence.sqlite.models import WizardConversationModel


# Message type alias
Message = dict[str, Any]


class WizardConversationRepository:
    """Repository for wizard conversation persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def save_message(self, thread_id: str, message: Message) -> str:
        """Save a message to the conversation.

        Args:
            thread_id: Conversation thread ID
            message: Message dict with role, content, and optional tool_calls/tool_call_id

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        role = message.get("role", "user")
        content = message.get("content", "")

        if isinstance(content, (dict, list)):
            content = json.dumps(content)

        tool_calls = message.get("tool_calls")
        tool_call_id = message.get("tool_call_id")

        model = WizardConversationModel(
            id=message_id,
            thread_id=thread_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            created_at=datetime.utcnow(),
        )
        self.session.add(model)
        await self.session.commit()
        return message_id

    async def load_conversation(self, thread_id: str) -> list[Message]:
        """Load all messages for a conversation thread.

        Args:
            thread_id: Conversation thread ID

        Returns:
            List of message dicts in order
        """
        result = await self.session.execute(
            select(WizardConversationModel)
            .where(WizardConversationModel.thread_id == thread_id)
            .order_by(WizardConversationModel.created_at)
        )
        rows = result.scalars().all()

        messages: list[Message] = []
        for row in rows:
            msg: Message = {
                "role": row.role,
                "content": row.content,
            }
            if row.tool_calls:
                msg["tool_calls"] = row.tool_calls
            if row.tool_call_id:
                msg["tool_call_id"] = row.tool_call_id
            messages.append(msg)

        return messages

    async def clear_conversation(self, thread_id: str) -> None:
        """Clear all messages for a conversation thread.

        Args:
            thread_id: Conversation thread ID
        """
        await self.session.execute(
            delete(WizardConversationModel).where(WizardConversationModel.thread_id == thread_id)
        )
        await self.session.commit()

    async def exists(self, thread_id: str) -> bool:
        """Check if a conversation exists.

        Args:
            thread_id: Conversation thread ID

        Returns:
            True if conversation has messages
        """
        result = await self.session.execute(
            select(WizardConversationModel.id)
            .where(WizardConversationModel.thread_id == thread_id)
            .limit(1)
        )
        return result.scalar() is not None
