"""Memory tools for agents to read and write their knowledge.

These tools allow agents to persistently store information they learn
from conversations. All write operations require HITL approval.
"""

from typing import Callable
from langchain_core.tools import tool

from backend.infrastructure.persistence.sqlite.memory_fs import (
    MemoryFileSystem,
    MAX_MEMORY_FILE_SIZE,
)


def create_memory_tools(
    memory_fs: MemoryFileSystem,
    agent_id: str,
    memory_approval_required: bool = True,
) -> list[Callable]:
    """Create memory tools for an agent.

    Args:
        memory_fs: Virtual filesystem for memory
        agent_id: Agent ID for scoping
        memory_approval_required: Whether write_memory requires HITL approval

    Returns:
        List of memory tool functions
    """

    @tool
    async def write_memory(path: str, content: str, reason: str) -> str:
        """
        Propose saving information to agent memory for user approval.

        Use this when you learn something worth remembering:
        - User preferences (formatting, tone, contacts)
        - Corrections to your behavior
        - Facts the user wants you to remember

        Args:
            path: Where to save (e.g., "knowledge/preferences.md")
            content: What to save (markdown format)
            reason: Why you want to remember this

        Returns:
            Status message indicating the proposal was created
        """
        # Validate path
        if not memory_fs.validate_path(agent_id, path):
            return f"Error: Invalid path '{path}'. Use 'knowledge/filename.md' format."

        # Validate content size
        is_valid, error_msg = memory_fs.validate_content_size(content)
        if not is_valid:
            return f"Error: {error_msg}"

        # The actual write is handled by HITL flow in chat.py
        # This tool just signals intent and returns a pending message
        return f"Memory update proposed at '{path}'. Waiting for user approval."

    # Mark as requiring HITL approval based on agent setting
    write_memory.metadata = {"requires_hitl": memory_approval_required}

    @tool
    async def read_memory(path: str) -> str:
        """
        Read from agent memory.

        Use this to recall information you previously saved:
        - User preferences
        - Contact information
        - Previous corrections

        Args:
            path: What to read (e.g., "knowledge/preferences.md")

        Returns:
            File contents or error message
        """
        try:
            content = await memory_fs.read(agent_id, path)
            return content
        except FileNotFoundError:
            return f"No memory file found at '{path}'."
        except PermissionError as e:
            return f"Error: {e}"

    @tool
    async def list_memory(directory: str = "knowledge") -> str:
        """
        List files in agent memory.

        Use this to see what you have remembered:
        - "knowledge" - User preferences, facts, contacts
        - "skills" - Reusable instructions

        Args:
            directory: Which directory to list ("skills" or "knowledge")

        Returns:
            List of file paths or message if empty
        """
        if directory not in ("knowledge", "skills"):
            return "Error: directory must be 'knowledge' or 'skills'"

        files = await memory_fs.list_files(agent_id, directory)

        if not files:
            return f"No files in {directory}/ directory."

        return "\n".join(files)

    return [write_memory, read_memory, list_memory]
