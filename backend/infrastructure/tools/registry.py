"""Tool registry for Agent Builder.

Unified registry for all tools (built-in + MCP).
"""

from typing import Any
from google.oauth2.credentials import Credentials

from backend.domain.entities import ToolConfig, ToolSource
from backend.domain.ports import MCPRepository
from backend.infrastructure.tools.builtin import BuiltinToolFactory
from backend.infrastructure.tools.mcp_client import MCPToolFactory


class ToolRegistryImpl:
    """Registry for all available tools (built-in + MCP).

    Implements the ToolFactory protocol from the domain layer
    and provides a unified interface for tool management.
    """

    def __init__(self, mcp_repo: MCPRepository):
        """Initialize the tool registry.

        Args:
            mcp_repo: Repository for MCP server configurations
        """
        self.mcp_repo = mcp_repo
        self.builtin_factory = BuiltinToolFactory()
        self.mcp_factory = MCPToolFactory()

    async def create_tools(
        self,
        configs: list[ToolConfig],
        credentials: Credentials | None
    ) -> list[Any]:
        """Create executable tools from configurations.

        Args:
            configs: List of tool configurations
            credentials: Google OAuth credentials for built-in tools (optional)

        Returns:
            List of LangChain-compatible tools
        """
        tools = []

        for config in configs:
            if not config.enabled:
                continue

            if config.source == ToolSource.BUILTIN:
                # Skip built-in tools if no credentials available
                if credentials is None:
                    continue
                tool = self.builtin_factory.get_tool_by_name(config.name, credentials)
                if tool:
                    tools.append(tool)

            elif config.source == ToolSource.MCP:
                if config.server_id:
                    mcp_tools = await self._get_mcp_tools(config.server_id)
                    # Find the specific tool by name
                    expected_name = f"mcp_{config.server_id}_{config.name}"
                    tool = next((t for t in mcp_tools if t.name == expected_name), None)
                    if tool:
                        tools.append(tool)

        return tools

    async def _get_mcp_tools(self, server_id: str) -> list[Any]:
        """Get tools from an MCP server.

        Args:
            server_id: MCP server ID

        Returns:
            List of MCP tools
        """
        # Check if already connected
        if self.mcp_factory.is_connected(server_id):
            return self.mcp_factory._tool_cache.get(server_id, [])

        # Get server config and connect
        server = await self.mcp_repo.get(server_id)
        if server:
            return await self.mcp_factory.create_tools(server)

        return []

    def list_available_builtin(self) -> dict[str, list[dict]]:
        """List all available built-in tools by category.

        Returns:
            Dict mapping category to list of tool metadata
        """
        return BuiltinToolFactory.list_available()

    async def list_available_mcp(self) -> dict[str, list[dict]]:
        """List all available MCP tools by server.

        Returns:
            Dict mapping server ID to list of tool metadata
        """
        servers = await self.mcp_repo.list_all()
        result = {}

        for server in servers:
            if server.enabled:
                try:
                    tools = await self.mcp_factory.create_tools(server)
                    result[server.id] = [
                        {"name": t.name, "description": t.__doc__ or ""}
                        for t in tools
                    ]
                except Exception:
                    # Skip servers that fail to connect
                    result[server.id] = []

        return result

    def get_hitl_tools(self, configs: list[ToolConfig]) -> list[str]:
        """Get list of tool names that require HITL approval.

        Args:
            configs: List of tool configurations

        Returns:
            List of tool names with hitl_enabled=True (with correct prefixes)
        """
        hitl_tools = []
        for config in configs:
            if not config.hitl_enabled:
                continue
            if config.source == ToolSource.MCP and config.server_id:
                # MCP tools are prefixed with mcp_{server_id}_{tool_name}
                hitl_tools.append(f"mcp_{config.server_id}_{config.name}")
            else:
                # Built-in tools use their plain name
                hitl_tools.append(config.name)
        return hitl_tools

    async def cleanup(self):
        """Clean up resources (disconnect MCP servers)."""
        await self.mcp_factory.disconnect_all()
        self.builtin_factory.clear_cache()
