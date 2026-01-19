# MCP Integration

Agent Builder supports [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers for extending tool capabilities.

## Configuration

### 1. Add MCP Server via API

```bash
POST /api/v1/tools/mcp
Content-Type: application/json

{
  "name": "File System",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
  "env": {}
}
```

Or via the UI: Agent Editor → Toolbox → "Add MCP Server"

### 2. Server Lifecycle

MCP servers are managed by `MCPToolFactory`:

```python
from backend.infrastructure.tools.mcp_client import MCPToolFactory

factory = MCPToolFactory()

# Create tools from MCP server
tools = await factory.create_tools(server_config)

# Tools are standard LangChain tools and can be used directly
```

The server process is started automatically when tools are created and stopped when the agent session ends.

## Using MCP Tools in Agents

### Via UI

1. Open agent editor
2. Go to **Toolbox** tab
3. MCP tools appear under their server name
4. Enable desired tools

### Via API

```json
POST /api/v1/agents
{
  "name": "Agent with MCP",
  "tools": [
    {"name": "read_file", "source": "mcp", "mcp_server_id": "filesystem"},
    {"name": "list_directory", "source": "mcp", "mcp_server_id": "filesystem"}
  ]
}
```

## Available MCP Servers

Community servers: https://github.com/modelcontextprotocol/servers

Popular options:
- `@modelcontextprotocol/server-filesystem` - File operations
- `@modelcontextprotocol/server-postgres` - PostgreSQL queries
- `@modelcontextprotocol/server-sqlite` - SQLite queries
- `@modelcontextprotocol/server-github` - GitHub API
- `@modelcontextprotocol/server-slack` - Slack API

## Creating Custom MCP Servers

### Python Server

```python
# my_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="my_custom_tool",
            description="Does something custom",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_custom_tool":
        return CallToolResult(
            content=[TextContent(type="text", text=f"Result: {arguments['input']}")]
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

### Register Custom Server

```json
{
  "id": "my-custom",
  "name": "My Custom Tools",
  "command": "python",
  "args": ["my_server.py"],
  "enabled": true
}
```

## Troubleshooting

### Server won't start

1. Check command exists: `which npx` or `which python`
2. Check server package installed: `npx -y @modelcontextprotocol/server-filesystem --help`
3. Check logs in backend terminal

### Tools not appearing

1. Verify server is enabled in config
2. Check `GET /api/v1/tools/mcp` returns the server
3. Restart backend after config changes

### Tool execution fails

1. Check MCP server logs
2. Verify tool arguments match schema
3. Check permissions (file access, database connections)
