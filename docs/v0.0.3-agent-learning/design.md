# Agent Builder v0.0.3 Design Document

Technical design for implementing the [v0.0.3 PRD](./prd.md).

**Reference:** [LangChain Agent Builder Memory](https://www.langchain.com/conceptual-guides/how-we-built-agent-builders-memory)

---

## Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing deps ...
    "langgraph-checkpoint-sqlite>=2.0.0",
    "python-frontmatter>=1.1.0",
    "slack-sdk>=3.27.0",
]
```

**Note:** No Alembic - using SQLAlchemy's `create_all()` for new tables (consistent with existing v0.0.2 pattern).

---

## Architecture Decisions

### 1. Memory as Virtual Filesystem

**Decision:** Present agent memory as virtual files (stored in SQLite, NOT disk files).

**Why:**
- LLMs work well with filesystem metaphors
- Users understand files and folders
- Enables future export/import portability
- Cleaner than exposing raw database tables

**Virtual Structure (conceptual):**
```
/agents/{agent_id}/
├── AGENTS.md           # Maps to AgentModel.system_prompt
├── tools.json          # Maps to AgentModel.tools relationship
├── skills/             # Maps to skills table
│   ├── skill1.md
│   └── skill2.md
└── knowledge/          # Maps to memory_files table
    ├── preferences.md
    └── contacts.md
```

**Important:** `AGENTS.md` and `tools.json` are read-only virtual mappings from existing SQL data. Only `skills/` and `knowledge/` support write operations via memory tools.

**Mapping Implementation:**
```python
class MemoryFileSystem:
    """Virtual filesystem backed by SQLite tables."""

    async def read(self, agent_id: str, path: str) -> str:
        if path == "AGENTS.md":
            agent = await self.agent_repo.get(agent_id)
            return agent.system_prompt
        elif path == "tools.json":
            agent = await self.agent_repo.get(agent_id)
            return json.dumps([t.model_dump() for t in agent.tools])
        elif path.startswith("skills/"):
            skill = await self.skill_repo.get_by_path(agent_id, path)
            return skill.to_markdown()
        elif path.startswith("knowledge/"):
            file = await self.memory_repo.get(agent_id, path)
            return file.content
        else:
            raise FileNotFoundError(path)
```

---

### 2. HITL Required for All Memory Writes

**Decision:** Agents cannot modify their own memory without user approval.

**Why:**
- Prevents prompt injection attacks from corrupting agent behavior
- Gives users control over what agents learn
- Aligns with LangChain's approach (with optional "yolo mode" later)

**Flow:**
1. Agent invokes `write_memory` tool
2. Tool creates `MemoryEditRequest` record, returns "Waiting for approval"
3. WebSocket sends `memory_edit_request` event to frontend
4. User sees diff (before/after) with suspicious patterns highlighted
5. User approves, edits, or rejects
6. Backend writes to `memory_files` table on approval

**Security: Suspicious Pattern Detection**
```python
import re

SUSPICIOUS_PATTERNS = [
    (r"always\s+(do|send|forward)", "Unconditional action"),
    (r"never\s+(ask|check|verify)", "Bypass verification"),
    (r"ignore\s+(previous|user)", "Ignore instructions"),
    (r"https?://\S+", "Contains URL"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Contains email"),
]

def detect_suspicious_patterns(content: str) -> list[dict]:
    """Return list of suspicious patterns found in content."""
    results = []
    for pattern, reason in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            results.append({"pattern": pattern, "match": match, "reason": reason})
    return results
```

**API Response for HITL:**
```typescript
// WebSocket message: memory_edit_request
{
  type: "memory_edit_request",
  request_id: "mem_123",
  tool_call_id: "call_abc123",
  path: "knowledge/preferences.md",
  operation: "write",
  current_content: "...",  // null if new file
  proposed_content: "...",
  reason: "User prefers bullet points",
  suspicious_flags: [
    {
      "pattern": "https?://\\S+",
      "match": "https://example.com",
      "description": "Contains URL",
      "severity": "warning"  // "warning" or "danger"
    }
  ]
}
```

---

### 3. Persistent Checkpointing

**Decision:** Replace in-memory `MemorySaver` with SQLite-backed checkpointing.

**Why:**
- Conversations survive server restarts
- HITL state persists across sessions
- Required for R1 (conversations persist)

**Implementation:**

`AsyncSqliteSaver.from_conn_string()` returns a context manager, so we manage it via FastAPI lifespan:

```python
# backend/main.py
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from backend.infrastructure.persistence.sqlite.checkpointer import set_checkpointer, clear_checkpointer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... db init ...
    checkpoint_path = data_dir / "checkpoints.db"
    async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
        set_checkpointer(checkpointer)
        yield
        clear_checkpointer()
```

```python
# backend/infrastructure/persistence/sqlite/checkpointer.py
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_checkpointer: AsyncSqliteSaver | None = None

def set_checkpointer(checkpointer: AsyncSqliteSaver) -> None:
    global _checkpointer
    _checkpointer = checkpointer

def get_checkpointer() -> AsyncSqliteSaver:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized")
    return _checkpointer
```

2. **Modify RunAgentUseCase:**
```python
# backend/application/use_cases/run_agent.py

class RunAgentUseCase:
    def __init__(self, ...):
        # REMOVE: self._agents: dict[str, Any] = {}
        self._checkpointer: AsyncSqliteSaver | None = None

    async def _get_checkpointer(self) -> AsyncSqliteSaver:
        if self._checkpointer is None:
            self._checkpointer = await get_checkpointer(settings.database_path)
        return self._checkpointer

    async def get_or_create_agent(self, agent_id: str, thread_id: str):
        # ALWAYS create fresh agent instance with shared checkpointer
        agent_def = await self.agent_repo.get(agent_id)
        tools = await self._create_tools(agent_def)
        checkpointer = await self._get_checkpointer()

        return create_deep_agent(
            model=agent_def.model,
            tools=tools,
            system_message=self._build_system_prompt(agent_def),
            checkpointer=checkpointer,
            interrupt_on=self._get_hitl_tools(agent_def),
        )
```

3. **Enable SQLite WAL mode (in database.py startup):**
```python
async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        await conn.run_sync(Base.metadata.create_all)
```

---

### 4. Skills Following Anthropic Agent Skills Specification

**Decision:** Skills follow the [Anthropic Agent Skills spec](https://agentskills.io/specification) with progressive disclosure.

**Why:**
- Industry standard for AI agent capabilities
- Progressive disclosure reduces system prompt bloat
- Clear spec-compliant naming (lowercase, hyphens, max 64 chars)
- Supports optional fields (license, compatibility, metadata, allowed_tools)

**Spec Compliance:**
- Name validation: lowercase letters, numbers, hyphens only. Max 64 chars.
- Auto-normalization: "PDF Processing" → "pdf-processing"
- YAML frontmatter with required (name, description) and optional fields

**Format:**
```markdown
---
name: professional-email-tone
description: Guidelines for formal business communication. Use when drafting emails to external parties.
license: MIT
compatibility: Requires send_email tool for sending.
allowed-tools: send_email draft_reply
---

When writing professional emails:
- Use formal greetings ("Dear" or "Hello")
- Avoid contractions and slang
- Include clear subject lines
- Sign with full name and title
```

**Architecture: Clean Domain Model with Service Layer**

1. **Skill Entity** (`domain/entities.py`): Pydantic model with auto-normalization
2. **SkillValidator** (`domain/validation/skill_validator.py`): Spec-compliant validation
3. **SkillLoader** (`application/services/skill_loader.py`): Progressive disclosure orchestration
4. **SkillRepository** (`infrastructure/persistence/sqlite/skill_repo.py`): CRUD returning Skill entities

**Progressive Disclosure (3-Stage Loading):**

1. **Stage 1 - Metadata (~100 tokens/skill):** Only name + description injected into system prompt
2. **Stage 2 - Full Instructions:** Agent reads `skills/{name}.md` via memory tools when needed
3. **Stage 3 - Resources:** Future support for scripts/, references/, assets/ directories

```python
# SkillLoader.get_metadata_for_prompt() - Stage 1
async def get_metadata_for_prompt(self, agent_id: str) -> str:
    """Get skills metadata section for system prompt injection."""
    skills = await self.skill_repo.list_by_agent(agent_id)
    if not skills:
        return ""

    section = "\n\n## Available Skills\n\n"
    section += "You have access to the following skills. To use a skill:\n"
    section += "1. Read its full instructions from `skills/{skill-name}.md`\n"
    section += "2. Follow the instructions in the skill file\n"
    section += "3. Prefix your response with `[Using skill: {skill-name}]`\n\n"

    for skill in skills:
        section += f"- **{skill.name}**: {skill.description}\n"

    return section
```

**Database Schema (SkillModel):**
```python
class SkillModel(Base):
    __tablename__ = "skills"
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"))
    name = Column(String(64), nullable=False)  # Spec: max 64 chars
    description = Column(Text, nullable=False)  # Spec: max 1024 chars
    instructions = Column(Text, nullable=False)

    # Anthropic Agent Skills spec optional fields
    license = Column(String, nullable=True)
    compatibility = Column(String(500), nullable=True)
    skill_metadata = Column(JSON, default=dict)
    allowed_tools = Column(JSON, default=list)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

**Future Extensibility:**
- File attachments (scripts/, references/, assets/) can be added in v0.0.4+
- SkillLoader service already has clean separation for extending to Stage 3

---

### 5. Slack as Built-in Integration

**Decision:** Add Slack tools alongside Gmail/Calendar in builtin tools.

**Scope:** Slack IS in scope for v0.0.3. The "fake tools" bug fix refers to Web and Notes tools only.

**Tools:**
```python
# backend/infrastructure/tools/builtin_slack.py

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def create_slack_tools(token: str) -> list:
    """Create Slack tools with the provided bot token."""
    client = WebClient(token=token)

    @tool
    def list_slack_channels(limit: int = 100) -> list[dict]:
        """
        List available Slack channels.

        Args:
            limit: Maximum number of channels to return (default 100)

        Returns:
            List of channels with id, name, and is_private fields
        """
        response = client.conversations_list(limit=limit, types="public_channel,private_channel")
        return [
            {"id": ch["id"], "name": ch["name"], "is_private": ch["is_private"]}
            for ch in response["channels"]
        ]

    @tool(requires_approval=True)
    def send_slack_message(channel_id: str, text: str) -> dict:
        """
        Send a message to a Slack channel. Requires user approval.

        Args:
            channel_id: The channel ID (e.g., "C1234567890")
            text: The message text to send

        Returns:
            Message details including timestamp
        """
        response = client.chat_postMessage(channel=channel_id, text=text)
        return {"ok": response["ok"], "ts": response["ts"], "channel": response["channel"]}

    return [list_slack_channels, send_slack_message]
```

**Required Slack Bot Scopes:**
- `channels:read` - List public channels
- `groups:read` - List private channels
- `chat:write` - Send messages

**Token Storage:**
- Manual token input via UI (no OAuth for MVP)
- Token stored encrypted in `credentials` table (provider="slack")
- Reuse existing `CredentialStore` infrastructure

---

## Memory Tool Integration

### Tool Registration

Memory tools are registered as builtin tools, always available to all agents:

```python
# backend/infrastructure/tools/builtin_memory.py

def create_memory_tools(memory_fs: MemoryFileSystem, agent_id: str) -> list:
    """Create memory tools for an agent."""

    @tool(requires_approval=True)
    def write_memory(path: str, content: str, reason: str) -> str:
        """
        Propose saving information to agent memory for user approval.

        Use this when you learn something worth remembering:
        - User preferences (formatting, tone, contacts)
        - Corrections to your behavior
        - Facts the user wants you to remember

        Args:
            path: Where to save (e.g., "knowledge/preferences.md")
            content: What to save (markdown format)
            reason: Why you want to remember this

        Returns:
            Status message
        """
        # Validate path
        if not memory_fs.validate_path(agent_id, f"/agents/{agent_id}/{path}"):
            return f"Error: Invalid path '{path}'"

        # Create pending request (does NOT write yet)
        request = memory_fs.create_edit_request(
            agent_id=agent_id,
            path=path,
            operation="write",
            proposed_content=content,
            reason=reason,
        )
        return f"Memory update proposed. Waiting for user approval. (Request ID: {request.id})"

    @tool
    def read_memory(path: str) -> str:
        """
        Read from agent memory.

        Args:
            path: What to read (e.g., "knowledge/preferences.md")

        Returns:
            File contents or error message
        """
        try:
            return memory_fs.read(agent_id, path)
        except FileNotFoundError:
            return f"No memory file at '{path}'"

    @tool
    def list_memory(directory: str = "knowledge") -> list[str]:
        """
        List files in agent memory.

        Args:
            directory: Which directory to list ("skills" or "knowledge")

        Returns:
            List of file paths
        """
        return memory_fs.list_files(agent_id, directory)

    return [write_memory, read_memory, list_memory]
```

### HITL Flow for Memory Tools

Memory tools use the existing HITL infrastructure with enhanced UI:

```python
# backend/api/v1/chat.py - modify handle_message()

async def handle_message(websocket, agent_id, thread_id, message):
    # ... existing code ...

    async for event in agent.astream_events(input_messages, config, version="v2"):
        if event.get("event") == "on_tool_start":
            tool_name = event["name"]
            tool_args = event["data"]["input"]

            if tool_name == "write_memory":
                # Create memory edit request
                request = await memory_repo.create_edit_request(
                    agent_id=agent_id,
                    path=tool_args["path"],
                    operation="write",
                    proposed_content=tool_args["content"],
                    reason=tool_args["reason"],
                )

                # Detect suspicious patterns
                suspicious = detect_suspicious_patterns(tool_args["content"])

                # Get current content for diff
                current = await memory_fs.read_safe(agent_id, tool_args["path"])

                # Send to frontend
                await websocket.send_json({
                    "type": "memory_edit_request",
                    "request_id": request.id,
                    "path": tool_args["path"],
                    "operation": "write",
                    "current_content": current,
                    "proposed_content": tool_args["content"],
                    "reason": tool_args["reason"],
                    "suspicious_flags": suspicious,
                })

                # Wait for approval (same pattern as existing HITL)
                # ... existing HITL wait logic ...
```

---

## Wizard Conversation Persistence

### Problem
Wizard stores conversation in memory (`self.conversation_state: dict`), lost on server restart.

### Solution
Use existing `conversation_messages` table with special agent_id.

```python
# backend/application/builder.py

WIZARD_AGENT_ID = "system:builder-wizard"

class BuilderWizard:
    def __init__(self, agent_repo, conversation_repo):
        self.agent_repo = agent_repo
        self.conversation_repo = conversation_repo
        # REMOVE: self.conversation_state: dict = {}

    async def get_conversation_history(self, thread_id: str) -> list[dict]:
        """Load conversation from database."""
        messages = await self.conversation_repo.get_messages(
            agent_id=WIZARD_AGENT_ID,
            thread_id=thread_id,
            limit=50,
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    async def save_message(self, thread_id: str, role: str, content: str):
        """Save message to database."""
        await self.conversation_repo.save_message(
            agent_id=WIZARD_AGENT_ID,
            thread_id=thread_id,
            role=role,
            content=content,
        )

    async def chat(self, thread_id: str, user_message: str) -> str:
        # Load history from DB
        history = await self.get_conversation_history(thread_id)

        # Save user message
        await self.save_message(thread_id, "user", user_message)

        # ... existing chat logic ...

        # Save assistant response
        await self.save_message(thread_id, "assistant", response)

        return response
```

---

## Database Schema Changes

### New Tables (via SQLAlchemy create_all)

```python
# backend/infrastructure/persistence/sqlite/models.py

class MemoryFileModel(Base):
    __tablename__ = "memory_files"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    path = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String, default="text/markdown")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_memory_files_agent_path", "agent_id", "path", unique=True),
    )


class MemoryEditRequestModel(Base):
    __tablename__ = "memory_edit_requests"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    path = Column(String, nullable=False)
    operation = Column(String, nullable=False)  # 'write', 'append', 'delete'
    proposed_content = Column(Text)
    previous_content = Column(Text)  # For undo support
    reason = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)


class SkillModel(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    instructions = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_skills_agent_name", "agent_id", "name", unique=True),
    )
```

### LangGraph Checkpoint Tables

Created automatically by `AsyncSqliteSaver` on first use:
- `checkpoints`
- `checkpoint_blobs`
- `checkpoint_writes`

---

## File Locations

| Component | Location |
|-----------|----------|
| Checkpointer | `backend/infrastructure/persistence/sqlite/checkpointer.py` |
| MemoryFileSystem | `backend/infrastructure/persistence/sqlite/memory_fs.py` |
| MemoryRepository | `backend/infrastructure/persistence/sqlite/memory_repo.py` |
| SkillRepository | `backend/infrastructure/persistence/sqlite/skill_repo.py` |
| Memory tools | `backend/infrastructure/tools/builtin_memory.py` |
| Slack tools | `backend/infrastructure/tools/builtin_slack.py` |
| New models | `backend/infrastructure/persistence/sqlite/models.py` (extend) |
| Tool registry | `backend/infrastructure/tools/registry.py` (extend) |
| Settings | `backend/config.py` (already has `database_path`) |

---

## Initialization & Wiring

### Database Initialization

Modify existing `backend/infrastructure/persistence/sqlite/database.py`:

```python
from sqlalchemy import text

async def init_db():
    """Initialize database with WAL mode and create tables."""
    async with engine.begin() as conn:
        # Enable WAL mode for better concurrency
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        # Create all tables including new memory/skills tables
        await conn.run_sync(Base.metadata.create_all)
```

### MemoryFileSystem Initialization

Add to `backend/api/dependencies.py`:

```python
from backend.infrastructure.persistence.sqlite.memory_fs import MemoryFileSystem

async def get_memory_fs(session: AsyncSession = Depends(get_session)) -> MemoryFileSystem:
    """Create MemoryFileSystem per-request to avoid stale session references."""
    return MemoryFileSystem(
        session=session,
        agent_repo=SQLiteAgentRepository(session),
        skill_repo=SkillRepository(session),
        memory_repo=MemoryRepository(session),
    )
```

### Memory Tools Registration

Modify `backend/infrastructure/tools/registry.py`:

```python
class ToolRegistryImpl:
    def __init__(self, memory_fs: MemoryFileSystem):
        self.memory_fs = memory_fs

    def create_tools(self, agent_id: str, configs: list[ToolConfig], credentials: dict) -> list:
        tools = []

        # Always add memory tools
        tools.extend(create_memory_tools(self.memory_fs, agent_id))

        # Add configured tools
        for config in configs:
            if config.source == "builtin":
                if config.name == "gmail":
                    tools.extend(create_gmail_tools(credentials.get("google")))
                elif config.name == "calendar":
                    tools.extend(create_calendar_tools(credentials.get("google")))
                elif config.name == "slack":
                    tools.extend(create_slack_tools(credentials.get("slack")))

        return tools
```

---

## Frontend Specifications

### Skills Panel (Agent Editor)

**Location:** Add new panel in `frontend/src/components/panels/SkillsPanel.tsx`

**UI Elements:**
- Section header: "Skills"
- List of skills with name and description
- "Add Skill" button
- Each skill row has: name, description preview, edit button, delete button

**Add/Edit Skill Modal:**
```typescript
interface SkillFormData {
  name: string;        // Required, text input
  description: string; // Required, text input
  instructions: string; // Required, markdown textarea
}
```

**API Endpoints:**

```typescript
// GET /api/v1/agents/{id}/skills
// Response: 200 OK
{ skills: [{ id, name, description, instructions, created_at, updated_at }] }

// POST /api/v1/agents/{id}/skills
// Request: { name, description, instructions }
// Response: 201 Created | 400 Bad Request | 409 Conflict (duplicate name)
{ skill: { id, name, description, instructions, created_at } }

// PUT /api/v1/agents/{id}/skills/{skillId}
// Request: { name?, description?, instructions? }
// Response: 200 OK | 404 Not Found
{ skill: { id, name, description, instructions, updated_at } }

// DELETE /api/v1/agents/{id}/skills/{skillId}
// Response: 204 No Content | 404 Not Found
```

### Memory View Panel (Agent Editor)

**Location:** Add new panel in `frontend/src/components/panels/MemoryPanel.tsx`

**UI Elements:**
- Section header: "Knowledge"
- List of memory files (path, last updated)
- Each row has: file path, updated timestamp, delete button
- Click row to view content in read-only modal

**API Endpoints:**

```typescript
// GET /api/v1/agents/{id}/memory
// Response: 200 OK
{ files: [{ path, content_type, created_at, updated_at, size_bytes }] }

// GET /api/v1/agents/{id}/memory/{path}
// Response: 200 OK | 404 Not Found
{ path, content, content_type, updated_at }

// DELETE /api/v1/agents/{id}/memory/{path}
// Response: 204 No Content | 404 Not Found
```

### Slack Token Input

**Location:** Add to Settings page or Agent Toolbox panel

**UI Elements:**
- Section: "Slack Integration"
- Input field: "Bot Token" (password type, masked)
- Help text: "Get your bot token from Slack App settings. Required scopes: channels:read, groups:read, chat:write"
- Save button
- Status indicator: "Connected" / "Not configured"

**API Endpoints:**

```typescript
// POST /api/v1/credentials/slack
// Request: { token: "xoxb-..." }
// Response: 200 OK | 400 Bad Request (invalid token format) | 401 Unauthorized (token rejected by Slack)
{ configured: true }

// GET /api/v1/credentials/slack/status
// Response: 200 OK
{ configured: boolean }

// DELETE /api/v1/credentials/slack
// Response: 204 No Content
```

### Memory Edit Request UI

**Location:** Extend `frontend/src/components/chat/HITLApproval.tsx`

**UI Changes for memory requests:**
- Title: "Memory Update Request"
- Show: path, reason, diff view (current vs proposed)
- Highlight suspicious patterns in red/yellow
- Tooltip on highlighted patterns explaining the risk
- Buttons: Approve, Edit, Reject

**WebSocket Protocol for Memory HITL:**

```typescript
// Server → Client: Memory edit request (agent pauses)
{
  type: "memory_edit_request",
  request_id: "mem_abc123",
  tool_call_id: "call_xyz789",
  path: "knowledge/preferences.md",
  operation: "write",
  current_content: "...",  // null if new file
  proposed_content: "...",
  reason: "User prefers bullet points",
  suspicious_flags: [
    {
      pattern: "https?://\\S+",
      match: "https://example.com",
      description: "Contains URL",
      severity: "warning"  // "warning" or "danger"
    }
  ]
}

// Client → Server: User decision
{
  type: "memory_edit_decision",
  request_id: "mem_abc123",
  decision: "approve" | "reject" | "edit",
  edited_content?: "..."  // Only if decision == "edit"
}

// Server → Client: Confirmation (then agent resumes)
{
  type: "memory_edit_complete",
  request_id: "mem_abc123",
  success: true,
  path: "knowledge/preferences.md"
}
```

**Memory Size Validation:**
- Checked on `write_memory` tool invocation (before HITL)
- If content > 100KB: Tool returns error immediately, no HITL triggered
- If total agent memory > 100KB after write: Warning in HITL UI, still allows approval

---

## Bug Fixes Required

| Bug | Fix | File Location | Priority |
|-----|-----|---------------|----------|
| Fake tools in wizard | Update tools list in wizard prompt. Keep Gmail, Calendar, Slack. | `backend/config/wizard_prompt.md`, `backend/config/tools.json` | P0 |
| Research Assistant wrong data | Update template in seed data or DB | `backend/infrastructure/templates/` | P1 |
| Create New Agent button invisible | Check CSS contrast/z-index | `frontend/src/pages/AgentList.tsx` | P0 |
| Wizard state lost on refresh | Use `conversation_messages` table with `agent_id="system:builder-wizard"` | `backend/application/builder.py` | P0 |

---

## Memory Conflict Detection (Deferred)

**Decision:** Defer semantic conflict detection to v0.0.4.

**v0.0.3 behavior:** Last-write-wins for same path. No automatic conflict detection.

**Rationale:**
- User approval via HITL provides opportunity to review
- Conflict detection requires semantic understanding (complex)
- Can add in v0.0.4 based on user feedback

---

## Implementation Checklist

### Phase 1: Infrastructure (P0) ✅ COMPLETE
- [x] Add dependencies to `pyproject.toml`
- [x] Implement `AsyncSqliteSaver` checkpointer via FastAPI lifespan
- [x] Modify `RunAgentUseCase` to remove agent caching
- [x] Add new SQLAlchemy models (MemoryFile, MemoryEditRequest, Skill, WizardConversation)
- [x] Enable SQLite WAL mode in database init

### Phase 2: Memory System (P0) ✅ COMPLETE
- [x] Implement `MemoryFileSystem` service
- [x] Implement `MemoryRepository` for memory_files table
- [x] Create memory tools (`write_memory`, `read_memory`, `list_memory`)
- [x] Wire memory tools to HITL flow via WebSocket
- [x] Add suspicious pattern detection with severity levels
- [x] Add frontend MemoryEditRequest UI with diff view

### Phase 3: Skills (P1) ✅ COMPLETE
- [x] Implement `SkillRepository` with frontmatter parsing
- [x] Add Skills panel to agent editor UI (frontend)
- [x] Modify `_build_system_prompt` to inject skills

### Phase 4: Slack (P1) ✅ COMPLETE
- [x] Implement `create_slack_tools()` in `builtin_slack.py`
- [x] Register Slack tools in `ToolRegistryImpl`
- [x] Add Slack token input UI (frontend)
- [x] Wire token to `CredentialStore` (provider="slack")
- [x] Update wizard to include Slack after tools are ready

### Phase 5: Bug Fixes (P0) ✅ COMPLETE
- [x] Remove fake tools (Web, Notes) from wizard
- [x] Fix Create button visibility (verified visible)
- [x] Persist wizard conversation state
- [x] Fix Research Assistant template description

### Phase 6: Testing (P0) ✅ COMPLETE
- [x] Path traversal attack tests
- [x] Content size validation tests
- [x] Suspicious pattern detection tests
- [x] v0.0.2 regression tests (46 tests passing)
- [x] E2E tests for core workflow

### Phase 7: Security Hardening ✅ COMPLETE
- [x] Fix TOCTOU vulnerability in memory decision handler
- [x] Add agent ID authorization check
- [x] Fix content size validation bypass on approve
- [x] Fix frontend pattern highlighting (use match instead of pattern)
- [x] Add severity field to suspicious patterns

---

## Recommended Instruction Patterns

Based on [LangSmith Agent Builder Analysis](../product-research/insights.md), quality differences are **instruction-driven, not model-driven**. Apply these patterns to agent system prompts:

### Communication Style Instructions

```markdown
## Communication Guidelines

### Transparency
- Use ✅ for capabilities you have
- Use ⚠️ for limitations or things requiring manual intervention
- Be explicit about what you can and cannot do automatically

### Structured Options
When multiple approaches exist, present them as:
A) [First option] - [brief description]
B) [Second option] - [brief description]
C) [Third option] - [brief description]

Ask: "What would you prefer?"

### Workflow Explanation
When explaining multi-step processes, use numbered lists:
1. First step description
2. Second step description
3. ...

### Expectation Setting
When a capability has limitations, explain:
- What works now
- What requires user action
- What could be automated in the future
```

### Self-Improvement Instructions

```markdown
## Learning from Feedback

When user corrects your behavior:
1. Acknowledge the correction
2. Explain what you're updating in memory
3. Use `write_memory` tool with clear reason
4. Confirm the update was proposed

Example:
"I see you prefer [X] over [Y]. Let me save this preference so I remember next time."
[write_memory call]
"I've proposed saving this preference. Once you approve, I'll use [X] in future interactions."
```

### Proactive Behavior Instructions

```markdown
## Proactive Suggestions

- When you notice repeated patterns, suggest creating a skill
- When capabilities are limited, explain what tools could help
- When workflows are manual, suggest automation opportunities

Format suggestions as:
"For [use case], I could:
- [Automation option 1]
- [Automation option 2]

Would any of these be helpful?"
```

### Template Integration

Add these patterns to `backend/config/wizard_prompt.md` for wizard-created agents:

```python
AGENT_BEHAVIOR_PATTERNS = """
## Communication Style
- Use ✅ for capabilities, ⚠️ for limitations
- Present options as A) B) C) when multiple paths exist
- Explain workflows step-by-step with numbered lists
- Set expectations about manual vs automated actions

## Self-Improvement
- When corrected, acknowledge and propose memory update
- Explain what you're learning and why
- Confirm updates were proposed

## Proactive Suggestions
- Suggest skills for repeated patterns
- Explain tool capabilities and limitations
- Propose automation opportunities
"""
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AsyncSqliteSaver not compatible | Test import immediately after adding dependency |
| Checkpoint performance impact | Enable WAL mode, monitor p99 latency |
| Prompt injection via memory | Suspicious pattern detection + HITL highlighting |
| Memory size explosion | Enforce 100KB limit per agent, warn at 80% |
| Concurrent access conflicts | SQLite WAL mode handles this; single writer per agent |
| Slack API errors | Wrap all Slack calls in try/except, return user-friendly errors |

---

*v0.0.3 | January 17, 2026*
