"""Create Agent use case."""

from pydantic import BaseModel
from datetime import datetime
import uuid

from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    TriggerConfig,
    SubagentConfig,
)
from backend.domain.ports import AgentRepository


class CreateAgentRequest(BaseModel):
    """Request to create a new agent."""
    name: str
    description: str = ""
    system_prompt: str
    model: str = "claude-sonnet-4-20250514"
    tools: list[ToolConfig] = []
    subagents: list[SubagentConfig] = []
    triggers: list[TriggerConfig] = []
    is_template: bool = False


class CreateAgentResponse(BaseModel):
    """Response from creating an agent."""
    agent_id: str


class CreateAgentUseCase:
    """Use case for creating a new agent.

    Creates an agent definition and persists it to the repository.
    """

    def __init__(self, agent_repo: AgentRepository):
        """Initialize the use case.

        Args:
            agent_repo: Repository for agent persistence
        """
        self.agent_repo = agent_repo

    async def execute(self, request: CreateAgentRequest) -> CreateAgentResponse:
        """Execute the use case.

        Args:
            request: Agent creation request

        Returns:
            Response with the new agent ID
        """
        now = datetime.utcnow()

        agent = AgentDefinition(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            model=request.model,
            tools=request.tools,
            subagents=request.subagents,
            triggers=request.triggers,
            is_template=request.is_template,
            created_at=now,
            updated_at=now,
        )

        await self.agent_repo.save(agent)
        return CreateAgentResponse(agent_id=agent.id)
