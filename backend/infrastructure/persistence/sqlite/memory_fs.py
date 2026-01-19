"""Virtual filesystem for agent memory backed by SQLite.

Provides a file-like abstraction over SQLite tables for agent memory.
The virtual structure is:

    /agents/{agent_id}/
    ├── AGENTS.md           # Read-only: Maps to AgentModel.system_prompt
    ├── tools.json          # Read-only: Maps to AgentModel.tools relationship
    ├── skills/             # Read/write: Maps to skills table
    │   ├── skill1.md
    │   └── skill2.md
    └── knowledge/          # Read/write: Maps to memory_files table
        ├── preferences.md
        └── contacts.md
"""

import json
import re
from typing import Protocol
from backend.domain.entities import AgentDefinition


class AgentRepositoryProtocol(Protocol):
    """Protocol for agent repository dependency."""
    async def get(self, agent_id: str) -> AgentDefinition | None: ...


class SkillLoaderProtocol(Protocol):
    """Protocol for skill loader service dependency (v0.0.3)."""
    async def get_full_instructions(self, agent_id: str, skill_name: str) -> str | None: ...


class SkillRepositoryProtocol(Protocol):
    """Protocol for skill repository dependency."""
    async def list_by_agent(self, agent_id: str) -> list: ...


class MemoryRepositoryProtocol(Protocol):
    """Protocol for memory repository dependency."""
    async def get(self, agent_id: str, path: str) -> dict | None: ...
    async def list_files(self, agent_id: str, directory: str) -> list[str]: ...


# Maximum memory file size (100KB)
MAX_MEMORY_FILE_SIZE = 100 * 1024


class MemoryFileSystem:
    """Virtual filesystem backed by SQLite tables.

    Provides read access to agent configuration (AGENTS.md, tools.json)
    and read/write access to skills and knowledge directories.
    """

    def __init__(
        self,
        agent_repo: AgentRepositoryProtocol,
        skill_repo: SkillRepositoryProtocol,
        memory_repo: MemoryRepositoryProtocol,
        skill_loader: SkillLoaderProtocol | None = None,
    ):
        """Initialize the filesystem with required repositories.

        Args:
            agent_repo: Repository for agent definitions
            skill_repo: Repository for skills (used for listing)
            memory_repo: Repository for memory files
            skill_loader: Service for loading skill content (v0.0.3, progressive disclosure)
        """
        self.agent_repo = agent_repo
        self.skill_repo = skill_repo
        self.memory_repo = memory_repo
        self.skill_loader = skill_loader

    def validate_path(self, agent_id: str, path: str) -> bool:
        """Validate that a path is safe and within agent's scope.

        Prevents path traversal attacks and access to other agents' data.

        Args:
            agent_id: Agent ID for scope checking
            path: Path to validate (can be relative or absolute)

        Returns:
            True if path is valid and safe
        """
        # Check agent scope if path has /agents/{id}/ prefix
        raw = path.lstrip("/")
        if raw.startswith("agents/"):
            parts = raw.split("/", 2)
            # Must have at least agents/{id}/... and id must match
            if len(parts) < 3 or parts[1] != agent_id:
                return False

        # Normalize the path
        normalized = self._normalize_path(path)

        # Check for path traversal attempts
        if ".." in normalized:
            return False

        # Must start with valid directory
        if not (normalized.startswith("knowledge/") or normalized.startswith("skills/")):
            return False

        # Check for valid filename characters
        filename = normalized.split("/")[-1]
        if not re.match(r"^[a-zA-Z0-9_-]+\.(md|txt|json)$", filename):
            return False

        return True

    def _normalize_path(self, path: str) -> str:
        """Normalize a path, removing agent_id prefix if present.

        Args:
            path: Path to normalize

        Returns:
            Normalized relative path (e.g., "knowledge/preferences.md")
        """
        # Remove leading slashes
        path = path.lstrip("/")

        # Remove /agents/{agent_id}/ prefix if present
        if path.startswith("agents/"):
            parts = path.split("/", 3)
            if len(parts) >= 3:
                path = "/".join(parts[2:])

        return path

    async def read(self, agent_id: str, path: str) -> str:
        """Read a file from the virtual filesystem.

        Args:
            agent_id: Agent ID
            path: Virtual path to read

        Returns:
            File contents

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If path is invalid
        """
        normalized = self._normalize_path(path)

        # Read-only virtual files
        if normalized == "AGENTS.md":
            agent = await self.agent_repo.get(agent_id)
            if not agent:
                raise FileNotFoundError(f"Agent {agent_id} not found")
            return agent.system_prompt

        elif normalized == "tools.json":
            agent = await self.agent_repo.get(agent_id)
            if not agent:
                raise FileNotFoundError(f"Agent {agent_id} not found")
            return json.dumps(
                [{"name": t.name, "source": t.source.value, "enabled": t.enabled} for t in agent.tools],
                indent=2,
            )

        # Skills directory (v0.0.3: progressive disclosure via SkillLoader)
        elif normalized.startswith("skills/"):
            # Extract skill name from path: "skills/pdf-processing.md" -> "pdf-processing"
            skill_name = normalized[7:]  # Remove "skills/"
            if skill_name.endswith(".md"):
                skill_name = skill_name[:-3]

            # Use SkillLoader for progressive disclosure if available
            if self.skill_loader:
                content = await self.skill_loader.get_full_instructions(agent_id, skill_name)
                if not content:
                    raise FileNotFoundError(f"Skill not found: {normalized}")
                return content
            else:
                # Fallback: list skills and check if name exists
                skills = await self.skill_repo.list_by_agent(agent_id)
                skill = next((s for s in skills if s.name == skill_name), None)
                if not skill:
                    raise FileNotFoundError(f"Skill not found: {normalized}")
                # Return basic markdown format
                return f"---\nname: {skill.name}\ndescription: {skill.description}\n---\n\n{skill.instructions}"

        # Knowledge directory
        elif normalized.startswith("knowledge/"):
            file = await self.memory_repo.get(agent_id, normalized)
            if not file:
                raise FileNotFoundError(f"Memory file not found: {normalized}")
            return file.get("content", "")

        else:
            raise PermissionError(f"Invalid path: {path}")

    async def read_safe(self, agent_id: str, path: str) -> str | None:
        """Read a file, returning None if not found.

        Args:
            agent_id: Agent ID
            path: Virtual path to read

        Returns:
            File contents or None if not found
        """
        try:
            return await self.read(agent_id, path)
        except FileNotFoundError:
            return None

    async def list_files(self, agent_id: str, directory: str = "knowledge") -> list[str]:
        """List files in a directory.

        Args:
            agent_id: Agent ID
            directory: Directory to list ("knowledge" or "skills")

        Returns:
            List of file paths
        """
        if directory == "knowledge":
            return await self.memory_repo.list_files(agent_id, directory)
        elif directory == "skills":
            skills = await self.skill_repo.list_by_agent(agent_id)
            return [f"skills/{s.name}.md" for s in skills]
        else:
            return []

    def validate_content_size(self, content: str) -> tuple[bool, str]:
        """Validate that content doesn't exceed size limits.

        Args:
            content: Content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        size = len(content.encode("utf-8"))
        if size > MAX_MEMORY_FILE_SIZE:
            return (
                False,
                f"Content too large ({size // 1024}KB). Maximum is {MAX_MEMORY_FILE_SIZE // 1024}KB.",
            )
        return True, ""
