"""Run Agent use case."""

from typing import Any, AsyncIterator
from google.oauth2.credentials import Credentials
from langgraph.checkpoint.memory import MemorySaver
from deepagents import create_deep_agent

from backend.domain.ports import AgentRepository, CredentialStore
from backend.domain.exceptions import AgentNotFoundError, CredentialNotFoundError
from backend.infrastructure.tools.registry import ToolRegistryImpl


class RunAgentUseCase:
    """Use case for running an agent with a message.

    Creates and executes a deepagents instance from an agent definition.
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        credential_store: CredentialStore,
        tool_registry: ToolRegistryImpl,
    ):
        """Initialize the use case.

        Args:
            agent_repo: Repository for agent definitions
            credential_store: Store for credentials
            tool_registry: Registry for tools
        """
        self.agent_repo = agent_repo
        self.credential_store = credential_store
        self.tool_registry = tool_registry
        self._agents: dict[str, Any] = {}  # Cache of running agents

    async def get_or_create_agent(
        self,
        agent_id: str,
        thread_id: str,
    ) -> tuple[Any, dict]:
        """Get or create an agent instance.

        Args:
            agent_id: Agent definition ID
            thread_id: Conversation thread ID

        Returns:
            Tuple of (agent instance, config dict)

        Raises:
            AgentNotFoundError: If agent not found
            CredentialNotFoundError: If credentials not found
        """
        cache_key = f"{agent_id}:{thread_id}"

        if cache_key in self._agents:
            return self._agents[cache_key]

        # Load agent definition
        agent_def = await self.agent_repo.get(agent_id)
        if not agent_def:
            raise AgentNotFoundError(agent_id)

        # Get credentials
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

        # Create tools
        tools = await self.tool_registry.create_tools(agent_def.tools, credentials)

        # Get HITL tools
        hitl_tools = self.tool_registry.get_hitl_tools(agent_def.tools)

        # Create checkpointer
        checkpointer = MemorySaver()

        # Create agent
        agent = create_deep_agent(
            model=agent_def.model,
            tools=tools,
            system_message=agent_def.system_prompt,
            checkpointer=checkpointer,
            interrupt_on=hitl_tools,
        )

        config = {"configurable": {"thread_id": thread_id}}
        self._agents[cache_key] = (agent, config)

        return agent, config

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
                            break

            async for event in agent.astream_events(None, config, version="v2"):
                yield event

    def clear_cache(self, agent_id: str | None = None):
        """Clear agent cache.

        Args:
            agent_id: Specific agent to clear, or None for all
        """
        if agent_id:
            keys_to_remove = [k for k in self._agents if k.startswith(f"{agent_id}:")]
            for key in keys_to_remove:
                del self._agents[key]
        else:
            self._agents.clear()
