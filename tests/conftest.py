"""
Pytest configuration and shared fixtures.
"""
import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    ToolSource,
    TriggerConfig,
    TriggerType,
)
from backend.infrastructure.persistence.sqlite.database import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database session for testing."""
    # Use in-memory SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_tool_configs() -> list[ToolConfig]:
    """Create sample tool configurations for testing."""
    return [
        ToolConfig(
            name="list_emails",
            source=ToolSource.BUILTIN,
            enabled=True,
            hitl_enabled=False,
        ),
        ToolConfig(
            name="send_email",
            source=ToolSource.BUILTIN,
            enabled=True,
            hitl_enabled=True,
        ),
        ToolConfig(
            name="draft_reply",
            source=ToolSource.BUILTIN,
            enabled=False,
            hitl_enabled=True,
        ),
    ]


@pytest.fixture
def sample_trigger_configs() -> list[TriggerConfig]:
    """Create sample trigger configurations for testing."""
    return [
        TriggerConfig(
            id="trigger-1",
            type=TriggerType.SCHEDULED,
            enabled=True,
            config={"cron": "0 9 * * *"},
        ),
        TriggerConfig(
            id="trigger-2",
            type=TriggerType.EMAIL_POLLING,
            enabled=False,
            config={"poll_interval": 60},
        ),
    ]


@pytest.fixture
def sample_agent(
    sample_tool_configs: list[ToolConfig],
    sample_trigger_configs: list[TriggerConfig],
) -> AgentDefinition:
    """Create a sample agent for testing."""
    now = datetime.utcnow()
    return AgentDefinition(
        id="test-agent-123",
        name="Test Agent",
        description="A test agent for unit testing",
        system_prompt="You are a helpful test assistant.",
        model="claude-sonnet-4-20250514",
        is_template=False,
        tools=sample_tool_configs,
        triggers=sample_trigger_configs,
        subagents=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_template(sample_tool_configs: list[ToolConfig]) -> AgentDefinition:
    """Create a sample template for testing."""
    now = datetime.utcnow()
    return AgentDefinition(
        id="test-template-456",
        name="Test Template",
        description="A test template",
        system_prompt="Template system prompt.",
        model="claude-sonnet-4-20250514",
        is_template=True,
        tools=sample_tool_configs,
        triggers=[],
        subagents=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)
