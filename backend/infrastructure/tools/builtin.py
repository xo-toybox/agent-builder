"""Built-in tool factory for Agent Builder.

Provides a unified factory for creating all built-in tools.
"""

from typing import Any
from google.oauth2.credentials import Credentials

from backend.infrastructure.tools.builtin_gmail import create_gmail_tools
from backend.infrastructure.tools.builtin_calendar import create_calendar_tools


class BuiltinToolFactory:
    """Factory for creating built-in tools.

    Creates LangChain-compatible tools for built-in services
    like Gmail and Calendar.
    """

    # Tool name to category mapping
    TOOL_CATEGORIES = {
        "list_emails": "gmail",
        "get_email": "gmail",
        "search_emails": "gmail",
        "draft_reply": "gmail",
        "send_email": "gmail",
        "label_email": "gmail",
        "list_events": "calendar",
        "get_event": "calendar",
    }

    # Available tools metadata
    AVAILABLE_TOOLS = {
        "gmail": [
            {"name": "list_emails", "description": "List emails from inbox with filters"},
            {"name": "get_email", "description": "Get full email content by ID"},
            {"name": "search_emails", "description": "Search emails using Gmail query syntax"},
            {"name": "draft_reply", "description": "Create draft reply (HITL recommended)"},
            {"name": "send_email", "description": "Send email (HITL recommended)"},
            {"name": "label_email", "description": "Modify email labels"},
        ],
        "calendar": [
            {"name": "list_events", "description": "List calendar events for a date range"},
            {"name": "get_event", "description": "Get event details"},
        ],
    }

    def __init__(self):
        self._tool_cache: dict[int, list] = {}

    def create_all_tools(self, credentials: Credentials) -> list[Any]:
        """Create all built-in tools.

        Args:
            credentials: Google OAuth credentials

        Returns:
            List of all available tools
        """
        cache_key = id(credentials)

        if cache_key not in self._tool_cache:
            gmail_tools = create_gmail_tools(credentials)
            calendar_tools = create_calendar_tools(credentials)
            self._tool_cache[cache_key] = gmail_tools + calendar_tools

        return self._tool_cache[cache_key]

    def get_tool_by_name(self, name: str, credentials: Credentials) -> Any | None:
        """Get a single tool by name.

        Args:
            name: Tool name
            credentials: Google OAuth credentials

        Returns:
            Tool instance or None if not found
        """
        all_tools = self.create_all_tools(credentials)

        for tool in all_tools:
            if tool.name == name:
                return tool

        return None

    def get_tools_by_names(
        self,
        names: list[str],
        credentials: Credentials
    ) -> list[Any]:
        """Get multiple tools by name.

        Args:
            names: List of tool names
            credentials: Google OAuth credentials

        Returns:
            List of tool instances (missing tools are skipped)
        """
        all_tools = self.create_all_tools(credentials)
        tool_map = {t.name: t for t in all_tools}

        return [tool_map[name] for name in names if name in tool_map]

    @classmethod
    def list_available(cls) -> dict[str, list[dict]]:
        """List all available built-in tools by category.

        Returns:
            Dict mapping category to list of tool metadata
        """
        return cls.AVAILABLE_TOOLS

    @classmethod
    def get_category(cls, tool_name: str) -> str | None:
        """Get the category of a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Category name or None if not found
        """
        return cls.TOOL_CATEGORIES.get(tool_name)

    def clear_cache(self):
        """Clear the tool cache."""
        self._tool_cache.clear()
