"""Migrate v0.0.1 JSON configuration to SQLite.

This script migrates the existing agent_config.json to the new SQLite database.
Run once during upgrade from v0.0.1 to v0.0.2.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    SubagentConfig,
    TriggerConfig,
    ToolSource,
    TriggerType,
)
from backend.infrastructure.persistence.sqlite.database import AsyncSessionLocal
from backend.infrastructure.persistence.sqlite.agent_repo import SQLiteAgentRepository

logger = logging.getLogger(__name__)

JSON_CONFIG_PATH = Path("data/agent_config.json")


async def migrate_from_json() -> bool:
    """Migrate existing JSON config to SQLite.

    Returns True if migration was performed, False if skipped.
    """
    if not JSON_CONFIG_PATH.exists():
        logger.info("No JSON config found, skipping migration")
        return False

    async with AsyncSessionLocal() as session:
        repo = SQLiteAgentRepository(session)

        # Check if already migrated (look for any non-template agents)
        existing = await repo.list_all(is_template=False)
        if existing:
            logger.info("Agents already exist in database, skipping JSON migration")
            return False

        # Load JSON config
        logger.info(f"Loading JSON config from {JSON_CONFIG_PATH}")
        with open(JSON_CONFIG_PATH) as f:
            data = json.load(f)

        # Convert to AgentDefinition
        tools = [
            ToolConfig(
                name=tool_name,
                source=ToolSource.BUILTIN,
                hitl_enabled=tool_name in data.get("hitl_tools", []),
            )
            for tool_name in data.get("tools", [])
        ]

        subagents = [
            SubagentConfig(
                name=s.get("name"),
                description=s.get("description", ""),
                system_prompt=s.get("system_prompt", ""),
                tools=s.get("tools", []),
            )
            for s in data.get("subagents", [])
        ]

        triggers = [
            TriggerConfig(
                id=t.get("id"),
                type=TriggerType(t.get("type", "email_polling").replace("gmail_polling", "email_polling")),
                enabled=t.get("enabled", False),
                config=t.get("config", {}),
            )
            for t in data.get("triggers", [])
        ]

        now = datetime.utcnow()
        agent = AgentDefinition(
            id="migrated_email_assistant",
            name=data.get("name", "Email Assistant"),
            description="Migrated from v0.0.1 JSON configuration",
            system_prompt=data.get("instructions", ""),
            tools=tools,
            subagents=subagents,
            triggers=triggers,
            created_at=now,
            updated_at=now,
            is_template=False,
        )

        await repo.save(agent)
        logger.info(f"Migrated agent: {agent.name} (ID: {agent.id})")

        # Backup JSON file
        backup_path = JSON_CONFIG_PATH.with_suffix(".json.backup")
        JSON_CONFIG_PATH.rename(backup_path)
        logger.info(f"Backed up JSON config to {backup_path}")

        return True


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate_from_json())
