"""MCP (Model Context Protocol) client for Agent Builder.

Connects to MCP servers and creates LangChain-compatible tools
from their tool manifests.
"""

import asyncio
import json
import os
from typing import Any
from langchain_core.tools import tool

from backend.domain.entities import MCPServerConfig
from backend.domain.exceptions import MCPConnectionError


class MCPToolFactory:
    """Creates LangChain tools from MCP server connections.

    Manages connections to MCP servers and wraps their tools
    as LangChain-compatible tools.
    """

    def __init__(self):
        self._connections: dict[str, asyncio.subprocess.Process] = {}
        self._tool_cache: dict[str, list] = {}

    async def create_tools(self, server_config: MCPServerConfig) -> list[Any]:
        """Connect to MCP server and create tools from its manifest.

        Args:
            server_config: MCP server configuration

        Returns:
            List of LangChain-compatible tools

        Raises:
            MCPConnectionError: If connection fails
        """
        # Check cache first
        if server_config.id in self._tool_cache:
            return self._tool_cache[server_config.id]

        try:
            # Start MCP server process
            process = await asyncio.create_subprocess_exec(
                server_config.command,
                *server_config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(os.environ), **server_config.env},
            )

            self._connections[server_config.id] = process

            # Request tools/list
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }

            process.stdin.write(json.dumps(request).encode() + b"\n")
            await process.stdin.drain()

            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                raise MCPConnectionError(
                    server_config.id,
                    "Timeout waiting for tools/list response"
                )

            if not response_line:
                raise MCPConnectionError(
                    server_config.id,
                    "Empty response from server"
                )

            response = json.loads(response_line)

            if "error" in response:
                raise MCPConnectionError(
                    server_config.id,
                    response["error"].get("message", "Unknown error")
                )

            # Create tools from manifest
            tools = []
            for tool_spec in response.get("result", {}).get("tools", []):
                wrapped_tool = self._create_tool(server_config.id, tool_spec, process)
                tools.append(wrapped_tool)

            self._tool_cache[server_config.id] = tools
            return tools

        except (OSError, json.JSONDecodeError) as e:
            raise MCPConnectionError(server_config.id, str(e))

    def _create_tool(
        self,
        server_id: str,
        tool_spec: dict,
        process: asyncio.subprocess.Process
    ) -> Any:
        """Create a LangChain tool from MCP tool specification.

        Args:
            server_id: MCP server ID
            tool_spec: Tool specification from MCP manifest
            process: Running MCP server process

        Returns:
            LangChain-compatible tool
        """
        tool_name = f"mcp_{server_id}_{tool_spec['name']}"
        tool_description = tool_spec.get("description", "MCP tool")

        @tool(name=tool_name)
        async def mcp_tool_wrapper(**kwargs) -> Any:
            """Dynamically generated MCP tool."""
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_spec["name"],
                    "arguments": kwargs
                }
            }

            process.stdin.write(json.dumps(request).encode() + b"\n")
            await process.stdin.drain()

            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                return {"error": "Tool call timed out"}

            if not response_line:
                return {"error": "Empty response from tool"}

            response = json.loads(response_line)

            if "error" in response:
                return {"error": response["error"].get("message", "Unknown error")}

            return response.get("result", {})

        mcp_tool_wrapper.__doc__ = tool_description
        return mcp_tool_wrapper

    async def disconnect(self, server_id: str) -> None:
        """Disconnect from a specific MCP server.

        Args:
            server_id: MCP server ID
        """
        if server_id in self._connections:
            process = self._connections.pop(server_id)
            process.terminate()
            await process.wait()
            self._tool_cache.pop(server_id, None)

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for server_id in list(self._connections.keys()):
            await self.disconnect(server_id)

    def is_connected(self, server_id: str) -> bool:
        """Check if connected to a server.

        Args:
            server_id: MCP server ID

        Returns:
            True if connected
        """
        if server_id not in self._connections:
            return False

        process = self._connections[server_id]
        return process.returncode is None

    def list_connected(self) -> list[str]:
        """List all connected server IDs.

        Returns:
            List of connected server IDs
        """
        return [
            server_id
            for server_id, process in self._connections.items()
            if process.returncode is None
        ]
