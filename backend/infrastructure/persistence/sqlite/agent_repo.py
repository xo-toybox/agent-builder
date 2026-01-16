"""SQLite implementation of AgentRepository."""

import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    SubagentConfig,
    TriggerConfig,
    ToolSource,
    TriggerType,
)
from backend.infrastructure.persistence.sqlite.models import (
    AgentModel,
    AgentToolModel,
    AgentSubagentModel,
    AgentTriggerModel,
)


class SQLiteAgentRepository:
    """SQLite implementation of the AgentRepository port."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, agent: AgentDefinition) -> None:
        """Save or update an agent definition."""
        # Check if agent exists - use selectinload to eagerly load relationships
        stmt = (
            select(AgentModel)
            .where(AgentModel.id == agent.id)
            .options(
                selectinload(AgentModel.tools),
                selectinload(AgentModel.subagents),
                selectinload(AgentModel.triggers),
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing agent
            existing.name = agent.name
            existing.description = agent.description
            existing.system_prompt = agent.system_prompt
            existing.model = agent.model
            existing.updated_at = datetime.utcnow()
            existing.is_template = agent.is_template

            # Delete existing related records
            for tool in existing.tools:
                await self.session.delete(tool)
            for subagent in existing.subagents:
                await self.session.delete(subagent)
            for trigger in existing.triggers:
                await self.session.delete(trigger)

            await self.session.flush()
            model = existing
        else:
            # Create new agent
            model = AgentModel(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                system_prompt=agent.system_prompt,
                model=agent.model,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
                is_template=agent.is_template,
            )
            self.session.add(model)

        # Add tools
        for tool in agent.tools:
            tool_model = AgentToolModel(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                name=tool.name,
                source=tool.source.value,
                enabled=tool.enabled,
                hitl_enabled=tool.hitl_enabled,
                server_id=tool.server_id,
                server_config=tool.server_config,
            )
            self.session.add(tool_model)

        # Add subagents
        for subagent in agent.subagents:
            subagent_model = AgentSubagentModel(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                name=subagent.name,
                description=subagent.description,
                system_prompt=subagent.system_prompt,
                tools=subagent.tools,
            )
            self.session.add(subagent_model)

        # Add triggers
        for trigger in agent.triggers:
            trigger_model = AgentTriggerModel(
                id=trigger.id,
                agent_id=agent.id,
                type=trigger.type.value,
                enabled=trigger.enabled,
                config=trigger.config,
            )
            self.session.add(trigger_model)

        await self.session.commit()

    async def get(self, id: str) -> AgentDefinition | None:
        """Get an agent by ID."""
        stmt = (
            select(AgentModel)
            .where(AgentModel.id == id)
            .options(
                selectinload(AgentModel.tools),
                selectinload(AgentModel.subagents),
                selectinload(AgentModel.triggers),
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_entity(model)

    async def list_all(self, is_template: bool | None = None) -> list[AgentDefinition]:
        """List all agents, optionally filtered by template status."""
        stmt = select(AgentModel).options(
            selectinload(AgentModel.tools),
            selectinload(AgentModel.subagents),
            selectinload(AgentModel.triggers),
        )

        if is_template is not None:
            stmt = stmt.where(AgentModel.is_template == is_template)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(m) for m in models]

    async def delete(self, id: str) -> None:
        """Delete an agent by ID."""
        model = await self.session.get(AgentModel, id)
        if model:
            await self.session.delete(model)
            await self.session.commit()

    async def clone(self, id: str, new_name: str) -> str:
        """Clone an agent with a new name."""
        agent = await self.get(id)
        if not agent:
            raise ValueError(f"Agent not found: {id}")

        new_id = str(uuid.uuid4())
        now = datetime.utcnow()

        cloned = AgentDefinition(
            id=new_id,
            name=new_name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            model=agent.model,
            tools=agent.tools,
            subagents=agent.subagents,
            triggers=[
                TriggerConfig(
                    id=str(uuid.uuid4()),
                    type=t.type,
                    enabled=False,  # Disable triggers on clone
                    config=t.config,
                )
                for t in agent.triggers
            ],
            created_at=now,
            updated_at=now,
            is_template=False,  # Clones are not templates
        )

        await self.save(cloned)
        return new_id

    def _model_to_entity(self, model: AgentModel) -> AgentDefinition:
        """Convert SQLAlchemy model to domain entity."""
        return AgentDefinition(
            id=model.id,
            name=model.name,
            description=model.description or "",
            system_prompt=model.system_prompt,
            model=model.model,
            tools=[
                ToolConfig(
                    name=t.name,
                    source=ToolSource(t.source),
                    enabled=t.enabled,
                    hitl_enabled=t.hitl_enabled,
                    server_id=t.server_id,
                    server_config=t.server_config or {},
                )
                for t in model.tools
            ],
            subagents=[
                SubagentConfig(
                    name=s.name,
                    description=s.description,
                    system_prompt=s.system_prompt,
                    tools=s.tools,
                )
                for s in model.subagents
            ],
            triggers=[
                TriggerConfig(
                    id=t.id,
                    type=TriggerType(t.type),
                    enabled=t.enabled,
                    config=t.config or {},
                )
                for t in model.triggers
            ],
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_template=model.is_template,
        )
