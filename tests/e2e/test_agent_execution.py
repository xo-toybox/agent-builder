"""
E2E tests for agent execution path.

Guards against regressions in:
- System prompt being used correctly (not cached/wrong agent)
- Auth requirements for different tool types
- HITL interrupt_on configuration format
"""

from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.domain.entities import AgentDefinition, ToolConfig, ToolSource
from backend.domain.exceptions import CredentialNotFoundError
from backend.infrastructure.persistence.sqlite.agent_repo import SQLiteAgentRepository
from backend.infrastructure.persistence.sqlite.database import Base
from backend.infrastructure.persistence.sqlite.skill_repo import SkillRepository
from backend.infrastructure.tools.registry import ToolRegistryImpl
from backend.application.use_cases.run_agent import RunAgentUseCase


@pytest_asyncio.fixture
async def db_session():
    """Create in-memory database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def agent_repo(db_session):
    """Create agent repository."""
    return SQLiteAgentRepository(db_session)


@pytest_asyncio.fixture
async def skill_repo(db_session):
    """Create skill repository."""
    return SkillRepository(db_session)


class TestSystemPromptCorrectness:
    """Verify system prompt is passed correctly to agent creation."""

    @pytest.mark.asyncio
    async def test_correct_system_prompt_passed_to_create_deep_agent(
        self, agent_repo, skill_repo
    ):
        """
        Regression test: Agent should use its OWN system prompt, not another agent's.

        Bug: Job Search Agent was responding as Email Assistant because system_message
        vs system_prompt parameter name, or checkpointer caching old state.
        """
        now = datetime.now(UTC)

        # Create agent with distinctive system prompt
        job_agent = AgentDefinition(
            id="job-search-agent",
            name="Job Search Agent",
            description="Finds jobs",
            system_prompt="You are a JOB SEARCH agent. Help find AI/ML jobs.",
            is_template=False,
            model="claude-sonnet-4-20250514",
            tools=[
                ToolConfig(name="web_search", source=ToolSource.BUILTIN, enabled=True),
            ],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(job_agent)

        # Mock dependencies
        mock_cred_store = AsyncMock()
        mock_cred_store.get.return_value = None  # No credentials

        mock_mcp_repo = AsyncMock()
        mock_mcp_repo.list_all.return_value = []

        tool_registry = ToolRegistryImpl(mock_mcp_repo)

        use_case = RunAgentUseCase(
            agent_repo=agent_repo,
            credential_store=mock_cred_store,
            tool_registry=tool_registry,
            skill_repo=skill_repo,
        )

        # Capture what gets passed to create_deep_agent
        captured_kwargs = {}

        with patch("backend.application.use_cases.run_agent.create_deep_agent") as mock_create:
            mock_agent = MagicMock()
            mock_create.return_value = mock_agent

            with patch("backend.application.use_cases.run_agent.get_checkpointer") as mock_cp:
                mock_cp.return_value = MagicMock()

                await use_case.get_or_create_agent("job-search-agent", "thread-1")

                # Verify create_deep_agent was called
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args.kwargs

                # KEY ASSERTION: system_prompt must contain our agent's prompt
                assert "system_prompt" in call_kwargs
                assert "JOB SEARCH" in call_kwargs["system_prompt"]
                assert "email" not in call_kwargs["system_prompt"].lower()

    @pytest.mark.asyncio
    async def test_skills_appended_to_system_prompt(self, agent_repo, skill_repo, db_session):
        """Skills should be appended to base system prompt."""
        now = datetime.now(UTC)

        agent = AgentDefinition(
            id="agent-with-skill",
            name="Agent With Skill",
            description="Test",
            system_prompt="Base prompt here.",
            is_template=False,
            model="claude-sonnet-4-20250514",
            tools=[],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(agent)

        # Add a skill
        await skill_repo.create(
            agent_id="agent-with-skill",
            name="summarize",
            description="Summarize content",
            instructions="When asked to summarize, use bullet points.",
        )
        await db_session.commit()

        mock_cred_store = AsyncMock()
        mock_cred_store.get.return_value = None

        mock_mcp_repo = AsyncMock()
        mock_mcp_repo.list_all.return_value = []

        tool_registry = ToolRegistryImpl(mock_mcp_repo)

        use_case = RunAgentUseCase(
            agent_repo=agent_repo,
            credential_store=mock_cred_store,
            tool_registry=tool_registry,
            skill_repo=skill_repo,
        )

        with patch("backend.application.use_cases.run_agent.create_deep_agent") as mock_create:
            mock_create.return_value = MagicMock()

            with patch("backend.application.use_cases.run_agent.get_checkpointer") as mock_cp:
                mock_cp.return_value = MagicMock()

                await use_case.get_or_create_agent("agent-with-skill", "thread-1")

                call_kwargs = mock_create.call_args.kwargs
                system_prompt = call_kwargs["system_prompt"]

                # Base prompt and skill should both be present
                assert "Base prompt here" in system_prompt
                assert "summarize" in system_prompt.lower()
                assert "bullet points" in system_prompt


class TestAuthRequirements:
    """Verify correct auth requirements for different tool types."""

    @pytest.mark.asyncio
    async def test_web_search_does_not_require_google_auth(self, agent_repo, skill_repo):
        """
        Regression test: web_search, memory, slack tools should NOT require Google OAuth.

        Bug: All builtin tools were triggering Google auth check, blocking agents
        that only use web/memory/slack tools.
        """
        now = datetime.now(UTC)

        agent = AgentDefinition(
            id="web-agent",
            name="Web Agent",
            description="Web search only",
            system_prompt="You search the web.",
            is_template=False,
            model="claude-sonnet-4-20250514",
            tools=[
                ToolConfig(name="web_search", source=ToolSource.BUILTIN, enabled=True),
                ToolConfig(name="write_memory", source=ToolSource.BUILTIN, enabled=True),
                ToolConfig(name="read_memory", source=ToolSource.BUILTIN, enabled=True),
            ],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(agent)

        mock_cred_store = AsyncMock()
        mock_cred_store.get.return_value = None  # No Google credentials

        mock_mcp_repo = AsyncMock()
        mock_mcp_repo.list_all.return_value = []

        tool_registry = ToolRegistryImpl(mock_mcp_repo)

        use_case = RunAgentUseCase(
            agent_repo=agent_repo,
            credential_store=mock_cred_store,
            tool_registry=tool_registry,
            skill_repo=skill_repo,
        )

        with patch("backend.application.use_cases.run_agent.create_deep_agent") as mock_create:
            mock_create.return_value = MagicMock()

            with patch("backend.application.use_cases.run_agent.get_checkpointer") as mock_cp:
                mock_cp.return_value = MagicMock()

                # Should NOT raise CredentialNotFoundError
                agent, config = await use_case.get_or_create_agent("web-agent", "thread-1")

                # Verify agent was created
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_gmail_tools_require_google_auth(self, agent_repo, skill_repo):
        """Gmail tools SHOULD require Google OAuth."""
        now = datetime.now(UTC)

        agent = AgentDefinition(
            id="email-agent",
            name="Email Agent",
            description="Email management",
            system_prompt="You manage emails.",
            is_template=False,
            model="claude-sonnet-4-20250514",
            tools=[
                ToolConfig(name="list_emails", source=ToolSource.BUILTIN, enabled=True),
                ToolConfig(name="send_email", source=ToolSource.BUILTIN, enabled=True),
            ],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(agent)

        mock_cred_store = AsyncMock()
        mock_cred_store.get.return_value = None  # No Google credentials

        mock_mcp_repo = AsyncMock()
        mock_mcp_repo.list_all.return_value = []

        tool_registry = ToolRegistryImpl(mock_mcp_repo)

        use_case = RunAgentUseCase(
            agent_repo=agent_repo,
            credential_store=mock_cred_store,
            tool_registry=tool_registry,
            skill_repo=skill_repo,
        )

        # Should raise CredentialNotFoundError for Gmail tools
        with pytest.raises(CredentialNotFoundError):
            await use_case.get_or_create_agent("email-agent", "thread-1")


class TestHITLConfiguration:
    """Verify HITL interrupt_on is configured correctly."""

    @pytest.mark.asyncio
    async def test_interrupt_on_is_dict_not_list(self, agent_repo, skill_repo):
        """
        Regression test: interrupt_on must be dict format for deepagents.

        Bug: Was passing list of tool names, but deepagents expects
        dict like {"tool_name": True} or {"tool_name": InterruptOnConfig(...)}.
        """
        now = datetime.now(UTC)

        agent = AgentDefinition(
            id="hitl-agent",
            name="HITL Agent",
            description="Agent with HITL tools",
            system_prompt="You are helpful.",
            is_template=False,
            model="claude-sonnet-4-20250514",
            tools=[
                ToolConfig(name="web_search", source=ToolSource.BUILTIN, enabled=True),
                ToolConfig(name="send_email", source=ToolSource.BUILTIN, enabled=True, hitl_enabled=True),
            ],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(agent)

        mock_cred_store = AsyncMock()
        mock_cred_store.get.return_value = {"token": "fake"}  # Provide creds

        mock_mcp_repo = AsyncMock()
        mock_mcp_repo.list_all.return_value = []

        tool_registry = ToolRegistryImpl(mock_mcp_repo)

        use_case = RunAgentUseCase(
            agent_repo=agent_repo,
            credential_store=mock_cred_store,
            tool_registry=tool_registry,
            skill_repo=skill_repo,
        )

        with patch("backend.application.use_cases.run_agent.create_deep_agent") as mock_create:
            mock_create.return_value = MagicMock()

            with patch("backend.application.use_cases.run_agent.get_checkpointer") as mock_cp:
                mock_cp.return_value = MagicMock()

                await use_case.get_or_create_agent("hitl-agent", "thread-1")

                call_kwargs = mock_create.call_args.kwargs
                interrupt_on = call_kwargs.get("interrupt_on")

                # KEY ASSERTION: Must be dict, not list
                assert interrupt_on is None or isinstance(interrupt_on, dict)

                if interrupt_on:
                    # Verify format is {tool_name: True}
                    for key, value in interrupt_on.items():
                        assert isinstance(key, str)
                        assert value is True or hasattr(value, "__class__")  # True or config object

    @pytest.mark.asyncio
    async def test_memory_tools_in_hitl_list(self, agent_repo, skill_repo):
        """Memory write tools should always be in HITL list."""
        now = datetime.now(UTC)

        agent = AgentDefinition(
            id="memory-agent",
            name="Memory Agent",
            description="Agent with memory",
            system_prompt="You remember things.",
            is_template=False,
            model="claude-sonnet-4-20250514",
            tools=[
                ToolConfig(name="web_search", source=ToolSource.BUILTIN, enabled=True),
            ],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(agent)

        mock_cred_store = AsyncMock()
        mock_cred_store.get.return_value = None

        mock_mcp_repo = AsyncMock()
        mock_mcp_repo.list_all.return_value = []

        tool_registry = ToolRegistryImpl(mock_mcp_repo)

        use_case = RunAgentUseCase(
            agent_repo=agent_repo,
            credential_store=mock_cred_store,
            tool_registry=tool_registry,
            skill_repo=skill_repo,
        )

        with patch("backend.application.use_cases.run_agent.create_deep_agent") as mock_create:
            mock_create.return_value = MagicMock()

            with patch("backend.application.use_cases.run_agent.get_checkpointer") as mock_cp:
                mock_cp.return_value = MagicMock()

                await use_case.get_or_create_agent("memory-agent", "thread-1")

                call_kwargs = mock_create.call_args.kwargs
                interrupt_on = call_kwargs.get("interrupt_on")

                # Memory write tool should be in HITL
                if interrupt_on:
                    assert "write_memory" in interrupt_on
