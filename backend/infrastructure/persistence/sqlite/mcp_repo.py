"""SQLite implementation of MCPRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities import MCPServerConfig
from backend.infrastructure.persistence.sqlite.models import MCPServerModel


class SQLiteMCPRepository:
    """SQLite implementation of the MCPRepository port."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, server: MCPServerConfig) -> None:
        """Save or update an MCP server configuration."""
        existing = await self.session.get(MCPServerModel, server.id)

        if existing:
            existing.name = server.name
            existing.command = server.command
            existing.args = server.args
            existing.env = server.env
            existing.enabled = server.enabled
        else:
            model = MCPServerModel(
                id=server.id,
                name=server.name,
                command=server.command,
                args=server.args,
                env=server.env,
                enabled=server.enabled,
            )
            self.session.add(model)

        await self.session.commit()

    async def get(self, id: str) -> MCPServerConfig | None:
        """Get an MCP server config by ID."""
        model = await self.session.get(MCPServerModel, id)

        if not model:
            return None

        return self._model_to_entity(model)

    async def list_all(self) -> list[MCPServerConfig]:
        """List all MCP server configurations."""
        stmt = select(MCPServerModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(m) for m in models]

    async def delete(self, id: str) -> None:
        """Delete an MCP server configuration by ID."""
        model = await self.session.get(MCPServerModel, id)
        if model:
            await self.session.delete(model)
            await self.session.commit()

    def _model_to_entity(self, model: MCPServerModel) -> MCPServerConfig:
        """Convert SQLAlchemy model to domain entity."""
        return MCPServerConfig(
            id=model.id,
            name=model.name,
            command=model.command,
            args=model.args or [],
            env=model.env or {},
            enabled=model.enabled,
        )
