"""Domain entities for Agent Builder.

Core business models that represent the domain concepts.
"""

from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from enum import Enum
from typing import Literal


class ToolSource(str, Enum):
    """Source of a tool - either built-in or from an MCP server."""
    BUILTIN = "builtin"
    MCP = "mcp"


class ToolConfig(BaseModel):
    """Configuration for a tool attached to an agent."""
    name: str
    source: ToolSource
    enabled: bool = True
    hitl_enabled: bool = False
    server_id: str | None = None  # Required for MCP tools
    server_config: dict = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_mcp_server_id(self):
        """Ensure MCP tools have a server_id."""
        if self.source == ToolSource.MCP and not self.server_id:
            raise ValueError("MCP tools must have a server_id")
        return self


class TriggerType(str, Enum):
    """Types of triggers that can activate an agent."""
    EMAIL_POLLING = "email_polling"
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    EVENT = "event"


class TriggerConfig(BaseModel):
    """Trigger configuration for an agent."""
    id: str
    type: TriggerType
    enabled: bool = False
    config: dict = Field(default_factory=dict)


class SubagentConfig(BaseModel):
    """Subagent configuration - a delegated agent with specific capabilities."""
    name: str
    description: str
    system_prompt: str
    tools: list[str]  # List of tool names


class AgentDefinition(BaseModel):
    """Core agent definition.

    Can be either a template (is_template=True) or a user-created agent.
    Templates can be cloned to create new agents.
    """
    id: str
    name: str
    description: str = ""
    system_prompt: str
    model: str = "claude-sonnet-4-20250514"
    tools: list[ToolConfig] = Field(default_factory=list)
    subagents: list[SubagentConfig] = Field(default_factory=list)
    triggers: list[TriggerConfig] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    is_template: bool = False


class HITLDecision(str, Enum):
    """Human-in-the-loop decision types."""
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class HITLRequest(BaseModel):
    """Pending human-in-the-loop approval request.

    Created when an agent invokes a tool that requires human approval.
    """
    id: str
    thread_id: str
    agent_id: str
    tool_call_id: str
    tool_name: str
    tool_args: dict
    status: Literal["pending", "approved", "rejected", "edited"]
    decision: HITLDecision | None = None
    edited_args: dict | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class MCPServerConfig(BaseModel):
    """MCP (Model Context Protocol) server connection configuration.

    Defines how to connect to an external MCP server that provides tools.
    """
    id: str
    name: str
    command: str  # Command to run the server
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
