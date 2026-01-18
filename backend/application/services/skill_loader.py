"""Service for loading skills with progressive disclosure.

Implements Anthropic's three-stage progressive disclosure:
1. Metadata only (name, description) - injected into system prompt
2. Full instructions - loaded on-demand via memory tools
3. Resources (scripts/, references/, assets/) - future feature

Reference: https://agentskills.io/specification
"""

from typing import Protocol

import frontmatter

from backend.domain.entities import Skill


class SkillRepositoryProtocol(Protocol):
    """Protocol for skill repository dependency."""

    async def list_by_agent(self, agent_id: str) -> list[Skill]:
        ...

    async def get_by_name(self, agent_id: str, name: str) -> Skill | None:
        ...


class SkillLoader:
    """Orchestrates skill loading with progressive disclosure.

    Implements the Agent Skills specification's progressive disclosure model:
    - Stage 1: Metadata-only injection into system prompt (~100 tokens/skill)
    - Stage 2: Full instructions loaded when agent reads skills/{name}.md
    - Stage 3: Resources loaded when referenced (deferred to future)
    """

    def __init__(self, skill_repo: SkillRepositoryProtocol):
        """Initialize the skill loader.

        Args:
            skill_repo: Repository for skill data access
        """
        self.skill_repo = skill_repo

    async def get_metadata_for_prompt(self, agent_id: str) -> str:
        """Get skills metadata section for system prompt injection.

        Returns compact metadata list for progressive disclosure stage 1.
        Only name and description are included to minimize token usage.

        Args:
            agent_id: Agent ID

        Returns:
            Formatted markdown section with skill name/description only,
            or empty string if no skills configured
        """
        skills = await self.skill_repo.list_by_agent(agent_id)
        if not skills:
            return ""

        section = "\n\n## Available Skills\n\n"
        section += (
            "You have access to the following skills. To use a skill:\n"
            "1. Read its full instructions from `skills/{skill-name}.md` using the read_memory tool\n"
            "2. Follow the instructions in the skill file\n"
            "3. Prefix your response with `[Using skill: {skill-name}]`\n\n"
        )

        for skill in skills:
            section += f"- **{skill.name}**: {skill.description}\n"

        return section

    async def get_full_instructions(
        self, agent_id: str, skill_name: str
    ) -> str | None:
        """Get full skill instructions (progressive disclosure stage 2).

        Called when agent reads skills/{skill-name}.md via memory tools.
        Returns the complete skill as markdown with YAML frontmatter.

        Args:
            agent_id: Agent ID
            skill_name: Normalized skill name (lowercase, hyphens)

        Returns:
            Full skill markdown with frontmatter, or None if not found
        """
        skill = await self.skill_repo.get_by_name(agent_id, skill_name)
        if not skill:
            return None

        return self._format_skill_markdown(skill)

    def _format_skill_markdown(self, skill: Skill) -> str:
        """Format skill as markdown with YAML frontmatter per spec.

        Args:
            skill: Skill entity

        Returns:
            Formatted markdown string with YAML frontmatter
        """
        post = frontmatter.Post(skill.instructions)
        post.metadata["name"] = skill.name
        post.metadata["description"] = skill.description

        # Optional spec fields
        if skill.license:
            post.metadata["license"] = skill.license
        if skill.compatibility:
            post.metadata["compatibility"] = skill.compatibility
        if skill.metadata:
            post.metadata["metadata"] = skill.metadata
        if skill.allowed_tools:
            # Spec uses space-delimited string for allowed-tools
            post.metadata["allowed-tools"] = " ".join(skill.allowed_tools)

        return frontmatter.dumps(post)
