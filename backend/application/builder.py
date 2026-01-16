"""Builder Wizard - Meta-agent for creating agents through conversation.

The Builder Wizard is a special agent that helps users create other agents
through natural language conversation.
"""

import uuid
from datetime import datetime
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from pydantic import BaseModel, Field

from backend.config import settings
from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    TriggerConfig,
    ToolSource,
    TriggerType,
)
from backend.domain.ports import AgentRepository


BUILDER_SYSTEM_PROMPT = """You are an agent builder assistant. You help users create AI agents through conversation.

Your job is to:
1. Understand what the user wants their agent to do
2. Ask clarifying questions to gather requirements
3. Suggest appropriate tools, triggers, and configurations
4. Use your tools to create the agent when ready

## Available Built-in Tools

### Gmail Tools
- list_emails: List emails from inbox with filters
- get_email: Get full email content by ID
- search_emails: Search emails using Gmail query syntax
- draft_reply: Create draft reply (requires HITL approval)
- send_email: Send email (requires HITL approval)
- label_email: Modify email labels

### Calendar Tools
- list_events: List calendar events for a date range
- get_event: Get event details
- create_event: Create a new calendar event (requires HITL approval)

### Web Tools
- web_search: Search the web for information
- fetch_url: Fetch and extract content from a URL

### Notes Tools
- create_note: Create a new note or document
- search_notes: Search through existing notes
- append_note: Append content to an existing note

### Slack Tools
- send_slack_message: Send a message to a Slack channel (requires HITL approval)
- list_slack_channels: List available Slack channels

## Available Triggers
- email_polling: Poll for new emails at an interval
- webhook: Trigger via HTTP webhook
- scheduled: Run on a schedule

## HITL (Human-in-the-Loop) Approval
You can mark tools as requiring human approval before execution. This is recommended for:
- Actions that send emails or messages
- Actions that create calendar events
- Actions that modify or delete data
- Any potentially destructive operations

## Creating an Agent

When you have gathered enough information, use the create_agent tool with:
- name: A descriptive name for the agent
- description: What the agent does
- system_prompt: Instructions for the agent's behavior
- tools: List of tools the agent should have access to
- triggers: Optional triggers to activate the agent

Be conversational and guide users step-by-step. Ask questions to understand:
- What problem they're trying to solve
- What actions the agent should take
- When the agent should be triggered
- What level of human oversight is needed

Suggest creative agent ideas based on the available tools. Examples:
- Research assistant: web_search + fetch_url + create_note
- Newsletter curator: list_emails + search_emails + create_note
- Meeting prep agent: list_events + get_event + search_emails
- Daily briefing: list_events + list_emails + send_slack_message"""


class ToolSpec(BaseModel):
    """Specification for a tool to add to an agent."""
    name: str = Field(description="Tool name (e.g., 'list_emails', 'send_email')")
    hitl: bool = Field(default=False, description="Whether this tool requires human approval")


class TriggerSpec(BaseModel):
    """Specification for a trigger to add to an agent."""
    type: str = Field(description="Trigger type: 'email_polling', 'webhook', or 'scheduled'")
    enabled: bool = Field(default=False, description="Whether the trigger should be enabled initially")
    config: dict = Field(default_factory=dict, description="Trigger configuration (e.g., interval_seconds)")


class AgentSpec(BaseModel):
    """Complete specification for creating an agent."""
    name: str = Field(description="Name of the agent")
    description: str = Field(description="Brief description of what the agent does")
    system_prompt: str = Field(description="System prompt with instructions for the agent")
    tools: list[ToolSpec] = Field(description="List of tools for the agent")
    triggers: list[TriggerSpec] = Field(default_factory=list, description="Optional triggers")


class BuilderWizard:
    """Chat-based wizard for creating agents via conversation.

    This is a meta-agent that helps users define and create other agents
    through natural language interaction.
    """

    def __init__(self, agent_repo: AgentRepository):
        """Initialize the builder wizard.

        Args:
            agent_repo: Repository for persisting created agents
        """
        self.agent_repo = agent_repo
        self.model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
        )
        self.conversation_state: dict[str, list] = {}  # thread_id -> messages
        self._setup_tools()

    def _setup_tools(self):
        """Set up the builder's tools."""

        @tool
        async def create_agent(
            name: str,
            description: str,
            system_prompt: str,
            tool_names: list[str],
            hitl_tool_names: list[str] | None = None,
        ) -> str:
            """Create an agent from the gathered specification.

            Call this when you have collected all necessary information about
            the agent the user wants to create.

            Args:
                name: Name of the agent (e.g., "Daily Digest Agent")
                description: Brief description of what the agent does
                system_prompt: System prompt with instructions for the agent
                tool_names: List of tool names (e.g., ["list_emails", "get_email"])
                hitl_tool_names: Optional list of tools requiring human approval
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
            agent = AgentDefinition(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                system_prompt=system_prompt,
                tools=tools,
                triggers=[],
                created_at=now,
                updated_at=now,
            )

            await self.agent_repo.save(agent)
            return f"✅ Created agent '{name}' with ID: {agent.id}"

        # Bind create_agent to self for access to agent_repo
        self._create_agent = create_agent

        @tool
        def list_available_tools() -> dict:
            """List all available built-in tools that can be added to an agent.

            Use this to show the user what tools are available.
            """
            return {
                "gmail": [
                    {"name": "list_emails", "description": "List emails from inbox with filters", "hitl_recommended": False},
                    {"name": "get_email", "description": "Get full email content by ID", "hitl_recommended": False},
                    {"name": "search_emails", "description": "Search emails using Gmail query syntax", "hitl_recommended": False},
                    {"name": "draft_reply", "description": "Create draft reply to an email", "hitl_recommended": True},
                    {"name": "send_email", "description": "Send an email", "hitl_recommended": True},
                    {"name": "label_email", "description": "Modify email labels (mark read, archive, etc.)", "hitl_recommended": False},
                ],
                "calendar": [
                    {"name": "list_events", "description": "List calendar events for a date range", "hitl_recommended": False},
                    {"name": "get_event", "description": "Get calendar event details", "hitl_recommended": False},
                    {"name": "create_event", "description": "Create a new calendar event", "hitl_recommended": True},
                ],
                "web": [
                    {"name": "web_search", "description": "Search the web for information", "hitl_recommended": False},
                    {"name": "fetch_url", "description": "Fetch and extract content from a URL", "hitl_recommended": False},
                ],
                "notes": [
                    {"name": "create_note", "description": "Create a new note or document", "hitl_recommended": False},
                    {"name": "search_notes", "description": "Search through existing notes", "hitl_recommended": False},
                    {"name": "append_note", "description": "Append content to an existing note", "hitl_recommended": False},
                ],
                "slack": [
                    {"name": "send_slack_message", "description": "Send a message to a Slack channel", "hitl_recommended": True},
                    {"name": "list_slack_channels", "description": "List available Slack channels", "hitl_recommended": False},
                ],
            }

        @tool
        def list_templates() -> list[dict]:
            """List available agent templates that can be cloned.

            Use this to suggest templates to users who want a starting point.
            """
            return [
                {
                    "id": "email_assistant_template",
                    "name": "Email Assistant",
                    "description": "An intelligent email assistant that triages emails, drafts responses, and integrates with calendar.",
                    "tools": ["list_emails", "get_email", "search_emails", "draft_reply", "send_email", "label_email"],
                    "triggers": ["email_polling"],
                },
            ]

        self.tools = [self._create_agent, list_available_tools, list_templates]

    async def chat(self, thread_id: str, user_message: str) -> str:
        """Process user message and return wizard response.

        Args:
            thread_id: Conversation thread ID
            user_message: User's message

        Returns:
            Assistant's response
        """
        if thread_id not in self.conversation_state:
            self.conversation_state[thread_id] = []

        # Add user message to history
        self.conversation_state[thread_id].append(HumanMessage(content=user_message))

        # Build messages for model
        messages = [
            {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
            *[self._message_to_dict(m) for m in self.conversation_state[thread_id]]
        ]

        # Get model response
        response = await self.model.bind_tools(self.tools).ainvoke(messages)

        # Handle tool calls
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # Find and execute tool
                tool_fn = next((t for t in self.tools if t.name == tool_call["name"]), None)
                if tool_fn:
                    try:
                        # Check if tool is async
                        if tool_call["name"] == "create_agent":
                            result = await tool_fn.ainvoke(tool_call["args"])
                        else:
                            result = tool_fn.invoke(tool_call["args"])
                    except Exception as e:
                        result = f"Error: {str(e)}"

                    # Add tool message to history
                    self.conversation_state[thread_id].append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call["id"],
                        )
                    )

            # Get follow-up response after tool execution
            messages = [
                {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
                *[self._message_to_dict(m) for m in self.conversation_state[thread_id]]
            ]
            response = await self.model.ainvoke(messages)

        # Add assistant response to history
        self.conversation_state[thread_id].append(AIMessage(content=response.content))

        # Extract text content
        return self._extract_content(response.content)

    async def stream_chat(self, thread_id: str, user_message: str):
        """Stream chat response for real-time UI updates.

        Args:
            thread_id: Conversation thread ID
            user_message: User's message

        Yields:
            Chunks of the response
        """
        if thread_id not in self.conversation_state:
            self.conversation_state[thread_id] = []

        self.conversation_state[thread_id].append(HumanMessage(content=user_message))

        messages = [
            {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
            *[self._message_to_dict(m) for m in self.conversation_state[thread_id]]
        ]

        # Use ainvoke for initial response (streaming breaks tool call args)
        response = await self.model.bind_tools(self.tools).ainvoke(messages)

        # Handle tool calls if present
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Add the AI response with tool_calls to history BEFORE tool results
            self.conversation_state[thread_id].append(response)

            for tool_call in response.tool_calls:
                yield {"type": "tool_call", "name": tool_call["name"], "args": tool_call["args"]}

                tool_fn = next((t for t in self.tools if t.name == tool_call["name"]), None)
                if tool_fn:
                    try:
                        if tool_call["name"] == "create_agent":
                            result = await tool_fn.ainvoke(tool_call["args"])
                        else:
                            result = tool_fn.invoke(tool_call["args"])
                    except Exception as e:
                        result = f"Error: {str(e)}"

                    yield {"type": "tool_result", "name": tool_call["name"], "result": result}

                    self.conversation_state[thread_id].append(
                        ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                    )

            # Stream follow-up response after tool execution
            messages = [
                {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
                *[self._message_to_dict(m) for m in self.conversation_state[thread_id]]
            ]
            full_content = ""
            async for chunk in self.model.astream(messages):
                chunk_text = self._extract_content(chunk.content)
                if chunk_text:
                    full_content += chunk_text
                    yield {"type": "token", "content": chunk_text}

            if full_content:
                self.conversation_state[thread_id].append(AIMessage(content=full_content))
        else:
            # No tool calls - yield the complete response
            content = self._extract_content(response.content)
            if content:
                yield {"type": "token", "content": content}
                self.conversation_state[thread_id].append(AIMessage(content=content))

        yield {"type": "complete"}

    def _message_to_dict(self, msg: Any) -> dict:
        """Convert a LangChain message to dict format."""
        if isinstance(msg, HumanMessage):
            return {"role": "user", "content": msg.content}
        elif isinstance(msg, AIMessage):
            result = {"role": "assistant", "content": msg.content or ""}
            # Include tool_calls if present (required for proper message sequencing)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                import json
                result["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"]) if isinstance(tc["args"], dict) else tc["args"],
                        },
                    }
                    for tc in msg.tool_calls
                ]
            return result
        elif isinstance(msg, ToolMessage):
            return {"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id}
        return {"role": "user", "content": str(msg)}

    def _extract_content(self, content: Any) -> str:
        """Extract text content from various formats."""
        if isinstance(content, list):
            parts = []
            for block in content:
                if hasattr(block, "text"):
                    parts.append(block.text)
                elif isinstance(block, dict) and "text" in block:
                    parts.append(block["text"])
            return "".join(parts)
        elif isinstance(content, str):
            return content
        return str(content)

    def clear_conversation(self, thread_id: str):
        """Clear conversation history for a thread.

        Args:
            thread_id: Thread to clear
        """
        self.conversation_state.pop(thread_id, None)
