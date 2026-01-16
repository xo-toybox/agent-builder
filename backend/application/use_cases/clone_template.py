"""Clone Template use case."""

from pydantic import BaseModel

from backend.domain.ports import AgentRepository
from backend.domain.exceptions import AgentNotFoundError


class CloneTemplateRequest(BaseModel):
    """Request to clone a template."""
    template_id: str
    new_name: str


class CloneTemplateResponse(BaseModel):
    """Response from cloning a template."""
    agent_id: str


class CloneTemplateUseCase:
    """Use case for cloning an agent template.

    Creates a new agent from an existing template.
    """

    def __init__(self, agent_repo: AgentRepository):
        """Initialize the use case.

        Args:
            agent_repo: Repository for agent persistence
        """
        self.agent_repo = agent_repo

    async def execute(self, request: CloneTemplateRequest) -> CloneTemplateResponse:
        """Execute the use case.

        Args:
            request: Clone template request

        Returns:
            Response with the new agent ID

        Raises:
            AgentNotFoundError: If template not found
        """
        # Verify template exists
        template = await self.agent_repo.get(request.template_id)
        if not template:
            raise AgentNotFoundError(request.template_id)

        # Clone the template
        new_id = await self.agent_repo.clone(
            request.template_id,
            request.new_name
        )

        return CloneTemplateResponse(agent_id=new_id)
