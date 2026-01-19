# Adding Tools

## Overview

Tools use LangChain's `@tool` decorator, organized by category (gmail, calendar, slack, web, memory). Each category has a factory function that creates tools with necessary credentials/context.

## Adding a Built-in Tool

### 1. Create Tool File

Create `backend/infrastructure/tools/builtin_mytool.py`:

```python
"""My custom tool implementation."""

from langchain_core.tools import tool


def create_mytool_tools(api_key: str) -> list:
    """Create my tools with credentials.

    Args:
        api_key: API key for the service

    Returns:
        List of tool functions
    """

    @tool
    def my_tool(param1: str, required_param: int) -> str:
        """What this tool does.

        Args:
            param1: First parameter description
            required_param: A required parameter description

        Returns:
            Result description
        """
        # api_key available via closure
        result = f"Processed {required_param} with {param1}"
        return result

    @tool
    def another_tool(query: str) -> str:
        """Another tool in this category.

        Args:
            query: The search query
        """
        return f"Result for {query}"

    # Mark tools that always require HITL
    # another_tool.metadata = {"requires_hitl": True}

    return [my_tool, another_tool]
```

**Key pattern**: Define tools INSIDE the factory function to capture credentials via closure.

### 2. Add Tool Metadata

Edit `backend/config/tools.json`:

```json
{
  "mytool": [
    {"name": "my_tool", "description": "What this tool does", "hitl_recommended": false},
    {"name": "another_tool", "description": "Another tool description", "hitl_recommended": true}
  ]
}
```

Fields:
- `name`: Must match the function name exactly
- `description`: Shown in UI
- `hitl_recommended`: Whether HITL should be enabled by default

### 3. Register in Tool Registry

Edit `backend/infrastructure/tools/registry.py`:

```python
# Add import at top
from backend.infrastructure.tools.builtin_mytool import create_mytool_tools

# In get_pool() function inside create_tools(), add:
elif category == "mytool":
    api_key = os.getenv("MYTOOL_API_KEY")
    if api_key:
        tool_pools[category] = create_mytool_tools(api_key)
```

### 4. Add to Templates (Optional)

```python
# backend/infrastructure/templates/my_template.py
tools=[
    ToolConfig(name="my_tool", source=ToolSource.BUILTIN, hitl_enabled=False),
]
```

## HITL (Human-in-the-Loop)

### Always-HITL (enforced by tool author)

For security-sensitive tools, set metadata after definition:

```python
@tool
def send_message(channel: str, text: str) -> str:
    """Send a message."""
    ...

send_message.metadata = {"requires_hitl": True}
```

This **cannot** be disabled by users.

### User-Configurable HITL

Set `hitl_recommended: true` in tools.json for default-on HITL that users can toggle.

## Best Practices

### Return Strings

```python
import json

@tool
def list_items() -> str:
    """List items."""
    result = {"items": ["a", "b"], "count": 2}
    return json.dumps(result, indent=2)
```

### Handle Errors Gracefully

```python
@tool
def risky_operation(param: str) -> str:
    """Do something risky."""
    try:
        return do_something(param)
    except SomeError as e:
        return f"Error: {e}"
```

## Reference Implementations

- `builtin_slack.py` - Credentials via closure, HITL metadata
- `builtin_web.py` - API key from env, optional tool creation
- `builtin_memory.py` - Agent context (agent_id, memory_fs)
