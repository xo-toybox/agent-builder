"""Built-in tool metadata for Agent Builder.

Loads tool categories and metadata from config/tools.json.
"""

import json
from pathlib import Path

_config_path = Path(__file__).parent.parent.parent / "config" / "tools.json"
_tools_config: dict[str, list[dict]] | None = None


def _load_config() -> dict[str, list[dict]]:
    global _tools_config
    if _tools_config is None:
        with open(_config_path) as f:
            _tools_config = json.load(f)
    return _tools_config


def get_available_tools() -> dict[str, list[dict]]:
    """Get available tools metadata by category."""
    return _load_config()


def get_tool_category(tool_name: str) -> str | None:
    """Get the category for a tool name."""
    for category, tools in _load_config().items():
        if any(t["name"] == tool_name for t in tools):
            return category
    return None


