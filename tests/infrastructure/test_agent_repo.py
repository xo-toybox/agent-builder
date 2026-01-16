"""
Tests for SQLite agent repository.
"""
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    ToolSource,
    TriggerConfig,
    TriggerType,
)
from backend.infrastructure.persistence.sqlite.agent_repo import SQLiteAgentRepository
from backend.infrastructure.persistence.sqlite.database import Base


@pytest_asyncio.fixture
async def agent_repo():
    """Create an agent repository with in-memory database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        repo = SQLiteAgentRepository(session)
        yield repo

    await engine.dispose()


class TestAgentRepository:
    """Tests for agent repository operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_agent(self, agent_repo: SQLiteAgentRepository, sample_agent: AgentDefinition):
        """Test saving and retrieving an agent."""
        await agent_repo.save(sample_agent)

        retrieved = await agent_repo.get(sample_agent.id)

        assert retrieved is not None
        assert retrieved.id == sample_agent.id
        assert retrieved.name == sample_agent.name
        assert retrieved.description == sample_agent.description
        assert retrieved.system_prompt == sample_agent.system_prompt

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, agent_repo: SQLiteAgentRepository):
        """Test getting an agent that doesn't exist."""
        result = await agent_repo.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_agents(self, agent_repo: SQLiteAgentRepository):
        """Test listing all agents."""
        now = datetime.utcnow()

        agent1 = AgentDefinition(
            id="agent-1",
            name="Agent 1",
            description="First agent",
            system_prompt="Prompt 1",
            created_at=now,
            updated_at=now,
        )
        agent2 = AgentDefinition(
            id="agent-2",
            name="Agent 2",
            description="Second agent",
            system_prompt="Prompt 2",
            created_at=now,
            updated_at=now,
        )

        await agent_repo.save(agent1)
        await agent_repo.save(agent2)

        all_agents = await agent_repo.list_all()

        assert len(all_agents) == 2
        agent_ids = [a.id for a in all_agents]
        assert "agent-1" in agent_ids
        assert "agent-2" in agent_ids

    @pytest.mark.asyncio
    async def test_list_templates_only(self, agent_repo: SQLiteAgentRepository):
        """Test listing only templates."""
        now = datetime.utcnow()

        agent = AgentDefinition(
            id="agent-1",
            name="Regular Agent",
            description="Not a template",
            system_prompt="Prompt",
            is_template=False,
            created_at=now,
            updated_at=now,
        )
        template = AgentDefinition(
            id="template-1",
            name="Template",
            description="Is a template",
            system_prompt="Prompt",
            is_template=True,
            created_at=now,
            updated_at=now,
        )

        await agent_repo.save(agent)
        await agent_repo.save(template)

        templates = await agent_repo.list_all(is_template=True)

        assert len(templates) == 1
        assert templates[0].id == "template-1"
        assert templates[0].is_template is True

    @pytest.mark.asyncio
    async def test_list_non_templates_only(self, agent_repo: SQLiteAgentRepository):
        """Test listing only non-template agents."""
        now = datetime.utcnow()

        agent = AgentDefinition(
            id="agent-1",
            name="Regular Agent",
            description="Not a template",
            system_prompt="Prompt",
            is_template=False,
            created_at=now,
            updated_at=now,
        )
        template = AgentDefinition(
            id="template-1",
            name="Template",
            description="Is a template",
            system_prompt="Prompt",
            is_template=True,
            created_at=now,
            updated_at=now,
        )

        await agent_repo.save(agent)
        await agent_repo.save(template)

        agents = await agent_repo.list_all(is_template=False)

        assert len(agents) == 1
        assert agents[0].id == "agent-1"
        assert agents[0].is_template is False

    @pytest.mark.asyncio
    async def test_delete_agent(self, agent_repo: SQLiteAgentRepository, sample_agent: AgentDefinition):
        """Test deleting an agent."""
        await agent_repo.save(sample_agent)

        # Verify it exists
        retrieved = await agent_repo.get(sample_agent.id)
        assert retrieved is not None

        # Delete it
        await agent_repo.delete(sample_agent.id)

        # Verify it's gone
        retrieved = await agent_repo.get(sample_agent.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_clone_agent(self, agent_repo: SQLiteAgentRepository, sample_template: AgentDefinition):
        """Test cloning an agent."""
        await agent_repo.save(sample_template)

        # Clone the template
        new_id = await agent_repo.clone(sample_template.id, "Cloned Agent")

        # Get the cloned agent
        cloned = await agent_repo.get(new_id)

        assert cloned is not None
        assert cloned.id == new_id
        assert cloned.name == "Cloned Agent"
        assert cloned.is_template is False  # Clones should not be templates
        assert cloned.system_prompt == sample_template.system_prompt
        # Tools should be copied
        assert len(cloned.tools) == len(sample_template.tools)

    @pytest.mark.asyncio
    async def test_update_agent(self, agent_repo: SQLiteAgentRepository, sample_agent: AgentDefinition):
        """Test updating an existing agent."""
        await agent_repo.save(sample_agent)

        # Modify and save again
        sample_agent.name = "Updated Name"
        sample_agent.description = "Updated description"

        await agent_repo.save(sample_agent)

        # Retrieve and verify
        retrieved = await agent_repo.get(sample_agent.id)

        assert retrieved is not None
        assert retrieved.name == "Updated Name"
        assert retrieved.description == "Updated description"

    @pytest.mark.asyncio
    async def test_save_agent_with_tools(self, agent_repo: SQLiteAgentRepository):
        """Test saving an agent with tool configurations."""
        now = datetime.utcnow()

        tools = [
            ToolConfig(
                name="list_emails",
                source=ToolSource.BUILTIN,
                enabled=True,
                hitl_enabled=False,
            ),
            ToolConfig(
                name="custom_tool",
                source=ToolSource.MCP,
                enabled=True,
                hitl_enabled=True,
                server_id="my-server",
                server_config={"url": "http://localhost"},
            ),
        ]

        agent = AgentDefinition(
            id="agent-with-tools",
            name="Agent with Tools",
            description="Has tools",
            system_prompt="Prompt",
            tools=tools,
            created_at=now,
            updated_at=now,
        )

        await agent_repo.save(agent)
        retrieved = await agent_repo.get(agent.id)

        assert retrieved is not None
        assert len(retrieved.tools) == 2

        # Check first tool
        tool1 = next(t for t in retrieved.tools if t.name == "list_emails")
        assert tool1.source == ToolSource.BUILTIN
        assert tool1.hitl_enabled is False

        # Check second tool
        tool2 = next(t for t in retrieved.tools if t.name == "custom_tool")
        assert tool2.source == ToolSource.MCP
        assert tool2.server_id == "my-server"
        assert tool2.server_config == {"url": "http://localhost"}

    @pytest.mark.asyncio
    async def test_save_agent_with_triggers(self, agent_repo: SQLiteAgentRepository):
        """Test saving an agent with trigger configurations."""
        now = datetime.utcnow()

        triggers = [
            TriggerConfig(
                id="trigger-1",
                type=TriggerType.SCHEDULED,
                enabled=True,
                config={"cron": "0 9 * * *"},
            ),
            TriggerConfig(
                id="trigger-2",
                type=TriggerType.EMAIL_POLLING,
                enabled=False,
                config={"poll_interval": 60},
            ),
        ]

        agent = AgentDefinition(
            id="agent-with-triggers",
            name="Agent with Triggers",
            description="Has triggers",
            system_prompt="Prompt",
            triggers=triggers,
            created_at=now,
            updated_at=now,
        )

        await agent_repo.save(agent)
        retrieved = await agent_repo.get(agent.id)

        assert retrieved is not None
        assert len(retrieved.triggers) == 2

        # Check triggers
        scheduled = next(t for t in retrieved.triggers if t.type == TriggerType.SCHEDULED)
        assert scheduled.enabled is True
        assert scheduled.config["cron"] == "0 9 * * *"

        email = next(t for t in retrieved.triggers if t.type == TriggerType.EMAIL_POLLING)
        assert email.enabled is False
        assert email.config["poll_interval"] == 60
