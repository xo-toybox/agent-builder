"""Repository for agent memory files and edit requests."""

import uuid
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.persistence.sqlite.models import (
    MemoryFileModel,
    MemoryEditRequestModel,
)


class MemoryRepository:
    """Repository for memory files stored in SQLite."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get(self, agent_id: str, path: str) -> dict | None:
        """Get a memory file by agent ID and path.

        Args:
            agent_id: Agent ID
            path: Virtual file path

        Returns:
            Memory file dict or None if not found
        """
        result = await self.session.execute(
            select(MemoryFileModel).where(
                MemoryFileModel.agent_id == agent_id,
                MemoryFileModel.path == path,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        return {
            "id": model.id,
            "agent_id": model.agent_id,
            "path": model.path,
            "content": model.content,
            "content_type": model.content_type,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def list_files(self, agent_id: str, directory: str = "knowledge") -> list[str]:
        """List memory files in a directory.

        Args:
            agent_id: Agent ID
            directory: Directory prefix to filter by

        Returns:
            List of file paths
        """
        result = await self.session.execute(
            select(MemoryFileModel.path).where(
                MemoryFileModel.agent_id == agent_id,
                MemoryFileModel.path.startswith(f"{directory}/"),
            )
        )
        return [row[0] for row in result.all()]

    async def save(
        self,
        agent_id: str,
        path: str,
        content: str,
        previous_content: str | None = None,
    ) -> dict:
        """Save or update a memory file.

        Args:
            agent_id: Agent ID
            path: Virtual file path
            content: File content
            previous_content: Previous content for undo support

        Returns:
            Saved memory file dict
        """
        # Check if file exists
        existing = await self.get(agent_id, path)

        if existing:
            # Update existing file
            result = await self.session.execute(
                select(MemoryFileModel).where(MemoryFileModel.id == existing["id"])
            )
            model = result.scalar_one()
            model.content = content
            model.updated_at = datetime.utcnow()
        else:
            # Create new file
            model = MemoryFileModel(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                path=path,
                content=content,
                content_type="text/markdown",
            )
            self.session.add(model)

        await self.session.commit()
        await self.session.refresh(model)

        return {
            "id": model.id,
            "agent_id": model.agent_id,
            "path": model.path,
            "content": model.content,
            "content_type": model.content_type,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def delete_file(self, agent_id: str, path: str) -> bool:
        """Delete a memory file.

        Args:
            agent_id: Agent ID
            path: Virtual file path

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(MemoryFileModel).where(
                MemoryFileModel.agent_id == agent_id,
                MemoryFileModel.path == path,
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def get_total_size(self, agent_id: str) -> int:
        """Get total size of all memory files for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Total size in bytes
        """
        result = await self.session.execute(
            select(MemoryFileModel.content).where(
                MemoryFileModel.agent_id == agent_id,
            )
        )
        total = sum(len(row[0].encode("utf-8")) for row in result.all())
        return total


class MemoryEditRequestRepository:
    """Repository for memory edit requests (HITL approval)."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        agent_id: str,
        path: str,
        operation: str,
        proposed_content: str,
        previous_content: str | None,
        reason: str,
    ) -> dict:
        """Create a new memory edit request.

        Args:
            agent_id: Agent ID
            path: Virtual file path
            operation: Operation type (write, append, delete)
            proposed_content: Proposed new content
            previous_content: Current content for undo
            reason: Reason for the change

        Returns:
            Created edit request dict
        """
        model = MemoryEditRequestModel(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            path=path,
            operation=operation,
            proposed_content=proposed_content,
            previous_content=previous_content,
            reason=reason,
            status="pending",
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

        return {
            "id": model.id,
            "agent_id": model.agent_id,
            "path": model.path,
            "operation": model.operation,
            "proposed_content": model.proposed_content,
            "previous_content": model.previous_content,
            "reason": model.reason,
            "status": model.status,
            "created_at": model.created_at,
        }

    async def get(self, request_id: str) -> dict | None:
        """Get a memory edit request by ID.

        Args:
            request_id: Request ID

        Returns:
            Edit request dict or None
        """
        result = await self.session.execute(
            select(MemoryEditRequestModel).where(
                MemoryEditRequestModel.id == request_id,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        return {
            "id": model.id,
            "agent_id": model.agent_id,
            "path": model.path,
            "operation": model.operation,
            "proposed_content": model.proposed_content,
            "previous_content": model.previous_content,
            "reason": model.reason,
            "status": model.status,
            "created_at": model.created_at,
            "resolved_at": model.resolved_at,
        }

    async def get_pending(self, agent_id: str) -> list[dict]:
        """Get all pending edit requests for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of pending edit request dicts
        """
        result = await self.session.execute(
            select(MemoryEditRequestModel).where(
                MemoryEditRequestModel.agent_id == agent_id,
                MemoryEditRequestModel.status == "pending",
            )
        )
        return [
            {
                "id": model.id,
                "agent_id": model.agent_id,
                "path": model.path,
                "operation": model.operation,
                "proposed_content": model.proposed_content,
                "previous_content": model.previous_content,
                "reason": model.reason,
                "status": model.status,
                "created_at": model.created_at,
            }
            for model in result.scalars().all()
        ]

    async def resolve(
        self,
        request_id: str,
        status: str,
        edited_content: str | None = None,
    ) -> dict | None:
        """Resolve a memory edit request.

        Args:
            request_id: Request ID
            status: New status (approved, rejected)
            edited_content: Edited content if user modified it

        Returns:
            Updated edit request dict or None
        """
        result = await self.session.execute(
            select(MemoryEditRequestModel).where(
                MemoryEditRequestModel.id == request_id,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        model.status = status
        model.resolved_at = datetime.utcnow()
        if edited_content is not None:
            model.proposed_content = edited_content

        await self.session.commit()
        await self.session.refresh(model)

        return {
            "id": model.id,
            "agent_id": model.agent_id,
            "path": model.path,
            "operation": model.operation,
            "proposed_content": model.proposed_content,
            "previous_content": model.previous_content,
            "reason": model.reason,
            "status": model.status,
            "created_at": model.created_at,
            "resolved_at": model.resolved_at,
        }

    async def get_last_approved(self, agent_id: str, path: str) -> dict | None:
        """Get the last approved edit request for undo support.

        Args:
            agent_id: Agent ID
            path: Virtual file path

        Returns:
            Last approved edit request or None
        """
        result = await self.session.execute(
            select(MemoryEditRequestModel)
            .where(
                MemoryEditRequestModel.agent_id == agent_id,
                MemoryEditRequestModel.path == path,
                MemoryEditRequestModel.status == "approved",
            )
            .order_by(MemoryEditRequestModel.resolved_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        return {
            "id": model.id,
            "agent_id": model.agent_id,
            "path": model.path,
            "operation": model.operation,
            "proposed_content": model.proposed_content,
            "previous_content": model.previous_content,
            "reason": model.reason,
            "status": model.status,
            "created_at": model.created_at,
            "resolved_at": model.resolved_at,
        }
