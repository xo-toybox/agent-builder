"""Domain layer for Agent Builder.

Contains core business entities, repository protocols, and service interfaces.
"""

from backend.domain.entities import (
    ToolSource,
    ToolConfig,
    TriggerType,
    TriggerConfig,
    SubagentConfig,
    AgentDefinition,
    HITLDecision,
    HITLRequest,
    MCPServerConfig,
)
from backend.domain.ports import (
    AgentRepository,
    MCPRepository,
    HITLRepository,
    ConversationRepository,
    CredentialStore,
)
from backend.domain.services import (
    ToolFactory,
    AgentFactory,
    TriggerManager,
)
from backend.domain.exceptions import (
    DomainError,
    AgentNotFoundError,
    AgentValidationError,
    ToolNotFoundError,
    MCPServerNotFoundError,
    CredentialNotFoundError,
    HITLRequestNotFoundError,
)

__all__ = [
    # Entities
    "ToolSource",
    "ToolConfig",
    "TriggerType",
    "TriggerConfig",
    "SubagentConfig",
    "AgentDefinition",
    "HITLDecision",
    "HITLRequest",
    "MCPServerConfig",
    # Ports
    "AgentRepository",
    "MCPRepository",
    "HITLRepository",
    "ConversationRepository",
    "CredentialStore",
    # Services
    "ToolFactory",
    "AgentFactory",
    "TriggerManager",
    # Exceptions
    "DomainError",
    "AgentNotFoundError",
    "AgentValidationError",
    "ToolNotFoundError",
    "MCPServerNotFoundError",
    "CredentialNotFoundError",
    "HITLRequestNotFoundError",
]
