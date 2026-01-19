"""Tool management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.domain.entities import MCPServerConfig
from backend.infrastructure.tools.builtin import get_available_tools
from backend.api.dependencies import get_mcp_repo, get_tool_registry

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolInfo(BaseModel):
    """Tool information."""
    name: str
    description: str
    category: str
    hitl_recommended: bool = False


class MCPServerCreate(BaseModel):
    """Request to register an MCP server."""
    id: str
    name: str
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class MCPServerInfo(BaseModel):
    """MCP server information."""
    id: str
    name: str
    command: str
    enabled: bool
    tools: list[dict] = []


@router.get("/builtin", response_model=dict)
async def list_builtin_tools():
    """List all available built-in tools by category."""
    return get_available_tools()


@router.get("/mcp", response_model=list[MCPServerInfo])
async def list_mcp_servers(
    mcp_repo=Depends(get_mcp_repo),
    tool_registry=Depends(get_tool_registry)
):
    """List all registered MCP servers with their tools."""
    servers = await mcp_repo.list_all()
    result = []

    for server in servers:
        tools = []
        if server.enabled:
            try:
                mcp_tools = await tool_registry._get_mcp_tools(server.id)
                tools = [
                    {"name": t.name, "description": t.__doc__ or ""}
                    for t in mcp_tools
                ]
            except Exception:
                pass  # Server offline or error

        result.append(MCPServerInfo(
            id=server.id,
            name=server.name,
            command=server.command,
            enabled=server.enabled,
            tools=tools,
        ))

    return result


@router.post("/mcp")
async def register_mcp_server(
    body: MCPServerCreate,
    mcp_repo=Depends(get_mcp_repo)
):
    """Register a new MCP server."""
    server = MCPServerConfig(
        id=body.id,
        name=body.name,
        command=body.command,
        args=body.args,
        env=body.env,
        enabled=True,
    )
    await mcp_repo.save(server)
    return {"success": True, "id": server.id}


@router.delete("/mcp/{server_id}")
async def delete_mcp_server(
    server_id: str,
    mcp_repo=Depends(get_mcp_repo),
    tool_registry=Depends(get_tool_registry)
):
    """Delete an MCP server registration."""
    server = await mcp_repo.get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    # Disconnect if connected
    await tool_registry.mcp_factory.disconnect(server_id)

    await mcp_repo.delete(server_id)
    return {"success": True}


@router.post("/mcp/{server_id}/toggle")
async def toggle_mcp_server(
    server_id: str,
    mcp_repo=Depends(get_mcp_repo),
    tool_registry=Depends(get_tool_registry)
):
    """Enable/disable an MCP server."""
    server = await mcp_repo.get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    server.enabled = not server.enabled
    await mcp_repo.save(server)

    if not server.enabled:
        # Disconnect if disabling
        await tool_registry.mcp_factory.disconnect(server_id)

    return {"success": True, "enabled": server.enabled}
