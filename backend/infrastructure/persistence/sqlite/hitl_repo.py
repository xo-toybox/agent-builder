"""SQLite implementation of HITLRepository."""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities import HITLRequest, HITLDecision
from backend.infrastructure.persistence.sqlite.models import HITLRequestModel


class SQLiteHITLRepository:
    """SQLite implementation of the HITLRepository port."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, request: HITLRequest) -> None:
        """Save a new HITL request."""
        model = HITLRequestModel(
            id=request.id,
            thread_id=request.thread_id,
            agent_id=request.agent_id,
            tool_call_id=request.tool_call_id,
            tool_name=request.tool_name,
            tool_args=request.tool_args,
            status=request.status,
            decision=request.decision.value if request.decision else None,
            edited_args=request.edited_args,
            created_at=request.created_at,
            resolved_at=request.resolved_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def get(self, id: str) -> HITLRequest | None:
        """Get a HITL request by ID."""
        model = await self.session.get(HITLRequestModel, id)

        if not model:
            return None

        return self._model_to_entity(model)

    async def get_by_tool_call(self, tool_call_id: str) -> HITLRequest | None:
        """Get a HITL request by tool call ID."""
        stmt = select(HITLRequestModel).where(
            HITLRequestModel.tool_call_id == tool_call_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_entity(model)

    async def list_pending(self, agent_id: str) -> list[HITLRequest]:
        """List all pending HITL requests for an agent."""
        stmt = select(HITLRequestModel).where(
            HITLRequestModel.agent_id == agent_id,
            HITLRequestModel.status == "pending",
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(m) for m in models]

    async def update_status(
        self,
        id: str,
        decision: str,
        edited_args: dict | None = None
    ) -> None:
        """Update the status/decision of a HITL request."""
        model = await self.session.get(HITLRequestModel, id)

        if model:
            model.decision = decision
            model.status = decision if decision in ("approved", "rejected") else "edited"
            model.edited_args = edited_args
            model.resolved_at = datetime.utcnow()
            await self.session.commit()

    def _model_to_entity(self, model: HITLRequestModel) -> HITLRequest:
        """Convert SQLAlchemy model to domain entity."""
        return HITLRequest(
            id=model.id,
            thread_id=model.thread_id,
            agent_id=model.agent_id,
            tool_call_id=model.tool_call_id,
            tool_name=model.tool_name,
            tool_args=model.tool_args,
            status=model.status,
            decision=HITLDecision(model.decision) if model.decision else None,
            edited_args=model.edited_args,
            created_at=model.created_at,
            resolved_at=model.resolved_at,
        )
