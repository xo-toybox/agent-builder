"""Tool registry for Agent Builder.

Unified registry for all tools (built-in + MCP + memory + Slack).
"""

from typing import Any
from google.oauth2.credentials import Credentials

from langchain_core.tools import BaseTool

from backend.domain.entities import ToolConfig, ToolSource
from backend.domain.ports import MCPRepository, CredentialStore
from backend.infrastructure.tools.builtin import get_tool_category, get_available_tools
from backend.infrastructure.tools.mcp_client import MCPToolFactory
from backend.infrastructure.tools.builtin_memory import create_memory_tools
from backend.infrastructure.tools.builtin_slack import create_slack_tools
from backend.infrastructure.tools.builtin_web import create_web_tools
from backend.infrastructure.tools.builtin_gmail import create_gmail_tools
from backend.infrastructure.tools.builtin_calendar import create_calendar_tools


class ToolRegistryImpl:
    """Registry for all available tools (built-in + MCP + memory + Slack).

    Implements the ToolFactory protocol from the domain layer
    and provides a unified interface for tool management.

    v0.0.3: Memory and Slack tools added.
    """

    def __init__(
        self,
        mcp_repo: MCPRepository,
        memory_fs=None,
        credential_store: CredentialStore | None = None,
    ):
        """Initialize the tool registry.

        Args:
            mcp_repo: Repository for MCP server configurations
            memory_fs: Virtual filesystem for memory (v0.0.3, optional)
            credential_store: Store for credentials (v0.0.3, for Slack)
        """
        self.mcp_repo = mcp_repo
        self.memory_fs = memory_fs
        self.credential_store = credential_store
        self.mcp_factory = MCPToolFactory()
        # Cache for created tools (by credentials id)
        self._google_tools_cache: dict[int, list] = {}

    async def create_tools(
        self,
        configs: list[ToolConfig],
        credentials: Credentials | None,
        agent_id: str | None = None,
        memory_approval_required: bool = True,
    ) -> list[Any]:
        """Create executable tools from configurations.

        Args:
            configs: List of tool configurations
            credentials: Google OAuth credentials for built-in tools (optional)
            agent_id: Agent ID for memory tools (v0.0.3)
            memory_approval_required: Whether write_memory requires HITL approval (v0.0.3)

        Returns:
            List of LangChain-compatible tools
        """
        tools = []

        # v0.0.3: Always add memory tools if memory_fs is available
        if self.memory_fs is not None and agent_id is not None:
            memory_tools = create_memory_tools(
                self.memory_fs, agent_id, memory_approval_required
            )
            tools.extend(memory_tools)

        # v0.0.3: Check for Slack credentials and global settings
        slack_token = None
        tavily_api_key = None
        if self.credential_store:
            slack_creds = await self.credential_store.get("slack")
            if slack_creds:
                slack_token = slack_creds.get("token")
            global_settings = await self.credential_store.get("global_settings")
            if global_settings:
                tavily_api_key = global_settings.get("tavily_api_key") or None

        # Build tool pools by category (lazy, only if needed)
        tool_pools: dict[str, list[Any]] = {}

        def get_pool(category: str) -> list[Any]:
            if category in tool_pools:
                return tool_pools[category]
            if category == "slack" and slack_token:
                tool_pools[category] = create_slack_tools(slack_token)
            elif category == "web":
                tool_pools[category] = create_web_tools(tavily_api_key)
            elif category in ("gmail", "calendar") and credentials:
                # Use stable cache key based on credentials (refresh_token or token)
                cache_key = credentials.refresh_token or credentials.token
                if cache_key:
                    if cache_key not in self._google_tools_cache:
                        self._google_tools_cache[cache_key] = (
                            create_gmail_tools(credentials) + create_calendar_tools(credentials)
                        )
                    cached = self._google_tools_cache[cache_key]
                else:
                    # No stable key available; create without caching
                    cached = create_gmail_tools(credentials) + create_calendar_tools(credentials)
                tool_pools["gmail"] = [t for t in cached if get_tool_category(t.name) == "gmail"]
                tool_pools["calendar"] = [t for t in cached if get_tool_category(t.name) == "calendar"]
            return tool_pools.get(category, [])

        for config in configs:
            if not config.enabled:
                continue

            if config.source == ToolSource.BUILTIN:
                category = get_tool_category(config.name)
                if category:
                    pool = get_pool(category)
                    tool = next((t for t in pool if t.name == config.name), None)
                    if tool:
                        tools.append(tool)

            elif config.source == ToolSource.MCP and config.server_id:
                mcp_tools = await self._get_mcp_tools(config.server_id)
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
        return get_available_tools()

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

    def get_hitl_tools(
        self, tools: list[BaseTool], configs: list[ToolConfig]
    ) -> list[str]:
        """Get list of tool names that require HITL approval.

        HITL tools come from two sources:
        1. Tool metadata: tools with metadata["requires_hitl"] = True
           (enforced by tool author, cannot be disabled)
        2. Tool config: tools with hitl_enabled=True in ToolConfig
           (user-configurable per agent)

        Args:
            tools: List of created LangChain tools
            configs: List of tool configurations

        Returns:
            List of tool names requiring HITL approval
        """
        hitl_tools: list[str] = []

        # 1. Introspect tool metadata for always-HITL tools
        for tool in tools:
            if hasattr(tool, "metadata") and tool.metadata:
                if tool.metadata.get("requires_hitl"):
                    hitl_tools.append(tool.name)

        # 2. Add user-configured HITL tools from configs
        for config in configs:
            if not config.hitl_enabled:
                continue
            if config.source == ToolSource.MCP and config.server_id:
                # MCP tools are prefixed with mcp_{server_id}_{tool_name}
                tool_name = f"mcp_{config.server_id}_{config.name}"
            else:
                # Built-in tools use their plain name
                tool_name = config.name

            # Avoid duplicates (tool might already be in list from metadata)
            if tool_name not in hitl_tools:
                hitl_tools.append(tool_name)

        return hitl_tools

    async def cleanup(self):
        """Clean up resources (disconnect MCP servers, clear caches)."""
        await self.mcp_factory.disconnect_all()
        self._google_tools_cache.clear()
