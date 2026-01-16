"""Repository ports (interfaces) for Agent Builder.

Defines abstract interfaces that infrastructure adapters must implement.
Following the Ports & Adapters (Hexagonal) architecture pattern.
"""

from typing import Protocol
from backend.domain.entities import (
    AgentDefinition,
    MCPServerConfig,
    HITLRequest,
)


class AgentRepository(Protocol):
    """Port for agent persistence."""

    async def save(self, agent: AgentDefinition) -> None:
        """Save or update an agent definition."""
        ...

    async def get(self, id: str) -> AgentDefinition | None:
        """Get an agent by ID. Returns None if not found."""
        ...

    async def list_all(self, is_template: bool | None = None) -> list[AgentDefinition]:
        """List all agents, optionally filtered by template status."""
        ...

    async def delete(self, id: str) -> None:
        """Delete an agent by ID."""
        ...

    async def clone(self, id: str, new_name: str) -> str:
        """Clone an agent with a new name. Returns the new agent's ID."""
        ...


class MCPRepository(Protocol):
    """Port for MCP server configuration persistence."""

    async def save(self, server: MCPServerConfig) -> None:
        """Save or update an MCP server configuration."""
        ...

    async def get(self, id: str) -> MCPServerConfig | None:
        """Get an MCP server config by ID. Returns None if not found."""
        ...

    async def list_all(self) -> list[MCPServerConfig]:
        """List all MCP server configurations."""
        ...

    async def delete(self, id: str) -> None:
        """Delete an MCP server configuration by ID."""
        ...


class HITLRepository(Protocol):
    """Port for HITL (Human-in-the-Loop) request persistence."""

    async def save(self, request: HITLRequest) -> None:
        """Save a new HITL request."""
        ...

    async def get(self, id: str) -> HITLRequest | None:
        """Get a HITL request by ID. Returns None if not found."""
        ...

    async def get_by_tool_call(self, tool_call_id: str) -> HITLRequest | None:
        """Get a HITL request by tool call ID. Returns None if not found."""
        ...

    async def list_pending(self, agent_id: str) -> list[HITLRequest]:
        """List all pending HITL requests for an agent."""
        ...

    async def update_status(
        self,
        id: str,
        decision: str,
        edited_args: dict | None = None
    ) -> None:
        """Update the status/decision of a HITL request."""
        ...


class ConversationRepository(Protocol):
    """Port for conversation thread persistence."""

    async def save_message(
        self,
        thread_id: str,
        agent_id: str,
        message: dict
    ) -> None:
        """Save a message to a conversation thread."""
        ...

    async def get_thread(self, thread_id: str) -> list[dict]:
        """Get all messages in a conversation thread."""
        ...

    async def list_threads(self, agent_id: str) -> list[str]:
        """List all thread IDs for an agent."""
        ...

    async def delete_thread(self, thread_id: str) -> None:
        """Delete a conversation thread and all its messages."""
        ...


class CredentialStore(Protocol):
    """Port for secure credential storage.

    Credentials are stored encrypted and keyed by provider name.
    """

    async def save(self, provider: str, credentials: dict) -> None:
        """Save credentials for a provider (encrypted)."""
        ...

    async def get(self, provider: str) -> dict | None:
        """Get credentials for a provider. Returns None if not found."""
        ...

    async def delete(self, provider: str) -> None:
        """Delete credentials for a provider."""
        ...
