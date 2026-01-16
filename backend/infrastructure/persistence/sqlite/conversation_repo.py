"""SQLite implementation of ConversationRepository."""

import uuid
import json
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.persistence.sqlite.models import ConversationMessageModel


class SQLiteConversationRepository:
    """SQLite implementation of the ConversationRepository port."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_message(
        self,
        thread_id: str,
        agent_id: str,
        message: dict
    ) -> None:
        """Save a message to a conversation thread."""
        # Extract content - handle both string and structured content
        content = message.get("content", "")
        if isinstance(content, dict) or isinstance(content, list):
            content = json.dumps(content)

        model = ConversationMessageModel(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            agent_id=agent_id,
            role=message.get("role", "user"),
            content=content,
            extra_data={
                k: v for k, v in message.items()
                if k not in ("role", "content")
            },
            created_at=datetime.utcnow(),
        )
        self.session.add(model)
        await self.session.commit()

    async def get_thread(self, thread_id: str) -> list[dict]:
        """Get all messages in a conversation thread."""
        stmt = (
            select(ConversationMessageModel)
            .where(ConversationMessageModel.thread_id == thread_id)
            .order_by(ConversationMessageModel.created_at)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        messages = []
        for m in models:
            msg = {
                "role": m.role,
                "content": m.content,
            }
            # Try to parse content as JSON if it looks like JSON
            if m.content.startswith("{") or m.content.startswith("["):
                try:
                    msg["content"] = json.loads(m.content)
                except json.JSONDecodeError:
                    pass
            # Add any extra_data
            if m.extra_data:
                msg.update(m.extra_data)
            messages.append(msg)

        return messages

    async def list_threads(self, agent_id: str) -> list[str]:
        """List all thread IDs for an agent."""
        stmt = (
            select(ConversationMessageModel.thread_id)
            .where(ConversationMessageModel.agent_id == agent_id)
            .distinct()
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def delete_thread(self, thread_id: str) -> None:
        """Delete a conversation thread and all its messages."""
        stmt = delete(ConversationMessageModel).where(
            ConversationMessageModel.thread_id == thread_id
        )
        await self.session.execute(stmt)
        await self.session.commit()
