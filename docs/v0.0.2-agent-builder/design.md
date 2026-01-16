# Agent Builder v0.0.2 Design Document

## Overview

v0.0.2 transforms Agent Builder from a hardcoded email assistant (v0.0.1) into a **generic agent platform** that can generate any agent a user is interested in.

**Vision:** Users describe what they want in natural language, and Agent Builder creates a fully configured agent ready to work.

**Key Features:**
- **Chat-based agent creation** - Describe your goal, AI figures out the approach
- **Any agent type** - Email, research, project management, customer support, etc.
- **Flexible tools** - Built-in tools + connect external APIs via MCP
- **Configurable triggers** - Email polling, webhooks, scheduled runs
- **HITL approvals** - Stay in control with approvals for sensitive actions
- **Templates** - Start from starters (email assistant) or build from scratch
- **Memory** - Agents learn from feedback over time

**Reference:** [LangSmith Agent Builder](https://www.blog.langchain.com/langsmith-agent-builder-generally-available/)

**Architecture:** Hexagonal (Ports & Adapters) with Domain-Driven Design

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ REST API     │  │ WebSocket    │  │ Builder Wizard         │ │
│  │ (FastAPI)    │  │ Chat Handler │  │ (Meta-Agent)           │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Application Layer                          │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Use Cases (Commands/Queries)                                 ││
│  │  - CreateAgentFromWizard                                     ││
│  │  - RunAgentWithHITL                                          ││
│  │  - StartTrigger / StopTrigger                                ││
│  │  - RegisterMCPServer                                         ││
│  │  - CloneTemplate                                             ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Domain Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Entities    │  │ Services      │  │ Ports (Protocols)      │ │
│  │ - Agent     │  │ - ToolFactory │  │ - AgentRepository      │ │
│  │ - Tool      │  │ - AgentFactory│  │ - MCPRepository        │ │
│  │ - Trigger   │  │ - TriggerMgr  │  │ - ConversationRepo     │ │
│  │ - HITL      │  │               │  │ - CredentialStore      │ │
│  └─────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                        │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Adapters (Implementations of Ports)                          ││
│  │                                                               ││
│  │ Persistence:                                                  ││
│  │  - SQLiteAgentRepository                                     ││
│  │  - SQLiteMCPRepository                                       ││
│  │  - SQLiteConversationRepository                              ││
│  │  - SQLiteCredentialStore                                     ││
│  │                                                               ││
│  │ External Services:                                            ││
│  │  - BuiltinToolFactory (Gmail, Calendar)                      ││
│  │  - MCPToolFactory (MCP client)                               ││
│  │  - DeepAgentsFactory (deepagents wrapper)                    ││
│  │  - GoogleOAuthProvider                                        ││
│  │  - EmailPollingTrigger                                        ││
│  │  - WebhookTrigger                                             ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
agent-builder/
├── backend/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app setup + router registration
│   ├── config.py                    # Environment config (Pydantic Settings)
│   │
│   ├── domain/                      # Domain Layer (Pure Business Logic)
│   │   ├── __init__.py
│   │   ├── entities.py              # Pydantic models: Agent, Tool, Trigger, HITL
│   │   ├── ports.py                 # Repository protocols (interfaces)
│   │   ├── services.py              # Domain service protocols
│   │   ├── tool_registry.py         # Tool registry protocol
│   │   └── exceptions.py            # Domain-specific exceptions
│   │
│   ├── application/                 # Application Layer (Use Cases)
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # UseCase protocol
│   │   │   ├── create_agent.py      # CreateAgentUseCase
│   │   │   ├── run_agent.py         # RunAgentWithHITLUseCase
│   │   │   ├── manage_triggers.py   # Start/StopTriggerUseCase
│   │   │   ├── manage_mcp.py        # RegisterMCPServerUseCase
│   │   │   └── clone_template.py    # CloneTemplateUseCase
│   │   ├── builder.py               # BuilderWizard implementation
│   │   ├── dto.py                   # Request/Response DTOs
│   │   └── dependencies.py          # Dependency injection container
│   │
│   ├── infrastructure/              # Infrastructure Layer (Adapters)
│   │   ├── __init__.py
│   │   ├── persistence/
│   │   │   ├── __init__.py
│   │   │   ├── sqlite/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py      # SQLAlchemy async engine setup
│   │   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   │   ├── agent_repo.py    # SQLiteAgentRepository
│   │   │   │   ├── mcp_repo.py      # SQLiteMCPRepository
│   │   │   │   ├── conversation_repo.py
│   │   │   │   └── credential_store.py
│   │   │   └── inmemory/            # For testing
│   │   │       ├── __init__.py
│   │   │       └── agent_repo.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── builtin.py           # BuiltinToolFactory
│   │   │   ├── builtin_gmail.py     # Gmail tools (refactored from tools/)
│   │   │   ├── builtin_calendar.py  # Calendar tools (refactored)
│   │   │   ├── mcp_client.py        # MCPToolFactory
│   │   │   └── registry.py          # ToolRegistry implementation
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   └── deepagents_factory.py # DeepAgentsFactory
│   │   ├── triggers/
│   │   │   ├── __init__.py
│   │   │   ├── email_polling.py     # EmailPollingTrigger (refactored)
│   │   │   ├── webhook.py           # WebhookTrigger
│   │   │   └── manager.py           # TriggerManager
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── google_oauth.py      # GoogleOAuthProvider (refactored)
│   │   └── templates/
│   │       ├── __init__.py
│   │       └── email_assistant.py   # Pre-built email assistant template
│   │
│   ├── api/                         # Presentation Layer (API Routes)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py            # Agent CRUD endpoints
│   │   │   ├── wizard.py            # Builder wizard chat
│   │   │   ├── chat.py              # Agent chat endpoints
│   │   │   ├── tools.py             # Tool listing, MCP management
│   │   │   ├── triggers.py          # Trigger management
│   │   │   └── auth.py              # OAuth endpoints (refactored)
│   │   ├── websocket.py             # WebSocket handlers (refactored)
│   │   └── dependencies.py          # FastAPI dependencies
│   │
│   └── migration/                   # Migration & Seeding
│       ├── __init__.py
│       ├── json_to_sqlite.py        # Migrate v0.0.1 JSON to SQLite
│       └── seed_templates.py        # Load email assistant template
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Main app with routing
│   │   ├── types/
│   │   │   └── index.ts             # Updated TypeScript types
│   │   ├── hooks/
│   │   │   ├── useAgent.ts          # MODIFY: Multi-agent support
│   │   │   ├── useWebSocket.ts      # MODIFY: Agent ID support
│   │   │   ├── useAgents.ts         # NEW: List agents hook
│   │   │   └── useBuilderChat.ts    # NEW: Builder wizard hook
│   │   ├── pages/
│   │   │   ├── AgentList.tsx        # NEW: Agent selection page
│   │   │   ├── AgentEditor.tsx      # Canvas UI (from App.tsx)
│   │   │   └── AgentBuilder.tsx     # NEW: Builder wizard page
│   │   └── components/
│   │       ├── layout/
│   │       │   ├── Sidebar.tsx      # MODIFY: Agent list
│   │       │   ├── Canvas.tsx       # Keep existing
│   │       │   └── Header.tsx       # Keep existing
│   │       ├── chat/
│   │       │   ├── ChatPanel.tsx    # Keep existing
│   │       │   └── HITLApproval.tsx # Keep existing
│   │       └── builder/
│   │           ├── WizardChat.tsx   # NEW: Builder chat UI
│   │           └── TemplateList.tsx # NEW: Template picker
│   └── ...
│
├── data/
│   ├── agent_builder.db             # SQLite database (gitignored)
│   └── google_token.json            # OAuth tokens (gitignored)
│
├── docs/
│   ├── v0.0.1-email-assistant/
│   │   └── design.md
│   └── v0.0.2-agent-builder/
│       ├── design.md                # This file
│       ├── migration-guide.md
│       └── mcp-guide.md
│
├── .env
└── pyproject.toml
```

---

## Domain Layer

### Core Entities

```python
# backend/domain/entities.py

from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from enum import Enum
from typing import Literal


class ToolSource(str, Enum):
    BUILTIN = "builtin"
    MCP = "mcp"


class ToolConfig(BaseModel):
    """Configuration for a tool attached to an agent."""
    name: str
    source: ToolSource
    enabled: bool = True
    hitl_enabled: bool = False
    server_id: str | None = None  # For MCP tools
    server_config: dict = {}

    @model_validator(mode='after')
    def validate_mcp_server_id(self):
        """Ensure MCP tools have a server_id."""
        if self.source == ToolSource.MCP and not self.server_id:
            raise ValueError("MCP tools must have a server_id")
        return self


class TriggerType(str, Enum):
    EMAIL_POLLING = "email_polling"
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    EVENT = "event"


class TriggerConfig(BaseModel):
    """Trigger configuration for an agent."""
    id: str
    type: TriggerType
    enabled: bool = False
    config: dict = {}


class SubagentConfig(BaseModel):
    """Subagent configuration."""
    name: str
    description: str
    system_prompt: str
    tools: list[str]


class AgentDefinition(BaseModel):
    """Core agent definition (can be a template)."""
    id: str
    name: str
    description: str = ""
    system_prompt: str
    model: str = "claude-sonnet-4-20250514"
    tools: list[ToolConfig] = []
    subagents: list[SubagentConfig] = []
    triggers: list[TriggerConfig] = []
    created_at: datetime
    updated_at: datetime
    is_template: bool = False


class HITLDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class HITLRequest(BaseModel):
    """Pending human-in-the-loop approval request."""
    id: str
    thread_id: str
    agent_id: str
    tool_call_id: str
    tool_name: str
    tool_args: dict
    status: Literal["pending", "approved", "rejected", "edited"]
    decision: HITLDecision | None = None
    edited_args: dict | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class MCPServerConfig(BaseModel):
    """MCP server connection configuration."""
    id: str
    name: str
    command: str
    args: list[str] = []
    env: dict[str, str] = {}
    enabled: bool = True
```

### Repository Ports (Interfaces)

```python
# backend/domain/ports.py

from typing import Protocol
from backend.domain.entities import (
    AgentDefinition, MCPServerConfig, HITLRequest
)


class AgentRepository(Protocol):
    """Port for agent persistence."""

    async def save(self, agent: AgentDefinition) -> None: ...
    async def get(self, id: str) -> AgentDefinition | None: ...
    async def list_all(self, is_template: bool | None = None) -> list[AgentDefinition]: ...
    async def delete(self, id: str) -> None: ...
    async def clone(self, id: str, new_name: str) -> str: ...


class MCPRepository(Protocol):
    """Port for MCP server configuration persistence."""

    async def save(self, server: MCPServerConfig) -> None: ...
    async def get(self, id: str) -> MCPServerConfig | None: ...
    async def list_all(self) -> list[MCPServerConfig]: ...
    async def delete(self, id: str) -> None: ...


class HITLRepository(Protocol):
    """Port for HITL request persistence."""

    async def save(self, request: HITLRequest) -> None: ...
    async def get(self, id: str) -> HITLRequest | None: ...
    async def get_by_tool_call(self, tool_call_id: str) -> HITLRequest | None: ...
    async def list_pending(self, agent_id: str) -> list[HITLRequest]: ...
    async def update_status(
        self, id: str,
        decision: str,
        edited_args: dict | None = None
    ) -> None: ...


class ConversationRepository(Protocol):
    """Port for conversation thread persistence."""

    async def save_message(self, thread_id: str, agent_id: str, message: dict) -> None: ...
    async def get_thread(self, thread_id: str) -> list[dict]: ...
    async def list_threads(self, agent_id: str) -> list[str]: ...
    async def delete_thread(self, thread_id: str) -> None: ...


class CredentialStore(Protocol):
    """Port for secure credential storage."""

    async def save(self, provider: str, credentials: dict) -> None: ...
    async def get(self, provider: str) -> dict | None: ...
    async def delete(self, provider: str) -> None: ...
```

### Service Protocols

```python
# backend/domain/services.py

from typing import Protocol, Any
from backend.domain.entities import AgentDefinition, ToolConfig


class ToolFactory(Protocol):
    """Creates executable tools from config."""

    def create_tools(
        self,
        configs: list[ToolConfig],
        credentials: dict
    ) -> list[Any]:
        """Create LangChain-compatible tools from configs."""
        ...


class AgentFactory(Protocol):
    """Creates runnable agents from definitions."""

    def create_agent(
        self,
        definition: AgentDefinition,
        credentials: dict,
        checkpointer: Any
    ) -> Any:
        """Create a deepagents instance from definition."""
        ...


class TriggerManager(Protocol):
    """Manages trigger lifecycle."""

    async def start(self, agent_id: str, trigger_id: str) -> None: ...
    async def stop(self, trigger_id: str) -> None: ...
    async def stop_all(self, agent_id: str) -> None: ...
    def list_running(self) -> list[str]: ...
```

---

## Application Layer

### Use Cases

```python
# backend/application/use_cases/create_agent.py

from pydantic import BaseModel
from backend.domain.entities import AgentDefinition, ToolConfig, TriggerConfig
from backend.domain.ports import AgentRepository
from datetime import datetime
import uuid


class CreateAgentRequest(BaseModel):
    name: str
    description: str = ""
    system_prompt: str
    tools: list[ToolConfig] = []
    triggers: list[TriggerConfig] = []
    is_template: bool = False


class CreateAgentResponse(BaseModel):
    agent_id: str


class CreateAgentUseCase:
    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    async def execute(self, request: CreateAgentRequest) -> CreateAgentResponse:
        agent = AgentDefinition(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            tools=request.tools,
            triggers=request.triggers,
            is_template=request.is_template,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await self.agent_repo.save(agent)
        return CreateAgentResponse(agent_id=agent.id)
```

```python
# backend/application/use_cases/clone_template.py

from pydantic import BaseModel
from backend.domain.ports import AgentRepository


class CloneTemplateRequest(BaseModel):
    template_id: str
    new_name: str


class CloneTemplateResponse(BaseModel):
    agent_id: str


class CloneTemplateUseCase:
    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    async def execute(self, request: CloneTemplateRequest) -> CloneTemplateResponse:
        new_id = await self.agent_repo.clone(
            request.template_id,
            request.new_name
        )
        return CloneTemplateResponse(agent_id=new_id)
```

### Builder Wizard

```python
# backend/application/builder.py

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Any

from backend.config import settings
from backend.domain.entities import AgentDefinition, ToolConfig, TriggerConfig
from backend.domain.ports import AgentRepository
from datetime import datetime
import uuid


BUILDER_SYSTEM_PROMPT = """You are an agent builder assistant. You help users create AI agents through conversation.

Your job is to:
1. Understand what the user wants their agent to do
2. Ask clarifying questions to gather requirements
3. Suggest appropriate tools, triggers, and configurations
4. Use your tools to create the agent when ready

Available built-in tools:
- Gmail: list_emails, get_email, search_emails, draft_reply, send_email, label_email
- Calendar: list_events, get_event

You can also suggest MCP server tools for additional capabilities.

When you have enough information, use the create_agent tool to finalize the agent.
Be conversational and guide users step-by-step."""


class AgentSpec(BaseModel):
    name: str
    description: str
    system_prompt: str
    tools: list[dict]
    triggers: list[dict] = []


class BuilderWizard:
    """Chat-based wizard for creating agents via conversation."""

    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo
        self.model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
        )
        self.conversation_state: dict[str, list] = {}  # thread_id -> messages
        self._setup_tools()

    def _setup_tools(self):
        @tool
        async def create_agent(spec: AgentSpec) -> str:
            """Create an agent from the gathered specification."""
            tools = [
                ToolConfig(
                    name=t["name"],
                    source=t.get("source", "builtin"),
                    hitl_enabled=t.get("hitl", False),
                    server_id=t.get("server_id"),
                    server_config=t.get("server_config", {}),
                )
                for t in spec.tools
            ]

            triggers = [
                TriggerConfig(
                    id=str(uuid.uuid4()),
                    type=t["type"],
                    enabled=t.get("enabled", False),
                    config=t.get("config", {}),
                )
                for t in spec.triggers
            ]

            agent = AgentDefinition(
                id=str(uuid.uuid4()),
                name=spec.name,
                description=spec.description,
                system_prompt=spec.system_prompt,
                tools=tools,
                triggers=triggers,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            await self.agent_repo.save(agent)
            return f"Created agent '{spec.name}' with ID: {agent.id}"

        @tool
        def list_available_tools() -> dict:
            """List all available built-in tools."""
            return {
                "gmail": [
                    {"name": "list_emails", "description": "List emails from inbox"},
                    {"name": "get_email", "description": "Get full email content"},
                    {"name": "search_emails", "description": "Search emails with query"},
                    {"name": "draft_reply", "description": "Create draft reply (HITL recommended)"},
                    {"name": "send_email", "description": "Send email (HITL recommended)"},
                    {"name": "label_email", "description": "Modify email labels"},
                ],
                "calendar": [
                    {"name": "list_events", "description": "List calendar events"},
                    {"name": "get_event", "description": "Get event details"},
                ],
            }

        self.tools = [create_agent, list_available_tools]

    async def chat(self, thread_id: str, user_message: str) -> str:
        """Process user message and return wizard response."""
        if thread_id not in self.conversation_state:
            self.conversation_state[thread_id] = []

        self.conversation_state[thread_id].append({
            "role": "user",
            "content": user_message
        })

        response = await self.model.bind_tools(self.tools).ainvoke([
            {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
            *self.conversation_state[thread_id]
        ])

        # Handle tool calls
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_fn = next(t for t in self.tools if t.name == tool_call["name"])
                result = await tool_fn.ainvoke(tool_call["args"])
                self.conversation_state[thread_id].append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call["id"]
                })

        self.conversation_state[thread_id].append({
            "role": "assistant",
            "content": response.content
        })

        return response.content
```

---

## Infrastructure Layer

### SQLite Persistence

```python
# backend/infrastructure/persistence/sqlite/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///{settings.database_path}"

engine = create_async_engine(DATABASE_URL, echo=settings.debug)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session
```

```python
# backend/infrastructure/persistence/sqlite/models.py

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.infrastructure.persistence.sqlite.database import Base


class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    system_prompt = Column(Text, nullable=False)
    model = Column(String, default="claude-sonnet-4-20250514")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_template = Column(Boolean, default=False)

    tools = relationship("AgentToolModel", back_populates="agent", cascade="all, delete-orphan")
    subagents = relationship("AgentSubagentModel", back_populates="agent", cascade="all, delete-orphan")
    triggers = relationship("AgentTriggerModel", back_populates="agent", cascade="all, delete-orphan")


class AgentToolModel(Base):
    __tablename__ = "agent_tools"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)  # "builtin" or "mcp"
    enabled = Column(Boolean, default=True)
    hitl_enabled = Column(Boolean, default=False)
    server_id = Column(String, nullable=True)
    server_config = Column(JSON, default={})

    agent = relationship("AgentModel", back_populates="tools")


class AgentSubagentModel(Base):
    __tablename__ = "agent_subagents"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    tools = Column(JSON, nullable=False)  # List of tool names

    agent = relationship("AgentModel", back_populates="subagents")


class AgentTriggerModel(Base):
    __tablename__ = "agent_triggers"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    type = Column(String, nullable=False)
    enabled = Column(Boolean, default=False)
    config = Column(JSON, default={})

    agent = relationship("AgentModel", back_populates="triggers")


class MCPServerModel(Base):
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    command = Column(String, nullable=False)
    args = Column(JSON, default=[])
    env = Column(JSON, default={})
    enabled = Column(Boolean, default=True)


class HITLRequestModel(Base):
    __tablename__ = "hitl_requests"

    id = Column(String, primary_key=True)
    thread_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    tool_call_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    tool_args = Column(JSON, nullable=False)
    status = Column(String, default="pending")
    decision = Column(String, nullable=True)
    edited_args = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class CredentialModel(Base):
    __tablename__ = "credentials"

    provider = Column(String, primary_key=True)
    encrypted_data = Column(Text, nullable=False)  # Fernet encrypted JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### MCP Tool Factory

```python
# backend/infrastructure/tools/mcp_client.py

import asyncio
import json
import os
from typing import Any
from langchain_core.tools import tool

from backend.domain.entities import MCPServerConfig


class MCPToolFactory:
    """Creates LangChain tools from MCP server connections."""

    def __init__(self):
        self._connections: dict[str, asyncio.subprocess.Process] = {}

    async def create_tools(
        self,
        server_config: MCPServerConfig
    ) -> list[Any]:
        """Connect to MCP server and create tools from its manifest."""
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

        response_line = await process.stdout.readline()
        response = json.loads(response_line)

        tools = []
        for tool_spec in response.get("result", {}).get("tools", []):
            tools.append(self._create_tool(server_config.id, tool_spec, process))

        return tools

    def _create_tool(
        self,
        server_id: str,
        tool_spec: dict,
        process: asyncio.subprocess.Process
    ) -> Any:
        """Create a LangChain tool from MCP tool specification."""

        @tool(name=f"mcp_{server_id}_{tool_spec['name']}")
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

            response_line = await process.stdout.readline()
            response = json.loads(response_line)

            if "error" in response:
                return {"error": response["error"]}

            return response.get("result", {})

        mcp_tool_wrapper.__doc__ = tool_spec.get("description", "MCP tool")
        return mcp_tool_wrapper

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for server_id, process in self._connections.items():
            process.terminate()
            await process.wait()
        self._connections.clear()
```

### Tool Registry

```python
# backend/infrastructure/tools/registry.py

from typing import Any
from google.oauth2.credentials import Credentials

from backend.domain.entities import ToolConfig, ToolSource
from backend.domain.ports import MCPRepository
from backend.infrastructure.tools.builtin_gmail import create_gmail_tools
from backend.infrastructure.tools.builtin_calendar import create_calendar_tools
from backend.infrastructure.tools.mcp_client import MCPToolFactory


class ToolRegistryImpl:
    """Registry for all available tools (builtin + MCP)."""

    def __init__(self, mcp_repo: MCPRepository):
        self.mcp_repo = mcp_repo
        self.mcp_factory = MCPToolFactory()
        self._tool_cache: dict[str, list] = {}

    async def create_tools(
        self,
        configs: list[ToolConfig],
        credentials: Credentials
    ) -> list[Any]:
        """Create executable tools from configurations."""
        tools = []

        for config in configs:
            if not config.enabled:
                continue

            if config.source == ToolSource.BUILTIN:
                tool = self._get_builtin_tool(config.name, credentials)
                if tool:
                    tools.append(tool)

            elif config.source == ToolSource.MCP:
                if config.server_id:
                    mcp_tools = await self._get_mcp_tools(config.server_id)
                    tool = next((t for t in mcp_tools if t.name == config.name), None)
                    if tool:
                        tools.append(tool)

        return tools

    def _get_builtin_tool(self, name: str, credentials: Credentials) -> Any:
        """Get a single builtin tool by name."""
        cache_key = f"builtin_{id(credentials)}"

        if cache_key not in self._tool_cache:
            gmail_tools = create_gmail_tools(credentials)
            calendar_tools = create_calendar_tools(credentials)
            self._tool_cache[cache_key] = gmail_tools + calendar_tools

        for tool in self._tool_cache[cache_key]:
            if tool.name == name:
                return tool

        return None

    async def _get_mcp_tools(self, server_id: str) -> list[Any]:
        """Get tools from an MCP server."""
        cache_key = f"mcp_{server_id}"

        if cache_key not in self._tool_cache:
            server = await self.mcp_repo.get(server_id)
            if server:
                tools = await self.mcp_factory.create_tools(server)
                self._tool_cache[cache_key] = tools
            else:
                self._tool_cache[cache_key] = []

        return self._tool_cache[cache_key]

    def list_available_builtin(self) -> dict:
        """List all available builtin tools."""
        return {
            "gmail": [
                {"name": "list_emails", "description": "List emails from inbox"},
                {"name": "get_email", "description": "Get full email content by ID"},
                {"name": "search_emails", "description": "Search emails using Gmail query syntax"},
                {"name": "draft_reply", "description": "Create draft reply (HITL recommended)"},
                {"name": "send_email", "description": "Send email (HITL recommended)"},
                {"name": "label_email", "description": "Modify email labels"},
            ],
            "calendar": [
                {"name": "list_events", "description": "List calendar events"},
                {"name": "get_event", "description": "Get event details"},
            ],
        }
```

---

## API Layer

### Agent CRUD Endpoints

```python
# backend/api/v1/agents.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.domain.entities import AgentDefinition, ToolConfig, TriggerConfig
from backend.domain.ports import AgentRepository
from backend.application.use_cases.create_agent import CreateAgentUseCase, CreateAgentRequest
from backend.application.use_cases.clone_template import CloneTemplateUseCase, CloneTemplateRequest
from backend.api.dependencies import get_agent_repo

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentSummary(BaseModel):
    id: str
    name: str
    description: str
    is_template: bool


class AgentDetail(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    model: str
    tools: list[ToolConfig]
    triggers: list[TriggerConfig]
    is_template: bool


class CreateAgentBody(BaseModel):
    name: str
    description: str = ""
    system_prompt: str
    tools: list[ToolConfig] = []
    triggers: list[TriggerConfig] = []


class CloneBody(BaseModel):
    new_name: str


@router.get("", response_model=list[AgentSummary])
async def list_agents(
    is_template: Optional[bool] = None,
    agent_repo: AgentRepository = Depends(get_agent_repo)
):
    """List all agents, optionally filtered by template status."""
    agents = await agent_repo.list_all(is_template=is_template)
    return [
        AgentSummary(
            id=a.id,
            name=a.name,
            description=a.description,
            is_template=a.is_template,
        )
        for a in agents
    ]


@router.get("/templates", response_model=list[AgentSummary])
async def list_templates(agent_repo: AgentRepository = Depends(get_agent_repo)):
    """List all agent templates."""
    agents = await agent_repo.list_all(is_template=True)
    return [
        AgentSummary(
            id=a.id,
            name=a.name,
            description=a.description,
            is_template=True,
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentDetail)
async def get_agent(
    agent_id: str,
    agent_repo: AgentRepository = Depends(get_agent_repo)
):
    """Get agent details."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("", response_model=dict)
async def create_agent(
    body: CreateAgentBody,
    agent_repo: AgentRepository = Depends(get_agent_repo)
):
    """Create a new agent."""
    use_case = CreateAgentUseCase(agent_repo)
    request = CreateAgentRequest(
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt,
        tools=body.tools,
        triggers=body.triggers,
    )
    response = await use_case.execute(request)
    return {"agent_id": response.agent_id}


@router.post("/{agent_id}/clone", response_model=dict)
async def clone_agent(
    agent_id: str,
    body: CloneBody,
    agent_repo: AgentRepository = Depends(get_agent_repo)
):
    """Clone an agent (typically from a template)."""
    use_case = CloneTemplateUseCase(agent_repo)
    request = CloneTemplateRequest(template_id=agent_id, new_name=body.new_name)
    response = await use_case.execute(request)
    return {"agent_id": response.agent_id}


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    agent_repo: AgentRepository = Depends(get_agent_repo)
):
    """Delete an agent."""
    await agent_repo.delete(agent_id)
    return {"success": True}
```

### WebSocket Chat Handler

```python
# backend/api/websocket.py

import json
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from langgraph.checkpoint.memory import MemorySaver

from backend.domain.ports import AgentRepository, CredentialStore
from backend.infrastructure.tools.registry import ToolRegistryImpl
from backend.infrastructure.agents.deepagents_factory import DeepAgentsFactory


class WebSocketChatHandler:
    """Handles WebSocket chat connections for agents."""

    def __init__(
        self,
        agent_repo: AgentRepository,
        credential_store: CredentialStore,
        tool_registry: ToolRegistryImpl,
    ):
        self.agent_repo = agent_repo
        self.credential_store = credential_store
        self.tool_registry = tool_registry
        self.agent_factory = DeepAgentsFactory(tool_registry)
        self.active_connections: dict[str, WebSocket] = {}

    async def handle_connection(self, websocket: WebSocket, agent_id: str):
        """Handle WebSocket connection for agent chat."""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        thread_id = str(uuid.uuid4())

        try:
            # Load agent definition
            agent_def = await self.agent_repo.get(agent_id)
            if not agent_def:
                await websocket.send_json({
                    "type": "error",
                    "message": "Agent not found"
                })
                return

            # Get credentials
            credentials = await self.credential_store.get("google")
            if not credentials:
                await websocket.send_json({
                    "type": "error",
                    "message": "Not authenticated. Please login first."
                })
                return

            # Create agent instance
            checkpointer = MemorySaver()
            agent = await self.agent_factory.create_agent(
                agent_def, credentials, checkpointer
            )
            config = {"configurable": {"thread_id": thread_id}}

            # Main message loop
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message["type"] == "message":
                    await self._run_agent(agent, config, message["content"], websocket)

                elif message["type"] == "hitl_decision":
                    await self._resume_agent(
                        agent, config, message, websocket
                    )

        except WebSocketDisconnect:
            pass
        finally:
            self.active_connections.pop(connection_id, None)

    async def _run_agent(self, agent, config, user_content, websocket):
        """Run agent and stream results."""
        input_messages = {"messages": [{"role": "user", "content": user_content}]}

        async for event in agent.astream_events(input_messages, config, version="v2"):
            event_type = event.get("event")

            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    content = self._extract_content(chunk.content)
                    if content:
                        await websocket.send_json({
                            "type": "token",
                            "content": content
                        })

            elif event_type == "on_tool_start":
                await websocket.send_json({
                    "type": "tool_call",
                    "name": event.get("name", ""),
                    "args": event.get("data", {}).get("input", {}),
                })

            elif event_type == "on_tool_end":
                result = event.get("data", {}).get("output")
                await websocket.send_json({
                    "type": "tool_result",
                    "name": event.get("name", ""),
                    "result": result if isinstance(result, (dict, list, str)) else str(result),
                })

        # Check for HITL interrupt
        state = agent.get_state(config)
        if state.next:
            await self._send_hitl_interrupt(state, websocket)
        else:
            await websocket.send_json({"type": "complete"})

    async def _send_hitl_interrupt(self, state, websocket):
        """Send HITL interrupt to client."""
        messages = state.values.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    await websocket.send_json({
                        "type": "hitl_interrupt",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                    })
                    return

    def _extract_content(self, content) -> str:
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
```

---

## Email Assistant Template

```python
# backend/infrastructure/templates/email_assistant.py

from backend.domain.entities import (
    AgentDefinition, ToolConfig, SubagentConfig,
    TriggerConfig, ToolSource, TriggerType
)
from datetime import datetime

EMAIL_ASSISTANT_SYSTEM_PROMPT = """# Email Assistant

You are an intelligent email assistant that helps process incoming emails, triage them, draft or send appropriate responses, and flag important messages when needed.

## Core Mission

Your primary objectives are:
1. Automatically mark emails as read that are not important.
2. Only surface emails that genuinely require your user's attention or decision-making.
3. Pay attention to feedback from the user and refine your approach over time.

## Email Preferences

### Emails to mark as read without notifying user:
- Spam emails from unknown senders
- Mass marketing emails from companies that come frequently
- Emails that look like phishing attempts

### Emails to notify user about (but don't take action):
- Emails from people who personally know the user
- Emails that sound urgent or time-sensitive

### Emails to take action on:
- Meeting requests: delegate to calendar_context subagent to check availability
- Availability inquiries: check calendar and respond appropriately

## Email Processing Workflow

When processing emails:
1. Analyze the email content thoroughly
2. Check if you have instructions for this type of email
3. Follow existing instructions, or notify the user if uncertain

## Available Tools

### Email Tools
- list_emails: List recent emails with filters
- get_email: Get full email content by ID
- search_emails: Search using Gmail query syntax
- draft_reply: Create a draft reply (requires approval)
- send_email: Send an email (requires approval)
- label_email: Modify labels (mark read, archive, etc.)

### Calendar (via calendar_context subagent)
- list_events: Check calendar for a date range
- get_event: Get event details

## Response Style

- Keep responses brief and to the point
- Be polite without being overly casual
- Match tone to email type (formal for external, natural for colleagues)
- Adapt based on relationship and context

## Important Guidelines

- When uncertain, ask the user for guidance
- Bias towards notifying rather than acting incorrectly
- Delegate date parsing and calendar checks to calendar_context subagent
- Learn from user feedback to improve over time
"""

EMAIL_ASSISTANT_TEMPLATE = AgentDefinition(
    id="email_assistant_template",
    name="Email Assistant",
    description="An intelligent email assistant that triages emails, drafts responses, and integrates with calendar.",
    system_prompt=EMAIL_ASSISTANT_SYSTEM_PROMPT,
    model="claude-sonnet-4-20250514",
    tools=[
        ToolConfig(name="list_emails", source=ToolSource.BUILTIN, hitl_enabled=False),
        ToolConfig(name="get_email", source=ToolSource.BUILTIN, hitl_enabled=False),
        ToolConfig(name="search_emails", source=ToolSource.BUILTIN, hitl_enabled=False),
        ToolConfig(name="draft_reply", source=ToolSource.BUILTIN, hitl_enabled=True),
        ToolConfig(name="send_email", source=ToolSource.BUILTIN, hitl_enabled=True),
        ToolConfig(name="label_email", source=ToolSource.BUILTIN, hitl_enabled=False),
    ],
    subagents=[
        SubagentConfig(
            name="calendar_context",
            description="Check calendar availability and parse meeting requests from emails",
            system_prompt="You help check calendar availability and parse meeting requests from emails.",
            tools=["list_events", "get_event"],
        )
    ],
    triggers=[
        TriggerConfig(
            id="gmail_poll_1",
            type=TriggerType.EMAIL_POLLING,
            enabled=False,
            config={"interval_seconds": 30},
        )
    ],
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    is_template=True,
)
```

---

## Migration

```python
# backend/migration/json_to_sqlite.py

import json
from pathlib import Path
from datetime import datetime

from backend.domain.entities import (
    AgentDefinition, ToolConfig, SubagentConfig,
    TriggerConfig, ToolSource, TriggerType
)
from backend.domain.ports import AgentRepository


JSON_CONFIG_PATH = Path("data/agent_config.json")


async def migrate_from_json(agent_repo: AgentRepository) -> bool:
    """Migrate existing JSON config to SQLite.

    Returns True if migration was performed, False if skipped.
    """
    if not JSON_CONFIG_PATH.exists():
        return False

    # Check if already migrated
    existing = await agent_repo.list_all()
    if existing:
        return False

    # Load JSON config
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
            type=TriggerType(t.get("type", "email_polling")),
            enabled=t.get("enabled", False),
            config=t.get("config", {}),
        )
        for t in data.get("triggers", [])
    ]

    agent = AgentDefinition(
        id="migrated_email_assistant",
        name=data.get("name", "Email Assistant"),
        description="Migrated from v0.0.1",
        system_prompt=data.get("instructions", ""),
        tools=tools,
        subagents=subagents,
        triggers=triggers,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_template=False,
    )

    await agent_repo.save(agent)

    # Backup JSON file
    JSON_CONFIG_PATH.rename(JSON_CONFIG_PATH.with_suffix(".json.backup"))

    return True
```

---

## Build Sequence

### Phase 1: Domain Foundation
- [ ] Create `backend/domain/entities.py` - All Pydantic domain models
- [ ] Create `backend/domain/ports.py` - Repository protocols
- [ ] Create `backend/domain/services.py` - Service protocols
- [ ] Create `backend/domain/exceptions.py` - Custom exceptions

### Phase 2: SQLite Infrastructure
- [ ] Update `pyproject.toml` - Add sqlalchemy, aiosqlite, alembic, cryptography
- [ ] Create `backend/infrastructure/persistence/sqlite/database.py`
- [ ] Create `backend/infrastructure/persistence/sqlite/models.py`
- [ ] Create `backend/infrastructure/persistence/sqlite/agent_repo.py`
- [ ] Create `backend/infrastructure/persistence/sqlite/mcp_repo.py`
- [ ] Create `backend/infrastructure/persistence/sqlite/hitl_repo.py`
- [ ] Create `backend/infrastructure/persistence/sqlite/credential_store.py`

### Phase 3: Tool Registry & MCP
- [ ] Refactor `backend/tools/gmail.py` → `backend/infrastructure/tools/builtin_gmail.py`
- [ ] Refactor `backend/tools/calendar.py` → `backend/infrastructure/tools/builtin_calendar.py`
- [ ] Create `backend/infrastructure/tools/builtin.py`
- [ ] Create `backend/infrastructure/tools/mcp_client.py`
- [ ] Create `backend/infrastructure/tools/registry.py`

### Phase 4: Application Layer
- [ ] Create `backend/application/use_cases/base.py`
- [ ] Create `backend/application/use_cases/create_agent.py`
- [ ] Create `backend/application/use_cases/run_agent.py`
- [ ] Create `backend/application/use_cases/manage_triggers.py`
- [ ] Create `backend/application/use_cases/manage_mcp.py`
- [ ] Create `backend/application/use_cases/clone_template.py`
- [ ] Create `backend/application/dto.py`
- [ ] Create `backend/application/dependencies.py`

### Phase 5: Builder Wizard
- [ ] Create `backend/application/builder.py`
- [ ] Define wizard tools (set_agent_name, add_tool, create_agent)
- [ ] Implement conversation state management

### Phase 6: API Refactor
- [ ] Create `backend/api/v1/agents.py`
- [ ] Create `backend/api/v1/wizard.py`
- [ ] Create `backend/api/v1/chat.py`
- [ ] Create `backend/api/v1/tools.py`
- [ ] Create `backend/api/v1/triggers.py`
- [ ] Create `backend/api/websocket.py`
- [ ] Refactor `backend/main.py` to use new routers

### Phase 7: Migration & Templates
- [ ] Create `backend/migration/json_to_sqlite.py`
- [ ] Create `backend/infrastructure/templates/email_assistant.py`
- [ ] Create `backend/migration/seed_templates.py`
- [ ] Add startup hooks for migration and seeding

### Phase 8: Frontend Updates
- [ ] Update `frontend/src/types/index.ts` with new types
- [ ] Create `frontend/src/hooks/useAgents.ts`
- [ ] Update `frontend/src/hooks/useAgent.ts` for agent_id
- [ ] Update `frontend/src/hooks/useWebSocket.ts` for agent_id
- [ ] Create `frontend/src/hooks/useBuilderChat.ts`
- [ ] Create `frontend/src/pages/AgentList.tsx`
- [ ] Create `frontend/src/pages/AgentBuilder.tsx`
- [ ] Create `frontend/src/pages/AgentEditor.tsx` (move from App.tsx)
- [ ] Update `frontend/src/App.tsx` with routing
- [ ] Update `frontend/src/components/layout/Sidebar.tsx` for agent list

### Phase 9: Testing
- [ ] Domain layer unit tests
- [ ] Use case tests with mock repositories
- [ ] SQLite repository integration tests
- [ ] API endpoint tests with TestClient
- [ ] E2E test for wizard workflow

### Phase 10: Documentation
- [ ] Update README.md
- [ ] Create migration guide
- [ ] Create MCP integration guide
- [ ] API documentation

---

## Dependencies (pyproject.toml additions)

```toml
[project]
dependencies = [
    # Existing dependencies...
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
    "alembic>=1.13.0",
    "cryptography>=42.0.0",
    "mcp>=1.0.0",
]
```

---

## Success Criteria

- [ ] Email assistant migrated from JSON to SQLite
- [ ] Can create new agent via builder wizard chat
- [ ] Can clone email assistant template
- [ ] Multiple agents work independently (separate WebSocket connections)
- [ ] At least 1 MCP server tool integrated
- [ ] Webhook trigger invokes agent
- [ ] Email polling per-agent (not global)
- [ ] No regressions in HITL, OAuth, or streaming
- [ ] Documentation complete

---

*Last updated: January 15, 2026*
