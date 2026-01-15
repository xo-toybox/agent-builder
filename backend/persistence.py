from pathlib import Path

from pydantic import BaseModel


CONFIG_PATH = Path("data/agent_config.json")


class TriggerConfig(BaseModel):
    id: str
    type: str = "gmail_polling"
    enabled: bool = False
    config: dict = {}


class SubagentConfig(BaseModel):
    name: str
    description: str
    system_prompt: str
    tools: list[str]


class AgentConfig(BaseModel):
    name: str = "Email Assistant"
    instructions: str = ""
    tools: list[str] = [
        "list_emails",
        "get_email",
        "search_emails",
        "draft_reply",
        "send_email",
        "label_email",
    ]
    hitl_tools: list[str] = ["draft_reply", "send_email"]
    subagents: list[SubagentConfig] = []
    triggers: list[TriggerConfig] = []


def load_config() -> AgentConfig:
    """Load agent configuration from JSON file."""
    if CONFIG_PATH.exists():
        return AgentConfig.model_validate_json(CONFIG_PATH.read_text())

    # Return default config with calendar subagent
    return AgentConfig(
        subagents=[
            SubagentConfig(
                name="calendar_context",
                description="Check calendar availability and parse meeting requests",
                system_prompt="You help check calendar availability and parse meeting requests from emails.",
                tools=["list_events", "get_event"],
            )
        ],
        triggers=[
            TriggerConfig(
                id="gmail_poll_1",
                type="gmail_polling",
                enabled=False,
                config={"interval_seconds": 30, "account": ""},
            )
        ],
    )


def save_config(config: AgentConfig) -> None:
    """Save agent configuration to JSON file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(config.model_dump_json(indent=2))
