"""
Tests for domain entities.
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.domain.entities import (
    AgentDefinition,
    HITLDecision,
    HITLRequest,
    MCPServerConfig,
    SubagentConfig,
    ToolConfig,
    ToolSource,
    TriggerConfig,
    TriggerType,
)


class TestToolConfig:
    """Tests for ToolConfig entity."""

    def test_create_builtin_tool(self):
        """Test creating a built-in tool configuration."""
        tool = ToolConfig(
            name="list_emails",
            source=ToolSource.BUILTIN,
            enabled=True,
            hitl_enabled=False,
        )
        assert tool.name == "list_emails"
        assert tool.source == ToolSource.BUILTIN
        assert tool.enabled is True
        assert tool.hitl_enabled is False
        assert tool.server_id is None

    def test_create_mcp_tool_with_server_id(self):
        """Test creating an MCP tool configuration with server_id."""
        tool = ToolConfig(
            name="custom_tool",
            source=ToolSource.MCP,
            enabled=True,
            hitl_enabled=True,
            server_id="my-mcp-server",
            server_config={"url": "http://localhost:8080"},
        )
        assert tool.name == "custom_tool"
        assert tool.source == ToolSource.MCP
        assert tool.server_id == "my-mcp-server"
        assert tool.server_config == {"url": "http://localhost:8080"}

    def test_mcp_tool_requires_server_id(self):
        """Test that MCP tools require a server_id."""
        with pytest.raises(ValidationError) as exc_info:
            ToolConfig(
                name="custom_tool",
                source=ToolSource.MCP,
                enabled=True,
            )
        assert "MCP tools must have a server_id" in str(exc_info.value)

    def test_default_values(self):
        """Test default values for tool configuration."""
        tool = ToolConfig(name="test_tool", source=ToolSource.BUILTIN)
        assert tool.enabled is True
        assert tool.hitl_enabled is False
        assert tool.server_config == {}


class TestTriggerConfig:
    """Tests for TriggerConfig entity."""

    def test_create_scheduled_trigger(self):
        """Test creating a scheduled trigger."""
        trigger = TriggerConfig(
            id="trigger-1",
            type=TriggerType.SCHEDULED,
            enabled=True,
            config={"cron": "0 9 * * *"},
        )
        assert trigger.type == TriggerType.SCHEDULED
        assert trigger.enabled is True
        assert trigger.config["cron"] == "0 9 * * *"

    def test_create_email_polling_trigger(self):
        """Test creating an email polling trigger."""
        trigger = TriggerConfig(
            id="trigger-2",
            type=TriggerType.EMAIL_POLLING,
            enabled=True,
            config={"poll_interval": 60, "filter": "is:unread"},
        )
        assert trigger.type == TriggerType.EMAIL_POLLING
        assert trigger.config["poll_interval"] == 60

    def test_create_webhook_trigger(self):
        """Test creating a webhook trigger."""
        trigger = TriggerConfig(
            id="trigger-3",
            type=TriggerType.WEBHOOK,
            enabled=False,
            config={"endpoint": "/webhook/trigger"},
        )
        assert trigger.type == TriggerType.WEBHOOK
        assert trigger.enabled is False

    def test_default_enabled(self):
        """Test default enabled value."""
        trigger = TriggerConfig(id="trigger-4", type=TriggerType.SCHEDULED)
        assert trigger.enabled is False


class TestSubagentConfig:
    """Tests for SubagentConfig entity."""

    def test_create_subagent(self):
        """Test creating a subagent configuration."""
        subagent = SubagentConfig(
            name="Research Assistant",
            description="Researches topics",
            system_prompt="You are a research assistant.",
            tools=["search", "read"],
        )
        assert subagent.name == "Research Assistant"
        assert subagent.description == "Researches topics"
        assert "search" in subagent.tools


class TestAgentDefinition:
    """Tests for AgentDefinition entity."""

    def test_create_minimal_agent(self):
        """Test creating an agent with minimal configuration."""
        now = datetime.utcnow()
        agent = AgentDefinition(
            id="agent-1",
            name="Test Agent",
            description="A simple test agent",
            system_prompt="You are a test assistant.",
            created_at=now,
            updated_at=now,
        )
        assert agent.name == "Test Agent"
        assert agent.description == "A simple test agent"
        assert agent.is_template is False
        assert agent.tools == []
        assert agent.triggers == []
        assert agent.subagents == []

    def test_create_agent_with_tools(self, sample_tool_configs):
        """Test creating an agent with tools."""
        now = datetime.utcnow()
        agent = AgentDefinition(
            id="agent-2",
            name="Agent with Tools",
            description="Has tools",
            system_prompt="You have tools.",
            tools=sample_tool_configs,
            created_at=now,
            updated_at=now,
        )
        assert len(agent.tools) == 3
        assert agent.tools[0].name == "list_emails"

    def test_create_template(self, sample_tool_configs):
        """Test creating a template agent."""
        now = datetime.utcnow()
        template = AgentDefinition(
            id="my-template",
            name="Email Template",
            description="Template for email agents",
            system_prompt="Email assistant prompt.",
            is_template=True,
            tools=sample_tool_configs,
            created_at=now,
            updated_at=now,
        )
        assert template.is_template is True
        assert template.id == "my-template"

    def test_default_model(self):
        """Test default model is set."""
        now = datetime.utcnow()
        agent = AgentDefinition(
            id="agent-3",
            name="Test",
            description="Test",
            system_prompt="Test",
            created_at=now,
            updated_at=now,
        )
        assert agent.model == "claude-sonnet-4-20250514"

    def test_custom_model(self):
        """Test custom model can be set."""
        now = datetime.utcnow()
        agent = AgentDefinition(
            id="agent-4",
            name="Test",
            description="Test",
            system_prompt="Test",
            model="claude-3-opus-20240229",
            created_at=now,
            updated_at=now,
        )
        assert agent.model == "claude-3-opus-20240229"


class TestHITLRequest:
    """Tests for HITLRequest entity."""

    def test_create_hitl_request(self):
        """Test creating an HITL request."""
        now = datetime.utcnow()
        request = HITLRequest(
            id="hitl-123",
            agent_id="agent-456",
            thread_id="thread-789",
            tool_call_id="call-001",
            tool_name="send_email",
            tool_args={"to": "user@example.com", "subject": "Test"},
            status="pending",
            created_at=now,
        )
        assert request.id == "hitl-123"
        assert request.agent_id == "agent-456"
        assert request.status == "pending"
        assert request.decision is None
        assert request.edited_args is None

    def test_hitl_decision_values(self):
        """Test HITL decision enum values."""
        assert HITLDecision.APPROVE == "approve"
        assert HITLDecision.REJECT == "reject"
        assert HITLDecision.EDIT == "edit"


class TestMCPServerConfig:
    """Tests for MCPServerConfig entity."""

    def test_create_stdio_server(self):
        """Test creating a stdio MCP server configuration."""
        server = MCPServerConfig(
            id="my-server",
            name="My MCP Server",
            command="node",
            args=["server.js"],
        )
        assert server.id == "my-server"
        assert server.command == "node"
        assert server.args == ["server.js"]

    def test_default_enabled(self):
        """Test default enabled value."""
        server = MCPServerConfig(
            id="server",
            name="Server",
            command="cmd",
        )
        assert server.enabled is True

    def test_server_with_env(self):
        """Test creating server with environment variables."""
        server = MCPServerConfig(
            id="server",
            name="Server",
            command="python",
            args=["-m", "server"],
            env={"API_KEY": "secret"},
        )
        assert server.env == {"API_KEY": "secret"}
