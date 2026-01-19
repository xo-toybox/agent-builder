"""Builder Wizard - Meta-agent for creating agents through conversation.

The Builder Wizard is a special agent that helps users create other agents
through natural language conversation.

v0.0.3: Conversation state persisted to SQLite. Replaced LangChain with raw Anthropic SDK.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import anthropic
from anthropic import beta_tool

from backend.config import settings

# Load config files
_CONFIG_DIR = Path(__file__).parent.parent / "config"
_TOOLS_CATALOG = json.loads((_CONFIG_DIR / "tools.json").read_text())
_TEMPLATES_CATALOG = json.loads((_CONFIG_DIR / "templates.json").read_text())
_WIZARD_PROMPT = (_CONFIG_DIR / "wizard_prompt.md").read_text()
from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    TriggerConfig,
    ToolSource,
    TriggerType,
)
from backend.domain.ports import AgentRepository


# Message type alias
Message = dict[str, Any]


# --- Tool definitions using Anthropic SDK's @beta_tool decorator ---
# Schema is auto-generated from function signature and docstring

@beta_tool
def list_available_tools() -> str:
    """List all available built-in tools that can be added to an agent.

    Returns:
        JSON object with tools grouped by category.
    """
    return json.dumps(_TOOLS_CATALOG, indent=2)


@beta_tool
def list_templates() -> str:
    """List available agent templates that can be cloned as starting points.

    Returns:
        JSON array of template objects.
    """
    return json.dumps(_TEMPLATES_CATALOG, indent=2)


# Note: create_agent tool is created per-instance in BuilderWizard.__init__
# because it needs access to agent_repo


class WizardConversationRepositoryProtocol(Protocol):
    """Protocol for wizard conversation persistence."""

    async def save_message(self, thread_id: str, message: Message) -> str: ...
    async def load_conversation(self, thread_id: str) -> list[Message]: ...
    async def clear_conversation(self, thread_id: str) -> None: ...
    async def exists(self, thread_id: str) -> bool: ...


class BuilderWizard:
    """Chat-based wizard for creating agents via conversation.

    This is a meta-agent that helps users define and create other agents
    through natural language interaction.

    v0.0.3: Conversation state persisted to SQLite. Uses raw Anthropic SDK.
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        conversation_repo: WizardConversationRepositoryProtocol | None = None,
    ):
        """Initialize the builder wizard.

        Args:
            agent_repo: Repository for persisting created agents
            conversation_repo: Repository for persisting conversation state (v0.0.3)
        """
        self.agent_repo = agent_repo
        self.conversation_repo = conversation_repo
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
        # In-memory cache, backed by database when conversation_repo is available
        self._conversation_cache: dict[str, list[Message]] = {}

        # Create create_agent tool with repo access
        @beta_tool
        async def create_agent(
            name: str,
            description: str,
            system_prompt: str,
            tool_names: list[str],
            hitl_tool_names: list[str] | None = None,
        ) -> str:
            """Create an agent from the gathered specification. Call this when you have enough information.

            Args:
                name: Name of the agent (e.g., Daily Digest Agent)
                description: Brief description of what the agent does
                system_prompt: System prompt with instructions for the agent
                tool_names: List of tool names (e.g., list_emails, get_email)
                hitl_tool_names: Tools requiring human approval
            """
            hitl_tools = set(hitl_tool_names or [])
            tools = [
                ToolConfig(
                    name=t,
                    source=ToolSource.BUILTIN,
                    hitl_enabled=(t in hitl_tools),
                )
                for t in tool_names
            ]

            now = datetime.utcnow()
            agent_def = AgentDefinition(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                system_prompt=system_prompt,
                tools=tools,
                triggers=[],
                created_at=now,
                updated_at=now,
            )

            await agent_repo.save(agent_def)
            return f"Created agent '{name}' with ID: {agent_def.id}"

        self._create_agent = create_agent
        self._tool_schemas = [
            create_agent.to_dict(),
            list_available_tools.to_dict(),
            list_templates.to_dict(),
        ]

    async def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool by name and return result."""
        if name == "create_agent":
            return await self._create_agent(**args)
        elif name == "list_available_tools":
            return list_available_tools()
        elif name == "list_templates":
            return list_templates()
        else:
            return f"Unknown tool: {name}"

    async def _get_conversation(self, thread_id: str) -> list[Message]:
        """Get conversation messages, loading from database if needed."""
        if thread_id not in self._conversation_cache:
            if self.conversation_repo:
                self._conversation_cache[thread_id] = await self.conversation_repo.load_conversation(thread_id)
            else:
                self._conversation_cache[thread_id] = []
        return self._conversation_cache[thread_id]

    async def _add_message(self, thread_id: str, message: Message) -> None:
        """Add message to conversation, persisting to database."""
        conversation = await self._get_conversation(thread_id)
        conversation.append(message)

        if self.conversation_repo:
            await self.conversation_repo.save_message(thread_id, message)

    def _build_messages(self, conversation: list[Message]) -> list[dict]:
        """Build messages list for Anthropic API from conversation history."""
        messages = []
        for msg in conversation:
            role = msg["role"]
            content = msg.get("content", "")

            if role == "user":
                messages.append({"role": "user", "content": content})
            elif role == "assistant":
                # Handle assistant messages with potential tool_use blocks
                if "tool_calls" in msg and msg["tool_calls"]:
                    # Build content with text and tool_use blocks
                    content_blocks = []
                    if content:
                        content_blocks.append({"type": "text", "text": content})
                    for tc in msg["tool_calls"]:
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["name"],
                            "input": tc["args"],
                        })
                    messages.append({"role": "assistant", "content": content_blocks})
                else:
                    messages.append({"role": "assistant", "content": content})
            elif role == "tool":
                # Tool results need to be in a user message with tool_result blocks
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": content,
                    }]
                })

        return messages

    def _extract_text(self, content: list | str) -> str:
        """Extract text from response content."""
        if isinstance(content, str):
            return content
        text_parts = []
        for block in content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            elif isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return "".join(text_parts)

    def _extract_tool_calls(self, content: list) -> list[dict]:
        """Extract tool calls from response content."""
        tool_calls = []
        for block in content:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "args": block.input,
                })
            elif isinstance(block, dict) and block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "name": block["name"],
                    "args": block["input"],
                })
        return tool_calls

    async def chat(self, thread_id: str, user_message: str) -> str:
        """Process user message and return wizard response.

        Args:
            thread_id: Conversation thread ID
            user_message: User's message

        Returns:
            Assistant's response
        """
        # Add user message to history
        await self._add_message(thread_id, {"role": "user", "content": user_message})

        # Build messages for API
        conversation = await self._get_conversation(thread_id)
        messages = self._build_messages(conversation)

        # Get model response
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=_WIZARD_PROMPT,
            tools=self._tool_schemas,
            messages=messages,
        )

        # Handle tool calls
        if response.stop_reason == "tool_use":
            tool_calls = self._extract_tool_calls(response.content)
            text_content = self._extract_text(response.content)

            # Add assistant message with tool calls
            await self._add_message(thread_id, {
                "role": "assistant",
                "content": text_content,
                "tool_calls": tool_calls,
            })

            # Execute tools and add results
            for tc in tool_calls:
                result = await self._execute_tool(tc["name"], tc["args"])
                await self._add_message(thread_id, {
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc["id"],
                })

            # Get follow-up response
            conversation = await self._get_conversation(thread_id)
            messages = self._build_messages(conversation)
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=_WIZARD_PROMPT,
                messages=messages,
            )

        # Extract and save response
        content = self._extract_text(response.content)
        await self._add_message(thread_id, {"role": "assistant", "content": content})

        return content

    async def stream_chat(self, thread_id: str, user_message: str):
        """Stream chat response for real-time UI updates.

        Args:
            thread_id: Conversation thread ID
            user_message: User's message

        Yields:
            Chunks of the response
        """
        await self._add_message(thread_id, {"role": "user", "content": user_message})

        conversation = await self._get_conversation(thread_id)
        messages = self._build_messages(conversation)

        # First call - check for tool use (can't stream tool calls reliably)
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=_WIZARD_PROMPT,
            tools=self._tool_schemas,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_calls = self._extract_tool_calls(response.content)
            text_content = self._extract_text(response.content)

            # Add assistant message with tool calls
            await self._add_message(thread_id, {
                "role": "assistant",
                "content": text_content,
                "tool_calls": tool_calls,
            })

            # Execute tools and yield results
            for tc in tool_calls:
                yield {"type": "tool_call", "name": tc["name"], "args": tc["args"]}

                result = await self._execute_tool(tc["name"], tc["args"])
                yield {"type": "tool_result", "name": tc["name"], "result": result}

                await self._add_message(thread_id, {
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc["id"],
                })

            # Stream follow-up response
            conversation = await self._get_conversation(thread_id)
            messages = self._build_messages(conversation)

            full_content = ""
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=_WIZARD_PROMPT,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_content += text
                    yield {"type": "token", "content": text}

            await self._add_message(thread_id, {"role": "assistant", "content": full_content})
        else:
            # No tool calls - yield the response
            content = self._extract_text(response.content)
            if content:
                yield {"type": "token", "content": content}
            await self._add_message(thread_id, {"role": "assistant", "content": content or ""})

        yield {"type": "complete"}

    async def clear_conversation(self, thread_id: str):
        """Clear conversation history for a thread."""
        self._conversation_cache.pop(thread_id, None)
        if self.conversation_repo:
            await self.conversation_repo.clear_conversation(thread_id)
