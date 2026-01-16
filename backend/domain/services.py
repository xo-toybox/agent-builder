"""Domain service protocols for Agent Builder.

Defines abstract interfaces for domain services that coordinate
complex operations involving multiple entities.
"""

from typing import Protocol, Any
from backend.domain.entities import AgentDefinition, ToolConfig


class ToolFactory(Protocol):
    """Creates executable tools from configuration.

    Responsible for instantiating LangChain-compatible tools
    from ToolConfig objects.
    """

    def create_tools(
        self,
        configs: list[ToolConfig],
        credentials: dict
    ) -> list[Any]:
        """Create LangChain-compatible tools from configs.

        Args:
            configs: List of tool configurations
            credentials: OAuth/API credentials for tool access

        Returns:
            List of instantiated tool objects
        """
        ...


class AgentFactory(Protocol):
    """Creates runnable agents from definitions.

    Responsible for converting AgentDefinition into executable
    deepagents instances.
    """

    def create_agent(
        self,
        definition: AgentDefinition,
        credentials: dict,
        checkpointer: Any
    ) -> Any:
        """Create a deepagents instance from definition.

        Args:
            definition: Agent definition with config
            credentials: OAuth/API credentials
            checkpointer: LangGraph checkpointer for state persistence

        Returns:
            Runnable agent instance
        """
        ...


class TriggerManager(Protocol):
    """Manages trigger lifecycle.

    Responsible for starting, stopping, and monitoring triggers
    that activate agents.
    """

    async def start(self, agent_id: str, trigger_id: str) -> None:
        """Start a trigger for an agent.

        Args:
            agent_id: ID of the agent to trigger
            trigger_id: ID of the trigger configuration
        """
        ...

    async def stop(self, trigger_id: str) -> None:
        """Stop a running trigger.

        Args:
            trigger_id: ID of the trigger to stop
        """
        ...

    async def stop_all(self, agent_id: str) -> None:
        """Stop all triggers for an agent.

        Args:
            agent_id: ID of the agent
        """
        ...

    def list_running(self) -> list[str]:
        """List IDs of all currently running triggers.

        Returns:
            List of trigger IDs that are active
        """
        ...
