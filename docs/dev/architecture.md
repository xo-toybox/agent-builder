# Architecture

## Overview

Agent Builder uses a hexagonal (ports & adapters) architecture with four layers.

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  REST API (FastAPI) │ WebSocket Handlers │ Builder Wizard   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  CreateAgent │ RunAgent │ CloneTemplate │ ManageTriggers    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  Entities: Agent, Tool, Trigger, Skill, Memory              │
│  Ports: AgentRepository, MemoryRepository, SkillRepository  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  SQLite Repos │ Tool Registry │ MCP Client │ Checkpointer   │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Presentation Layer (`backend/api/`)

- HTTP endpoints and WebSocket handlers
- Request/response serialization
- Authentication middleware
- No business logic

### Application Layer (`backend/application/`)

- Use cases orchestrate domain operations
- Transaction boundaries
- Cross-cutting concerns (logging, error handling)

### Domain Layer (`backend/domain/`)

- Core entities and value objects
- Repository protocols (ports)
- Business rules
- No framework dependencies

### Infrastructure Layer (`backend/infrastructure/`)

- Database implementations (SQLite)
- External service clients (MCP, Google APIs)
- Tool implementations
- File system access

## Key Components

### Agent Runtime (`RunAgentUseCase`)

```
User Message → Agent Loop → Tool Execution → HITL Check → Response
                  ↑              │
                  └──────────────┘
```

Uses LangGraph for:
- Conversation state management
- Tool call routing
- Checkpoint persistence

### Builder Wizard (`BuilderService`)

Meta-agent that creates other agents:
1. Receives user description
2. Asks clarifying questions
3. Generates agent configuration
4. Calls `create_agent` tool

### HITL Flow

```
Tool Call → Check hitl_enabled → Yes → Send interrupt → Wait for decision
                    │                                          │
                    No                                    [Approve/Edit/Reject]
                    │                                          │
                    ▼                                          ▼
              Execute tool ←──────────────────────────── Resume with decision
```

### Memory System

```
write_memory(path, content)
        │
        ▼
  Path Validation → Security Check → HITL Approval → SQLite Storage
        │                  │
   (traversal)      (suspicious patterns)
```

## Data Flow

### Chat Message

```
Frontend → WebSocket → ChatHandler → RunAgentUseCase → Claude API
                                           │
                                     Tool Registry
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                          Gmail API   Calendar API   Memory FS
```

### Agent Creation

```
Builder Wizard → create_agent tool → CreateAgentUseCase → SQLite
                                            │
                                      AgentRepository
```

## Database Schema

```sql
-- Core entities
agents (id, name, description, system_prompt, model, is_template, memory_approval_required, ...)
agent_tools (id, agent_id, name, source, enabled, hitl_enabled, server_id, ...)
agent_triggers (id, agent_id, type, enabled, config, ...)
agent_subagents (id, agent_id, name, description, system_prompt, tools, ...)

-- MCP servers
mcp_servers (id, name, command, args, env, enabled)

-- Conversation & HITL
conversation_messages (id, thread_id, agent_id, role, content, extra_data, ...)
hitl_requests (id, thread_id, agent_id, tool_call_id, tool_name, tool_args, status, ...)

-- Credentials (encrypted)
credentials (provider, encrypted_data, created_at, updated_at)

-- v0.0.3: Memory & Skills
memory_files (id, agent_id, path, content, content_type, ...)
memory_edit_requests (id, agent_id, path, operation, proposed_content, status, ...)
skills (id, agent_id, name, description, instructions, enabled, ...)
wizard_conversations (id, messages, created_at, ...)

-- LangGraph checkpoints (auto-managed)
checkpoints (thread_id, checkpoint_ns, checkpoint_id, ...)
checkpoint_writes (...)
checkpoint_blobs (...)
```

## Security

### Credential Encryption

Integration credentials (Slack tokens, etc.) are encrypted at rest using Fernet symmetric encryption before storage in SQLite.

- Key: `ENCRYPTION_KEY` environment variable
- Algorithm: Fernet (AES-128-CBC with HMAC)
- Implementation: `backend/infrastructure/persistence/sqlite/credential_store.py`

Generate a key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Without `ENCRYPTION_KEY`, credentials are stored in plaintext with a warning logged. This is only acceptable for local development.

### Encryption in Transit

Not implemented by design. Agent Builder runs entirely on localhost—both the backend API and frontend are accessed via `localhost` or `127.0.0.1`. There is no network transit to protect; all communication stays on the local machine.

If you deploy this to a remote server (not recommended for this use case), you would need to add TLS termination via a reverse proxy (nginx, Caddy, etc.).

### Memory Content Validation

Agent-written memory content is scanned for suspicious patterns (prompt injection indicators, credential patterns) before requiring user approval. See `backend/infrastructure/tools/security.py`.

## Configuration

Environment variables (`.env`):

```bash
ANTHROPIC_API_KEY=       # Required
GOOGLE_CLIENT_ID=        # Required for Gmail/Calendar
GOOGLE_CLIENT_SECRET=    # Required for Gmail/Calendar
ENCRYPTION_KEY=          # Required for production (credential encryption)
TAVILY_API_KEY=          # Optional, for web search
SERPAPI_KEY=             # Optional, alternative web search
```
