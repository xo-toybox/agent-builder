"""
Tests for the agents API endpoints.
"""
from datetime import datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.api.v1.agents import router
from backend.api.dependencies import get_agent_repo
from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    ToolSource,
)
from backend.infrastructure.persistence.sqlite.agent_repo import SQLiteAgentRepository
from backend.infrastructure.persistence.sqlite.database import Base


@pytest_asyncio.fixture
async def app_with_repo():
    """Create FastAPI app with real in-memory database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        repo = SQLiteAgentRepository(session)

        # Seed a template
        now = datetime.utcnow()
        template = AgentDefinition(
            id="email_assistant_template",
            name="Email Assistant",
            description="Template email assistant",
            system_prompt="You are an email assistant.",
            is_template=True,
            tools=[
                ToolConfig(name="list_emails", source=ToolSource.BUILTIN, hitl_enabled=False),
                ToolConfig(name="send_email", source=ToolSource.BUILTIN, hitl_enabled=True),
            ],
            created_at=now,
            updated_at=now,
        )
        await repo.save(template)

        # Seed a regular agent
        agent = AgentDefinition(
            id="test-agent-123",
            name="Test Agent",
            description="A test agent",
            system_prompt="Test prompt",
            is_template=False,
            created_at=now,
            updated_at=now,
        )
        await repo.save(agent)

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Override dependency - return the repo directly
        def override_get_agent_repo():
            return repo

        app.dependency_overrides[get_agent_repo] = override_get_agent_repo

        yield app, repo, session

    await engine.dispose()


class TestAgentsAPI:
    """Tests for agents API endpoints."""

    @pytest.mark.asyncio
    async def test_list_agents(self, app_with_repo):
        """Test listing agents."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # List all agents (both templates and non-templates)
            response = await client.get("/api/v1/agents")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_agents_non_templates(self, app_with_repo):
        """Test listing only non-template agents."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/agents?is_template=false")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "test-agent-123"
            assert data[0]["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_list_templates(self, app_with_repo):
        """Test listing templates."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/agents/templates")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "email_assistant_template"
            assert data[0]["name"] == "Email Assistant"

    @pytest.mark.asyncio
    async def test_get_agent(self, app_with_repo):
        """Test getting a specific agent."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/agents/test-agent-123")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test-agent-123"
            assert data["name"] == "Test Agent"
            assert data["description"] == "A test agent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, app_with_repo):
        """Test getting a nonexistent agent."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/agents/nonexistent")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_agent(self, app_with_repo):
        """Test creating a new agent."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            new_agent = {
                "name": "New Agent",
                "description": "A newly created agent",
                "system_prompt": "You are a helpful assistant.",
            }
            response = await client.post("/api/v1/agents", json=new_agent)
            assert response.status_code == 200
            data = response.json()
            assert "agent_id" in data

    @pytest.mark.asyncio
    async def test_create_agent_with_tools(self, app_with_repo):
        """Test creating an agent with tools."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            new_agent = {
                "name": "Agent with Tools",
                "description": "Has tools",
                "system_prompt": "You have tools.",
                "tools": [
                    {
                        "name": "list_emails",
                        "source": "builtin",
                        "enabled": True,
                        "hitl_enabled": False,
                    }
                ],
            }
            response = await client.post("/api/v1/agents", json=new_agent)
            assert response.status_code == 200
            agent_id = response.json()["agent_id"]

            # Verify the agent was created with tools
            get_response = await client.get(f"/api/v1/agents/{agent_id}")
            assert get_response.status_code == 200
            data = get_response.json()
            assert len(data["tools"]) == 1
            assert data["tools"][0]["name"] == "list_emails"

    @pytest.mark.asyncio
    async def test_delete_agent(self, app_with_repo):
        """Test deleting an agent."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Delete the test agent
            delete_response = await client.delete("/api/v1/agents/test-agent-123")
            assert delete_response.status_code == 200

            # Verify it's gone
            get_response = await client.get("/api/v1/agents/test-agent-123")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template_fails(self, app_with_repo):
        """Test that deleting a template fails."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/v1/agents/email_assistant_template")
            assert response.status_code == 400
            assert "template" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_clone_agent(self, app_with_repo):
        """Test cloning an agent/template."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            clone_request = {"new_name": "Cloned Email Agent"}
            response = await client.post(
                "/api/v1/agents/email_assistant_template/clone",
                json=clone_request,
            )
            assert response.status_code == 200
            agent_id = response.json()["agent_id"]

            # Get the cloned agent
            get_response = await client.get(f"/api/v1/agents/{agent_id}")
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["name"] == "Cloned Email Agent"
            assert data["is_template"] is False
            # Should have copied tools
            assert len(data["tools"]) == 2

    @pytest.mark.asyncio
    async def test_clone_nonexistent_agent(self, app_with_repo):
        """Test cloning a nonexistent agent."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            clone_request = {"new_name": "Won't Work"}
            response = await client.post(
                "/api/v1/agents/nonexistent/clone",
                json=clone_request,
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_agent(self, app_with_repo):
        """Test updating an agent."""
        app, _, _ = app_with_repo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            update_body = {
                "name": "Updated Agent",
                "description": "Updated description",
            }
            response = await client.put(
                "/api/v1/agents/test-agent-123",
                json=update_body,
            )
            assert response.status_code == 200

            # Verify the update
            get_response = await client.get("/api/v1/agents/test-agent-123")
            data = get_response.json()
            assert data["name"] == "Updated Agent"
            assert data["description"] == "Updated description"
