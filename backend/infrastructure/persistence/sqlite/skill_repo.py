"""Repository for agent skills (Anthropic Agent Skills spec).

Implements CRUD operations for skills stored in SQLite,
returning Skill domain entities with spec-compliant validation.

Reference: https://agentskills.io/specification
"""

import uuid
from datetime import datetime

import frontmatter
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities import Skill
from backend.domain.validation.skill_validator import (
    normalize_skill_name,
    validate_skill_name,
)
from backend.infrastructure.persistence.sqlite.models import SkillModel


def parse_skill_markdown(content: str) -> tuple[dict, str]:
    """Parse skill markdown with YAML frontmatter.

    Args:
        content: Markdown content with YAML frontmatter

    Returns:
        Tuple of (metadata dict, instructions string)

    Raises:
        ValueError: If required fields are missing
    """
    post = frontmatter.loads(content)
    metadata = dict(post.metadata)

    if "name" not in metadata:
        raise ValueError("Skill must have 'name' in frontmatter")
    if "description" not in metadata:
        raise ValueError("Skill must have 'description' in frontmatter")

    # Parse allowed-tools from space-delimited string to list
    if "allowed-tools" in metadata:
        allowed_tools_str = metadata.pop("allowed-tools")
        if isinstance(allowed_tools_str, str):
            metadata["allowed_tools"] = allowed_tools_str.split()
        else:
            metadata["allowed_tools"] = allowed_tools_str or []

    return metadata, post.content


class SkillRepository:
    """Repository for skills stored in SQLite.

    Returns Skill domain entities with automatic name normalization
    and spec-compliant validation.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get(self, skill_id: str) -> Skill | None:
        """Get a skill by ID.

        Args:
            skill_id: Skill ID

        Returns:
            Skill entity or None if not found
        """
        result = await self.session.execute(
            select(SkillModel).where(SkillModel.id == skill_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        return self._model_to_entity(model)

    async def get_by_name(self, agent_id: str, name: str) -> Skill | None:
        """Get a skill by agent ID and name.

        Args:
            agent_id: Agent ID
            name: Skill name (will be normalized for lookup)

        Returns:
            Skill entity or None if not found
        """
        # Normalize the name for lookup
        normalized_name = normalize_skill_name(name)

        result = await self.session.execute(
            select(SkillModel).where(
                SkillModel.agent_id == agent_id,
                SkillModel.name == normalized_name,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        return self._model_to_entity(model)

    async def list_by_agent(self, agent_id: str) -> list[Skill]:
        """List all skills for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of Skill entities
        """
        result = await self.session.execute(
            select(SkillModel)
            .where(SkillModel.agent_id == agent_id)
            .order_by(SkillModel.name)
        )
        return [self._model_to_entity(model) for model in result.scalars().all()]

    async def count_by_agent(self, agent_id: str) -> int:
        """Count skills for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Number of skills
        """
        result = await self.session.execute(
            select(func.count()).select_from(SkillModel).where(SkillModel.agent_id == agent_id)
        )
        return result.scalar() or 0

    async def create(
        self,
        agent_id: str,
        name: str,
        description: str,
        instructions: str,
        license: str | None = None,
        compatibility: str | None = None,
        metadata: dict | None = None,
        allowed_tools: list[str] | None = None,
    ) -> Skill:
        """Create a new skill.

        Name will be auto-normalized to spec format (lowercase, hyphens).

        Args:
            agent_id: Agent ID
            name: Skill name (will be normalized)
            description: Skill description (max 1024 chars)
            instructions: Skill instructions
            license: Optional license identifier
            compatibility: Optional compatibility requirements (max 500 chars)
            metadata: Optional JSON metadata
            allowed_tools: Optional list of pre-approved tools

        Returns:
            Created Skill entity

        Raises:
            ValueError: If skill limit (50) exceeded or validation fails
        """
        # Check skill limit
        count = await self.count_by_agent(agent_id)
        if count >= 50:
            raise ValueError(
                "Maximum 50 skills per agent. Delete unused skills to add more."
            )

        # Create entity (validates and normalizes name)
        now = datetime.utcnow()
        skill = Skill(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            name=name,  # Auto-normalized by Skill entity
            description=description,
            instructions=instructions,
            license=license,
            compatibility=compatibility,
            metadata=metadata or {},
            allowed_tools=allowed_tools or [],
            created_at=now,
            updated_at=now,
        )

        # Persist to database
        model = SkillModel(
            id=skill.id,
            agent_id=skill.agent_id,
            name=skill.name,
            description=skill.description,
            instructions=skill.instructions,
            license=skill.license,
            compatibility=skill.compatibility,
            skill_metadata=skill.metadata,
            allowed_tools=skill.allowed_tools,
            created_at=skill.created_at,
            updated_at=skill.updated_at,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

        return skill

    async def create_from_markdown(self, agent_id: str, content: str) -> Skill:
        """Create a skill from markdown with YAML frontmatter.

        Args:
            agent_id: Agent ID
            content: Markdown content with frontmatter

        Returns:
            Created Skill entity
        """
        metadata, instructions = parse_skill_markdown(content)
        return await self.create(
            agent_id=agent_id,
            name=metadata["name"],
            description=metadata["description"],
            instructions=instructions,
            license=metadata.get("license"),
            compatibility=metadata.get("compatibility"),
            metadata=metadata.get("metadata"),
            allowed_tools=metadata.get("allowed_tools"),
        )

    async def update(
        self,
        skill_id: str,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        license: str | None = None,
        compatibility: str | None = None,
        metadata: dict | None = None,
        allowed_tools: list[str] | None = None,
    ) -> Skill | None:
        """Update a skill.

        If name is provided, it will be normalized to spec format.

        Args:
            skill_id: Skill ID
            name: New name (optional, will be normalized)
            description: New description (optional)
            instructions: New instructions (optional)
            license: New license (optional)
            compatibility: New compatibility (optional)
            metadata: New metadata (optional)
            allowed_tools: New allowed tools (optional)

        Returns:
            Updated Skill entity or None if not found
        """
        result = await self.session.execute(
            select(SkillModel).where(SkillModel.id == skill_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        # Apply updates to model fields
        new_name = model.name
        if name is not None:
            new_name = normalize_skill_name(name)
            # Validate normalized name before applying
            validate_skill_name(new_name)
            model.name = new_name

        new_description = model.description
        if description is not None:
            new_description = description
            # Validate description
            if not new_description or not new_description.strip():
                raise ValueError("Description cannot be empty")
            model.description = new_description

        if instructions is not None:
            model.instructions = instructions
        if license is not None:
            model.license = license
        if compatibility is not None:
            model.compatibility = compatibility
        if metadata is not None:
            model.skill_metadata = metadata
        if allowed_tools is not None:
            model.allowed_tools = allowed_tools

        model.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(model)

        return self._model_to_entity(model)

    async def delete(self, skill_id: str) -> bool:
        """Delete a skill.

        Args:
            skill_id: Skill ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(SkillModel).where(SkillModel.id == skill_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    def _model_to_entity(self, model: SkillModel) -> Skill:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: SkillModel instance

        Returns:
            Skill domain entity
        """
        return Skill(
            id=model.id,
            agent_id=model.agent_id,
            name=model.name,
            description=model.description,
            instructions=model.instructions,
            license=model.license,
            compatibility=model.compatibility,
            metadata=model.skill_metadata or {},
            allowed_tools=model.allowed_tools or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
