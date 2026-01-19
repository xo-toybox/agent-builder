"""Skills management API endpoints (v0.0.3).

Provides REST endpoints for creating and managing agent skills
following the Anthropic Agent Skills specification.

Reference: https://agentskills.io/specification
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.dependencies import get_skill_repo
from backend.domain.entities import Skill
from backend.domain.validation.skill_validator import normalize_skill_name
from backend.infrastructure.persistence.sqlite.skill_repo import SkillRepository

router = APIRouter(prefix="/agents/{agent_id}/skills", tags=["skills"])


class SkillCreate(BaseModel):
    """Request model for creating a skill.

    Name will be auto-normalized to spec format (lowercase, hyphens).
    """

    name: str = Field(..., description="Skill name (will be normalized to lowercase-hyphens)")
    description: str = Field(..., max_length=1024, description="What the skill does and when to use it")
    instructions: str = Field(..., description="Full skill instructions (markdown)")

    # v0.0.3: Anthropic Agent Skills spec optional fields
    license: str | None = Field(None, description="License identifier")
    compatibility: str | None = Field(None, max_length=500, description="Environment requirements")
    metadata: dict[str, Any] | None = Field(None, description="Arbitrary key-value metadata")
    allowed_tools: list[str] | None = Field(None, description="List of pre-approved tools")


class SkillUpdate(BaseModel):
    """Request model for updating a skill."""

    name: str | None = Field(None, description="New name (will be normalized)")
    description: str | None = Field(None, max_length=1024)
    instructions: str | None = None

    # v0.0.3: Anthropic Agent Skills spec optional fields
    license: str | None = None
    compatibility: str | None = Field(None, max_length=500)
    metadata: dict[str, Any] | None = None
    allowed_tools: list[str] | None = None


class SkillResponse(BaseModel):
    """Response model for a skill."""

    id: str
    name: str  # Normalized name (lowercase-hyphens)
    description: str
    instructions: str

    # v0.0.3: Anthropic Agent Skills spec optional fields
    license: str | None = None
    compatibility: str | None = None
    metadata: dict[str, Any] | None = None
    allowed_tools: list[str] | None = None

    created_at: str
    updated_at: str


class SkillListResponse(BaseModel):
    """Response model for list of skills."""

    skills: list[SkillResponse]


def _skill_to_response(skill: Skill) -> SkillResponse:
    """Convert Skill entity to API response."""
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        instructions=skill.instructions,
        license=skill.license,
        compatibility=skill.compatibility,
        metadata=skill.metadata if skill.metadata else None,
        allowed_tools=skill.allowed_tools if skill.allowed_tools else None,
        created_at=skill.created_at.isoformat(),
        updated_at=skill.updated_at.isoformat(),
    )


@router.get("", response_model=SkillListResponse)
async def list_skills(
    agent_id: str,
    skill_repo: SkillRepository = Depends(get_skill_repo),
):
    """List all skills for an agent."""
    skills = await skill_repo.list_by_agent(agent_id)
    return SkillListResponse(skills=[_skill_to_response(s) for s in skills])


@router.post("", response_model=SkillResponse, status_code=201)
async def create_skill(
    agent_id: str,
    data: SkillCreate,
    skill_repo: SkillRepository = Depends(get_skill_repo),
):
    """Create a new skill for an agent.

    Name will be auto-normalized to spec format (lowercase, hyphens).
    Returns 409 if a skill with the same normalized name already exists.
    """
    # Check for duplicate name (normalize first)
    normalized_name = normalize_skill_name(data.name)
    existing = await skill_repo.get_by_name(agent_id, normalized_name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Skill with name '{normalized_name}' already exists (normalized from '{data.name}')",
        )

    try:
        skill = await skill_repo.create(
            agent_id=agent_id,
            name=data.name,  # Will be normalized in repository
            description=data.description,
            instructions=data.instructions,
            license=data.license,
            compatibility=data.compatibility,
            metadata=data.metadata,
            allowed_tools=data.allowed_tools,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _skill_to_response(skill)


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    agent_id: str,
    skill_id: str,
    skill_repo: SkillRepository = Depends(get_skill_repo),
):
    """Get a specific skill."""
    skill = await skill_repo.get(skill_id)
    if not skill or skill.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Skill not found")

    return _skill_to_response(skill)


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    agent_id: str,
    skill_id: str,
    data: SkillUpdate,
    skill_repo: SkillRepository = Depends(get_skill_repo),
):
    """Update a skill.

    If name is provided, it will be normalized to spec format.
    """
    # Verify skill belongs to agent
    existing = await skill_repo.get(skill_id)
    if not existing or existing.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Check for duplicate name if changing name
    if data.name:
        normalized_name = normalize_skill_name(data.name)
        if normalized_name != existing.name:
            duplicate = await skill_repo.get_by_name(agent_id, normalized_name)
            if duplicate:
                raise HTTPException(
                    status_code=409,
                    detail=f"Skill with name '{normalized_name}' already exists",
                )

    try:
        skill = await skill_repo.update(
            skill_id=skill_id,
            name=data.name,
            description=data.description,
            instructions=data.instructions,
            license=data.license,
            compatibility=data.compatibility,
            metadata=data.metadata,
            allowed_tools=data.allowed_tools,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _skill_to_response(skill)


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    agent_id: str,
    skill_id: str,
    skill_repo: SkillRepository = Depends(get_skill_repo),
):
    """Delete a skill."""
    # Verify skill belongs to agent
    existing = await skill_repo.get(skill_id)
    if not existing or existing.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Skill not found")

    await skill_repo.delete(skill_id)
    return None
