"""Domain entities for Agent Builder.

Core business models that represent the domain concepts.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from backend.domain.validation.skill_validator import (
    normalize_skill_name,
    validate_skill_name,
)


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
    memory_approval_required: bool = False  # v0.0.3: Require HITL approval for memory writes
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


class Skill(BaseModel):
    """Agent skill following Anthropic Agent Skills specification.

    Skills are packages of specialized instructions that agents load dynamically.
    Progressive disclosure: Only name/description loaded into system prompt by default,
    full instructions accessed via memory filesystem when needed.

    Reference: https://agentskills.io/specification
    """

    id: str
    agent_id: str
    name: str = Field(..., max_length=64)  # Spec: lowercase-hyphenated
    description: str = Field(..., max_length=1024)  # Spec: max 1024 chars
    instructions: str  # Full skill instructions (markdown body)

    # Optional spec fields
    license: str | None = None
    compatibility: str | None = Field(None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
    allowed_tools: list[str] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def auto_normalize_name(cls, values: dict) -> dict:
        """Auto-normalize name to spec format (lowercase, hyphens)."""
        if isinstance(values, dict) and "name" in values:
            values["name"] = normalize_skill_name(values["name"])
        return values

    @field_validator("name")
    @classmethod
    def validate_name_spec(cls, v: str) -> str:
        """Validate name against Anthropic spec rules."""
        validate_skill_name(v)
        return v

    @field_validator("description")
    @classmethod
    def validate_description_not_empty(cls, v: str) -> str:
        """Ensure description is non-empty."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v
