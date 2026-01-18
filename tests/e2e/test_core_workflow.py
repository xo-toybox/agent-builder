"""
Minimal E2E test for core v0.0.3 workflow.

Covers: templates → clone → memory → skills
Intentionally minimal as behavior is evolving.
"""

from datetime import datetime, UTC

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.api.v1 import agents, memory, skills
from backend.api.dependencies import get_agent_repo, get_memory_repo, get_skill_repo
from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    ToolSource,
)
from backend.infrastructure.persistence.sqlite.agent_repo import SQLiteAgentRepository
from backend.infrastructure.persistence.sqlite.memory_repo import MemoryRepository
from backend.infrastructure.persistence.sqlite.skill_repo import SkillRepository
from backend.infrastructure.persistence.sqlite.database import Base


@pytest_asyncio.fixture
async def app_with_repos():
    """Create FastAPI app with in-memory database for all v0.0.3 features."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        agent_repo = SQLiteAgentRepository(session)
        memory_repo = MemoryRepository(session)
        skill_repo = SkillRepository(session)

        # Seed templates (simulating startup behavior)
        now = datetime.now(UTC)
        email_template = AgentDefinition(
            id="email_assistant_template",
            name="Email Assistant",
            description="An intelligent email assistant with memory support.",
            system_prompt="You are an email assistant.",
            is_template=True,
            model="claude-sonnet-4-20250514",
            tools=[
                ToolConfig(name="list_emails", source=ToolSource.BUILTIN, hitl_enabled=False),
                ToolConfig(name="send_email", source=ToolSource.BUILTIN, hitl_enabled=True),
                ToolConfig(name="write_memory", source=ToolSource.BUILTIN, hitl_enabled=True),
                ToolConfig(name="read_memory", source=ToolSource.BUILTIN, hitl_enabled=False),
            ],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(email_template)

        research_template = AgentDefinition(
            id="research_assistant_template",
            name="Research Assistant",
            description="A web research assistant that learns your preferences.",
            system_prompt="You are a research assistant.",
            is_template=True,
            model="claude-sonnet-4-20250514",
            tools=[
                ToolConfig(name="web_search", source=ToolSource.BUILTIN, hitl_enabled=False),
                ToolConfig(name="write_memory", source=ToolSource.BUILTIN, hitl_enabled=True),
                ToolConfig(name="read_memory", source=ToolSource.BUILTIN, hitl_enabled=False),
            ],
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(research_template)

        app = FastAPI()
        app.include_router(agents.router, prefix="/api/v1")
        app.include_router(memory.router, prefix="/api/v1")
        app.include_router(skills.router, prefix="/api/v1")

        app.dependency_overrides[get_agent_repo] = lambda: agent_repo
        app.dependency_overrides[get_memory_repo] = lambda: memory_repo
        app.dependency_overrides[get_skill_repo] = lambda: skill_repo

        yield app, agent_repo, memory_repo, skill_repo, session

    await engine.dispose()


class TestCoreWorkflow:
    """E2E test for core v0.0.3 workflow."""

    @pytest.mark.asyncio
    async def test_templates_available(self, app_with_repos):
        """Verify templates are seeded and accessible."""
        app, _, _, _, _ = app_with_repos
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/agents/templates")
            assert response.status_code == 200

            templates = response.json()
            assert len(templates) == 2

            names = {t["name"] for t in templates}
            assert "Email Assistant" in names
            assert "Research Assistant" in names

    @pytest.mark.asyncio
    async def test_clone_template_and_verify_tools(self, app_with_repos):
        """Clone template and verify memory tools are included."""
        app, _, _, _, _ = app_with_repos
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Clone email assistant template
            response = await client.post(
                "/api/v1/agents/email_assistant_template/clone",
                json={"new_name": "My Email Agent"},
            )
            assert response.status_code == 200
            agent_id = response.json()["agent_id"]

            # Get the cloned agent
            response = await client.get(f"/api/v1/agents/{agent_id}")
            assert response.status_code == 200

            agent = response.json()
            assert agent["name"] == "My Email Agent"
            assert agent["is_template"] is False

            # Verify memory tools were included
            tool_names = {t["name"] for t in agent["tools"]}
            assert "write_memory" in tool_names
            assert "read_memory" in tool_names

    @pytest.mark.asyncio
    async def test_skills_crud_workflow(self, app_with_repos):
        """Test creating, listing, and deleting skills."""
        app, agent_repo, _, _, _ = app_with_repos
        transport = ASGITransport(app=app)

        # First create an agent to attach skills to
        now = datetime.now(UTC)
        agent = AgentDefinition(
            id="test-agent-skills",
            name="Test Agent",
            description="Test",
            system_prompt="Test",
            is_template=False,
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(agent)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create a skill 
            response = await client.post(
                "/api/v1/agents/test-agent-skills/skills",
                json={
                    "name": "summarize_email",  # Will be normalized to "summarize-email"
                    "description": "Summarize long emails",
                    "instructions": "When user asks for summary, provide bullet points.",
                },
            )
            assert response.status_code == 201
            skill = response.json()
            assert skill["name"] == "summarize-email"
            skill_id = skill["id"]

            # List skills
            response = await client.get("/api/v1/agents/test-agent-skills/skills")
            assert response.status_code == 200
            skills = response.json()["skills"]
            assert len(skills) == 1

            # Delete skill
            response = await client.delete(
                f"/api/v1/agents/test-agent-skills/skills/{skill_id}"
            )
            assert response.status_code == 204

            # Verify deleted
            response = await client.get("/api/v1/agents/test-agent-skills/skills")
            assert len(response.json()["skills"]) == 0

    @pytest.mark.asyncio
    async def test_memory_workflow(self, app_with_repos):
        """Test memory file operations."""
        app, agent_repo, memory_repo, _, _ = app_with_repos
        transport = ASGITransport(app=app)

        # Create an agent
        now = datetime.now(UTC)
        agent = AgentDefinition(
            id="test-agent-memory",
            name="Test Agent",
            description="Test",
            system_prompt="Test",
            is_template=False,
            created_at=now,
            updated_at=now,
        )
        await agent_repo.save(agent)

        # Seed a memory file directly (simulating agent writing memory)
        await memory_repo.save(
            agent_id="test-agent-memory",
            path="knowledge/preferences.md",
            content="# Preferences\n\n- User prefers bullet points",
        )

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # List memory files
            response = await client.get("/api/v1/agents/test-agent-memory/memory")
            assert response.status_code == 200
            files = response.json()["files"]
            assert len(files) == 1
            assert files[0]["path"] == "knowledge/preferences.md"

            # Get specific file
            response = await client.get(
                "/api/v1/agents/test-agent-memory/memory/knowledge/preferences.md"
            )
            assert response.status_code == 200
            file_data = response.json()
            assert "bullet points" in file_data["content"]

            # Delete file
            response = await client.delete(
                "/api/v1/agents/test-agent-memory/memory/knowledge/preferences.md"
            )
            assert response.status_code == 204

            # Verify deleted
            response = await client.get("/api/v1/agents/test-agent-memory/memory")
            assert len(response.json()["files"]) == 0

    @pytest.mark.asyncio
    async def test_research_template_has_web_search(self, app_with_repos):
        """Verify Research Assistant template has web_search tool."""
        app, _, _, _, _ = app_with_repos
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/agents/research_assistant_template")
            assert response.status_code == 200

            agent = response.json()
            tool_names = {t["name"] for t in agent["tools"]}
            assert "web_search" in tool_names
            assert "Email" not in agent["description"]  # Verify correct description
