"""Domain-specific exceptions for Agent Builder.

Custom exceptions for domain-level errors that may occur
during business operations.
"""


class DomainError(Exception):
    """Base exception for all domain errors."""
    pass


class AgentNotFoundError(DomainError):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: {agent_id}")


class AgentValidationError(DomainError):
    """Raised when agent validation fails."""

    def __init__(self, message: str):
        super().__init__(message)


class ToolNotFoundError(DomainError):
    """Raised when a tool is not found."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool not found: {tool_name}")


class MCPServerNotFoundError(DomainError):
    """Raised when an MCP server configuration is not found."""

    def __init__(self, server_id: str):
        self.server_id = server_id
        super().__init__(f"MCP server not found: {server_id}")


class CredentialNotFoundError(DomainError):
    """Raised when credentials are not found."""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Credentials not found for provider: {provider}")


class HITLRequestNotFoundError(DomainError):
    """Raised when a HITL request is not found."""

    def __init__(self, request_id: str):
        self.request_id = request_id
        super().__init__(f"HITL request not found: {request_id}")


class TriggerError(DomainError):
    """Raised when a trigger operation fails."""

    def __init__(self, trigger_id: str, message: str):
        self.trigger_id = trigger_id
        super().__init__(f"Trigger error ({trigger_id}): {message}")


class MCPConnectionError(DomainError):
    """Raised when MCP server connection fails."""

    def __init__(self, server_id: str, message: str):
        self.server_id = server_id
        super().__init__(f"MCP connection error ({server_id}): {message}")
