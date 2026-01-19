"""Run Agent use case."""

import logging
from typing import Any, AsyncIterator, Protocol

from deepagents import create_deep_agent
from google.oauth2.credentials import Credentials

from backend.application.services.skill_loader import SkillLoader
from backend.domain.entities import AgentDefinition, ToolSource
from backend.domain.exceptions import AgentNotFoundError, CredentialNotFoundError
from backend.domain.ports import AgentRepository, CredentialStore
from backend.infrastructure.persistence.sqlite.checkpointer import get_checkpointer
from backend.infrastructure.tools.registry import ToolRegistryImpl

logger = logging.getLogger(__name__)


class RunAgentUseCase:
    """Use case for running an agent with a message.

    Creates and executes a deepagents instance from an agent definition.
    Uses persistent SQLite checkpointing for conversation state (v0.0.3).
    Uses SkillLoader for progressive disclosure of skills (v0.0.3).
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        credential_store: CredentialStore,
        tool_registry: ToolRegistryImpl,
        skill_loader: SkillLoader | None = None,
    ):
        """Initialize the use case.

        Args:
            agent_repo: Repository for agent definitions
            credential_store: Store for credentials
            tool_registry: Registry for tools
            skill_loader: Service for loading skills with progressive disclosure (v0.0.3)
        """
        self.agent_repo = agent_repo
        self.credential_store = credential_store
        self.tool_registry = tool_registry
        self.skill_loader = skill_loader
        # v0.0.3: Removed agent caching - always create fresh agent with shared checkpointer

    async def get_or_create_agent(
        self,
        agent_id: str,
        thread_id: str,
    ) -> tuple[Any, dict]:
        """Create an agent instance with persistent checkpointing.

        v0.0.3: Always creates fresh agent instance with shared AsyncSqliteSaver.
        This enables conversation resumption across server restarts.

        Args:
            agent_id: Agent definition ID
            thread_id: Conversation thread ID

        Returns:
            Tuple of (agent instance, config dict)

        Raises:
            AgentNotFoundError: If agent not found
            CredentialNotFoundError: If credentials not found
        """
        # Load agent definition
        agent_def = await self.agent_repo.get(agent_id)
        if not agent_def:
            raise AgentNotFoundError(agent_id)

        # Check if agent needs Google credentials (only for Gmail/Calendar tools)
        GOOGLE_TOOLS = {"list_emails", "get_email", "search_emails", "draft_reply",
                        "send_email", "label_email", "list_events", "get_event"}
        needs_google = any(
            t.enabled and t.source == ToolSource.BUILTIN and t.name in GOOGLE_TOOLS
            for t in agent_def.tools
        )

        credentials = None
        if needs_google:
            creds_dict = await self.credential_store.get("google")
            if not creds_dict:
                raise CredentialNotFoundError("google")

            credentials = Credentials(
                token=creds_dict.get("token"),
                refresh_token=creds_dict.get("refresh_token"),
                token_uri=creds_dict.get("token_uri"),
                client_id=creds_dict.get("client_id"),
                client_secret=creds_dict.get("client_secret"),
            )

        # Create tools (v0.0.3: includes memory tools with configurable HITL)
        tools = await self.tool_registry.create_tools(
            agent_def.tools,
            credentials,
            agent_id,
            memory_approval_required=agent_def.memory_approval_required,
        )

        # Get HITL tools - convert list to dict for deepagents interrupt_on
        # Passes tools for metadata introspection + configs for user-configured HITL
        hitl_tools_list = self.tool_registry.get_hitl_tools(tools, agent_def.tools)
        hitl_tools = {name: True for name in hitl_tools_list} if hitl_tools_list else None

        # Get persistent checkpointer (v0.0.3)
        checkpointer = get_checkpointer()

        # v0.0.3: Build system prompt with skills
        system_prompt = await self._build_system_prompt(agent_id, agent_def)

        # Create agent with persistent checkpointer
        agent = create_deep_agent(
            model=agent_def.model,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,
            interrupt_on=hitl_tools,
        )

        config = {"configurable": {"thread_id": thread_id}}
        return agent, config

    async def _build_system_prompt(
        self,
        agent_id: str,
        agent_def: AgentDefinition,
    ) -> str:
        """Build system prompt with skills metadata (progressive disclosure).

        v0.0.3: Uses SkillLoader for progressive disclosure - only metadata
        (name, description) injected into system prompt. Full instructions
        loaded on-demand via memory tools when agent reads skills/{name}.md.

        Args:
            agent_id: Agent ID
            agent_def: Agent definition

        Returns:
            Complete system prompt with skills metadata section
        """
        base_prompt = agent_def.system_prompt

        # Skip if no skill loader
        if self.skill_loader is None:
            return base_prompt

        # Inject metadata only (stage 1 of progressive disclosure)
        skills_section = await self.skill_loader.get_metadata_for_prompt(agent_id)

        return base_prompt + skills_section

    async def run(
        self,
        agent_id: str,
        thread_id: str,
        user_message: str,
    ) -> AsyncIterator[dict]:
        """Run an agent with a user message.

        Args:
            agent_id: Agent definition ID
            thread_id: Conversation thread ID
            user_message: User's message

        Yields:
            Stream events from the agent

        Raises:
            AgentNotFoundError: If agent not found
            CredentialNotFoundError: If credentials not found
        """
        agent, config = await self.get_or_create_agent(agent_id, thread_id)

        input_messages = {"messages": [{"role": "user", "content": user_message}]}

        async for event in agent.astream_events(input_messages, config, version="v2"):
            yield event

    async def resume(
        self,
        agent_id: str,
        thread_id: str,
        tool_call_id: str,
        decision: str,
        edited_args: dict | None = None,
    ) -> AsyncIterator[dict]:
        """Resume an agent after HITL decision.

        Args:
            agent_id: Agent definition ID
            thread_id: Conversation thread ID
            tool_call_id: Tool call ID being decided
            decision: Decision (approve, reject, edit)
            edited_args: Edited arguments if decision is edit

        Yields:
            Stream events from the agent
        """
        agent, config = await self.get_or_create_agent(agent_id, thread_id)

        if decision == "approve":
            # Resume with no changes
            async for event in agent.astream_events(None, config, version="v2"):
                yield event

        elif decision == "reject":
            # Update state to remove pending tool call
            state = agent.get_state(config)
            messages = state.values.get("messages", [])

            # Find and modify the tool call message
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls"):
                    for tc in msg.tool_calls:
                        if tc["id"] == tool_call_id:
                            # Add rejection message
                            from langchain_core.messages import ToolMessage
                            rejection = ToolMessage(
                                content="Tool call rejected by user",
                                tool_call_id=tool_call_id,
                            )
                            agent.update_state(config, {"messages": [rejection]})
                            break

            async for event in agent.astream_events(None, config, version="v2"):
                yield event

        elif decision == "edit" and edited_args:
            # Update tool call args and resume
            state = agent.get_state(config)
            messages = state.values.get("messages", [])

            for msg in reversed(messages):
                if hasattr(msg, "tool_calls"):
                    for tc in msg.tool_calls:
                        if tc["id"] == tool_call_id:
                            tc["args"] = edited_args
                            # Persist the modified message to checkpoint
                            agent.update_state(config, {"messages": [msg]})
                            break

            async for event in agent.astream_events(None, config, version="v2"):
                yield event

    # v0.0.3: Removed clear_cache - no longer needed with persistent checkpointing
