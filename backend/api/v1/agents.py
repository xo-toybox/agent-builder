"""Agent CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.domain.entities import ToolConfig, TriggerConfig, SubagentConfig

# Available models for validation
AVAILABLE_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-5-20251101",
    "claude-haiku-4-20250514",
]
from backend.domain.exceptions import AgentNotFoundError
from backend.application.use_cases.create_agent import CreateAgentUseCase, CreateAgentRequest
from backend.application.use_cases.clone_template import CloneTemplateUseCase, CloneTemplateRequest
from backend.api.dependencies import get_agent_repo

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentSummary(BaseModel):
    """Agent summary for list views."""
    id: str
    name: str
    description: str
    is_template: bool


class AgentDetail(BaseModel):
    """Full agent details."""
    id: str
    name: str
    description: str
    system_prompt: str
    model: str
    memory_approval_required: bool
    tools: list[ToolConfig]
    subagents: list[SubagentConfig]
    triggers: list[TriggerConfig]
    is_template: bool


class CreateAgentBody(BaseModel):
    """Request body for creating an agent."""
    name: str
    description: str = ""
    system_prompt: str
    model: str = "claude-sonnet-4-20250514"
    tools: list[ToolConfig] = []
    subagents: list[SubagentConfig] = []
    triggers: list[TriggerConfig] = []


class UpdateAgentBody(BaseModel):
    """Request body for updating an agent."""
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    memory_approval_required: bool | None = None
    tools: list[ToolConfig] | None = None
    subagents: list[SubagentConfig] | None = None
    triggers: list[TriggerConfig] | None = None


class CloneBody(BaseModel):
    """Request body for cloning an agent."""
    new_name: str


@router.get("", response_model=list[AgentSummary])
async def list_agents(
    is_template: Optional[bool] = None,
    agent_repo=Depends(get_agent_repo)
):
    """List all agents, optionally filtered by template status."""
    agents = await agent_repo.list_all(is_template=is_template)
    return [
        AgentSummary(
            id=a.id,
            name=a.name,
            description=a.description,
            is_template=a.is_template,
        )
        for a in agents
    ]


@router.get("/templates", response_model=list[AgentSummary])
async def list_templates(agent_repo=Depends(get_agent_repo)):
    """List all agent templates."""
    agents = await agent_repo.list_all(is_template=True)
    return [
        AgentSummary(
            id=a.id,
            name=a.name,
            description=a.description,
            is_template=True,
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentDetail)
async def get_agent(
    agent_id: str,
    agent_repo=Depends(get_agent_repo)
):
    """Get agent details."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentDetail(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        model=agent.model,
        memory_approval_required=agent.memory_approval_required,
        tools=agent.tools,
        subagents=agent.subagents,
        triggers=agent.triggers,
        is_template=agent.is_template,
    )


@router.post("", response_model=dict)
async def create_agent(
    body: CreateAgentBody,
    agent_repo=Depends(get_agent_repo)
):
    """Create a new agent."""
    # Validate model
    if body.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Must be one of: {AVAILABLE_MODELS}",
        )

    use_case = CreateAgentUseCase(agent_repo)
    request = CreateAgentRequest(
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt,
        model=body.model,
        tools=body.tools,
        subagents=body.subagents,
        triggers=body.triggers,
    )
    response = await use_case.execute(request)
    return {"agent_id": response.agent_id}


@router.put("/{agent_id}", response_model=dict)
async def update_agent(
    agent_id: str,
    body: UpdateAgentBody,
    agent_repo=Depends(get_agent_repo)
):
    """Update an agent."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Update fields if provided
    if body.name is not None:
        agent.name = body.name
    if body.description is not None:
        agent.description = body.description
    if body.system_prompt is not None:
        agent.system_prompt = body.system_prompt
    if body.model is not None:
        if body.model not in AVAILABLE_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model. Must be one of: {AVAILABLE_MODELS}",
            )
        agent.model = body.model
    if body.memory_approval_required is not None:
        agent.memory_approval_required = body.memory_approval_required
    if body.tools is not None:
        agent.tools = body.tools
    if body.subagents is not None:
        agent.subagents = body.subagents
    if body.triggers is not None:
        agent.triggers = body.triggers

    await agent_repo.save(agent)
    return {"success": True}


@router.post("/{agent_id}/clone", response_model=dict)
async def clone_agent(
    agent_id: str,
    body: CloneBody,
    agent_repo=Depends(get_agent_repo)
):
    """Clone an agent (typically from a template)."""
    use_case = CloneTemplateUseCase(agent_repo)
    try:
        request = CloneTemplateRequest(template_id=agent_id, new_name=body.new_name)
        response = await use_case.execute(request)
        return {"agent_id": response.agent_id}
    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    agent_repo=Depends(get_agent_repo)
):
    """Delete an agent."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.is_template:
        raise HTTPException(status_code=400, detail="Cannot delete templates")

    await agent_repo.delete(agent_id)
    return {"success": True}
