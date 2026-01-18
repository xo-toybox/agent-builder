# Agent Builder v0.0.3 User Journey

Complete walkthrough of a user journey with architecture deep-dive.

**Related:** [PRD](./prd.md) | [Design](./design.md)

---

## Example Scenario

**User Goal:** Create an email curator agent that summarizes newsletters, learns preferences, and remembers past summaries.

---

## Phase 1: Agent Creation via Builder Wizard

### User Action
Opens `/agent-builder` and types:
> "Create an email curator that summarizes my newsletters and learns my reading preferences"

### Frontend Flow

```
AgentBuilder.tsx
    │
    ├─ useBuilderChat() hook initializes
    │   └─ WebSocket connects to /api/v1/wizard/chat
    │
    └─ User message sent as JSON:
        { "type": "message", "content": "Create an email curator..." }
```

**Key file:** `frontend/src/pages/AgentBuilder.tsx`
- Lines 16-41: Smart auto-scroll that respects user scrolling
- Lines 46-48: Agent creation detection via "Created agent" in response
- Lines 51-53: Auto-redirect to agent page after creation

### Backend Flow

```
api/v1/wizard.py:wizard_chat()
    │
    ├─ Accept WebSocket connection
    ├─ Generate unique thread_id (or reuse from message)
    │
    └─ BuilderWizard.stream_chat(thread_id, message)
            │
            ├─ Load conversation history from DB
            │   └─ Uses agent_id="system:builder-wizard"
            │
            ├─ Call Claude via Anthropic SDK with tools:
            │   ├─ create_agent (@beta_tool, closure with repo)
            │   ├─ list_available_tools (@beta_tool)
            │   └─ list_templates (@beta_tool)
            │
            ├─ Claude decides to call create_agent tool
            │   └─ Tool executes → AgentDefinition saved to SQLite
            │
            └─ Yield streaming events:
                token → tool_call → tool_result → token → complete
```

**Key files:**
- `backend/application/builder.py` - BuilderWizard class, tool definitions
- `backend/config/tools.json` - Available tools catalog
- `backend/config/templates.json` - Agent templates
- `backend/config/wizard_prompt.md` - Wizard system prompt

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Wizard is a meta-agent** | Uses same Claude+tools pattern as user agents. Dogfooding. |
| **Wizard state in DB** | Survives server restarts. Uses `agent_id="system:builder-wizard"`. |
| **Raw Anthropic SDK over LangChain** | `@beta_tool` decorator auto-generates schemas. Fewer dependencies. |

### WebSocket Message Flow

```
Client → Server: { type: "message", content: "Create an email curator..." }

Server → Client: { type: "token", content: "I'll create " }
Server → Client: { type: "token", content: "an email curator..." }
Server → Client: { type: "tool_call", name: "create_agent", args: {...} }
Server → Client: { type: "tool_result", result: "✅ Created agent 'Email Curator' (ID: abc-123)" }
Server → Client: { type: "token", content: "Done! Your agent..." }
Server → Client: { type: "complete" }
```

---

## Phase 2: User Sends Chat Message

### User Action
After redirect, user types in agent chat:
> "Summarize my unread newsletters from this week"

### Frontend Flow

```
ChatPanel.tsx
    │
    ├─ useWebSocket(agentId) hook initializes
    │   └─ WebSocket connects to /api/v1/chat/{agent_id}
    │
    └─ Message sent:
        { "type": "message", "content": "Summarize my unread newsletters..." }
```

**Key file:** `frontend/src/hooks/useWebSocket.ts`
- Lines 4-8: Dynamic WebSocket URL construction
- Lines 64-200: Message type handling (token, tool_call, hitl_interrupt, memory_edit_request)

### Backend Flow

```
api/v1/chat.py:agent_chat()
    │
    ├─ Receive message
    │
    └─ _run_agent(agent_id, thread_id, user_message)
            │
            └─ RunAgentUseCase.run()
                    │
                    ├─ get_or_create_agent()
                    │   │
                    │   ├─ Load AgentDefinition from SQLite
                    │   │
                    │   ├─ Check credentials (Google OAuth, Slack token)
                    │   │
                    │   ├─ ToolRegistry.create_tools():
                    │   │   ├─ Memory tools (always added)
                    │   │   ├─ Gmail tools (if credentials exist)
                    │   │   ├─ Slack tools (if token exists)
                    │   │   └─ MCP tools (if configured)
                    │   │
                    │   ├─ Get HITL tool list:
                    │   │   ├─ Tools with requires_hitl=True in metadata
                    │   │   └─ Tools with hitl_enabled=True in config
                    │   │
                    │   ├─ Build system prompt:
                    │   │   ├─ Base agent prompt
                    │   │   └─ Injected skills section
                    │   │
                    │   └─ create_deep_agent():
                    │       ├─ model: claude-sonnet-4-20250514
                    │       ├─ tools: [list_emails, get_email, read_memory, ...]
                    │       ├─ checkpointer: AsyncSqliteSaver (persistent)
                    │       └─ interrupt_on: ["send_email", "write_memory"]
                    │
                    └─ agent.astream_events(input_messages, config, version="v2")
                            │
                            └─ Yield LangGraph events
```

**Key file:** `backend/application/use_cases/run_agent.py`
- Lines 51-123: `get_or_create_agent` - agent factory with tool injection
- Lines 125-162: `_build_system_prompt` - skill injection into context
- Lines 164-189: `run` - streaming event loop

### Tool Registration Architecture

```
ToolRegistryImpl.create_tools(configs, credentials, agent_id)
    │
    ├─ Memory tools (always):
    │   └─ create_memory_tools(memory_fs, agent_id)
    │
    ├─ Gmail tools (if credentials):
    │   └─ create_gmail_tools(credentials)
    │
    ├─ Calendar tools (if credentials):
    │   └─ create_calendar_tools(credentials)
    │
    ├─ Slack tools (if token):
    │   └─ create_slack_tools(token)
    │
    ├─ Web tools:
    │   └─ create_web_tools()
    │
    └─ MCP tools (if configured):
        └─ _get_mcp_tools(server_id)
```

Tool metadata (names, descriptions, categories) loaded from `backend/config/tools.json`.

**Key file:** `backend/infrastructure/tools/registry.py`

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Tools created per-request** | Ensures fresh credentials, avoids stale state. |
| **Memory tools always available** | Core feature, not opt-in. Enables learning by default. |
| **HITL via interrupt_on** | LangGraph's native pattern. Agent pauses, state frozen. |
| **Skills injected into prompt** | Simple, reliable. Agent sees skills as part of its instructions. |

---

## Phase 3: Agent Executes Tools

### Agent Calls list_emails

The agent decides to fetch the user's emails:

```
LangGraph Agent
    │
    └─ Tool call: list_emails(query="is:unread label:newsletter newer_than:7d")
```

### Streaming Events

```
Server → Client: { type: "token", content: "I'll check your emails..." }
Server → Client: {
    type: "tool_call",
    name: "list_emails",
    args: { query: "is:unread label:newsletter newer_than:7d" }
}
Server → Client: {
    type: "tool_result",
    name: "list_emails",
    result: [{ id: "msg1", subject: "TechCrunch Daily", ... }, ...]
}
Server → Client: { type: "token", content: "Found 5 newsletters. Let me read them..." }
```

### Agent Reads Emails and Prepares Summary

```
LangGraph Agent
    │
    ├─ Tool call: get_email(message_id="msg1") → Full email content
    ├─ Tool call: get_email(message_id="msg2") → Full email content
    │   ...
    │
    └─ Agent generates summary text
```

---

## Phase 4: HITL Interrupt on write_memory

### Agent Proposes Memory Write

The agent wants to save the summary for future reference:

```
LangGraph Agent
    │
    └─ Tool call: write_memory(
           path="knowledge/summaries/2026-01-18.md",
           content="## Newsletter Summary - Jan 18, 2026\n\n### TechCrunch...",
           reason="Saving newsletter summary for future reference"
       )
```

### LangGraph Interrupt

The agent hits the `interrupt_on` condition and **pauses**:

```
create_deep_agent(
    ...
    interrupt_on=["send_email", "write_memory"]  ← Agent pauses here
)
```

State is frozen in the checkpointer. The agent will resume when HITL decision is received.

### Backend Sends HITL Request

**Key file:** `backend/api/v1/chat.py`
- Lines 246-307: `_send_hitl_interrupt`

```python
# Detect write_memory in pending tool calls
state = agent.get_state(config)
if state.next:  # Agent is waiting
    for msg in reversed(state.values["messages"]):
        if hasattr(msg, "tool_calls"):
            for tool_call in msg.tool_calls:
                if tool_call["name"] == "write_memory":
                    # Get current content for diff
                    current = await memory_fs.read_safe(agent_id, path)

                    # Security: Detect suspicious patterns
                    flags = detect_suspicious_patterns(content)

                    # Create edit request in DB
                    edit_request = await memory_edit_repo.create(...)

                    # Send to frontend
                    await websocket.send_json({
                        "type": "memory_edit_request",
                        ...
                    })
```

### WebSocket Message

```json
{
  "type": "memory_edit_request",
  "request_id": "mem_abc123",
  "tool_call_id": "call_xyz789",
  "path": "knowledge/summaries/2026-01-18.md",
  "current_content": null,
  "proposed_content": "## Newsletter Summary - Jan 18, 2026\n\n### TechCrunch...",
  "reason": "Saving newsletter summary for future reference",
  "suspicious_flags": []
}
```

### Suspicious Pattern Detection

**Key file:** `backend/infrastructure/tools/security.py`

```python
SUSPICIOUS_PATTERNS = [
    (r"always\s+(do|send|forward)", "Unconditional action", "warning"),
    (r"never\s+(ask|check|verify)", "Bypass verification", "danger"),
    (r"ignore\s+(previous|user)", "Ignore instructions", "danger"),
    (r"https?://\S+", "Contains URL", "warning"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Contains email", "warning"),
]
```

If patterns match, they appear in `suspicious_flags` with severity levels.

### Frontend Displays Diff

**Key file:** `frontend/src/components/chat/MemoryEditApproval.tsx`

```
┌─────────────────────────────────────────────────────┐
│ Memory Update Request                               │
├─────────────────────────────────────────────────────┤
│ Path: knowledge/summaries/2026-01-18.md             │
│ Reason: Saving newsletter summary for future ref... │
├─────────────────────────────────────────────────────┤
│ Current: (empty - new file)                         │
├─────────────────────────────────────────────────────┤
│ Proposed:                                           │
│ ## Newsletter Summary - Jan 18, 2026                │
│                                                     │
│ ### TechCrunch Daily                                │
│ - AI startup raises $50M...                         │
│ ...                                                 │
├─────────────────────────────────────────────────────┤
│ [Reject]  [Edit]  [Approve]                         │
└─────────────────────────────────────────────────────┘
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **All memory writes require HITL** | Prevents prompt injection from corrupting agent memory. |
| **Diff view (current vs proposed)** | User sees exactly what changes. Transparency. |
| **Suspicious pattern detection** | Defense-in-depth. User sees warnings for risky content. |
| **Edit option** | User can fix content before approval. |

---

## Phase 5: User Approves Memory Write

### User Action
User reviews the diff and clicks **[Approve]**

### Frontend Sends Decision

```json
{
  "type": "memory_edit_decision",
  "request_id": "mem_abc123",
  "tool_call_id": "call_xyz789",
  "decision": "approve"
}
```

### Backend Processes Decision

**Key file:** `backend/api/v1/chat.py`
- Lines 309-452: `_handle_memory_decision`

```python
async def _handle_memory_decision(message, agent_id, thread_id, ...):
    request_id = message.get("request_id")
    decision = message.get("decision")

    # Security: Verify agent ID matches
    edit_request = await memory_edit_repo.get(request_id)
    if edit_request.get("agent_id") != agent_id:
        return {"error": "Unauthorized"}

    if decision == "approve":
        # Write to memory
        await memory_repo.save(agent_id, path, content, reason)
        await memory_edit_repo.resolve(request_id, "approved")

        # Notify frontend
        await websocket.send_json({
            "type": "memory_edit_complete",
            "request_id": request_id,
            "success": True,
            "path": path
        })

    # Resume agent with HITL decision
    async for event in run_agent.resume(agent_id, thread_id, tool_call_id, "approve"):
        # Stream remaining events
```

### Agent Resumes

The agent receives the HITL decision as a tool result:

```
Tool result for write_memory: "Memory saved successfully"
```

Agent continues execution, generating its final response.

### WebSocket Messages

```
Server → Client: {
    type: "memory_edit_complete",
    request_id: "mem_abc123",
    success: true,
    path: "knowledge/summaries/2026-01-18.md"
}
Server → Client: { type: "token", content: "I've saved the summary. " }
Server → Client: { type: "token", content: "Here's what I found..." }
Server → Client: { type: "complete" }
```

### Security Checks

| Check | Location | Purpose |
|-------|----------|---------|
| **Agent ID verification** | `chat.py:320` | Prevent cross-agent memory manipulation |
| **Path validation** | `memory_fs.py:45` | Prevent path traversal attacks |
| **Content size limit** | `memory_repo.py:67` | Prevent memory exhaustion (100KB limit) |
| **Pattern detection** | `security.py:25` | Flag suspicious content |

---

## Phase 6: User Adds Skills

### User Action
User clicks the **+** button in the SKILLS section to add a custom skill.

### Frontend Flow

```
SkillsPanel.tsx
    │
    ├─ Click "+" → setShowCreateForm(true)
    │
    ├─ CreateSkillForm renders:
    │   ├─ Name input (e.g., "Newsletter Preferences")
    │   ├─ Description input
    │   └─ Instructions textarea
    │
    └─ Submit → POST /api/v1/agents/{agent_id}/skills
            │
            └─ On success → fetchSkills() → UI updates
```

**Key file:** `frontend/src/components/panels/SkillsPanel.tsx`
- Lines 42-60: `handleCreateSkill` - POST to API
- Lines 190-256: `CreateSkillForm` - form UI

### Backend Flow

```
api/v1/skills.py:create_skill()
    │
    ├─ Normalize skill name (lowercase, hyphens)
    │   └─ "Newsletter Preferences" → "newsletter-preferences"
    │
    ├─ Check for duplicate name (409 if exists)
    │
    └─ skill_repo.create()
            │
            └─ Insert into SQLite skills table
```

**Key file:** `backend/api/v1/skills.py`
- Lines 103-137: `create_skill` endpoint

### Skill Data Model

```json
{
  "id": "skill_abc123",
  "name": "newsletter-preferences",
  "description": "User's content preferences for newsletter summaries",
  "instructions": "Prioritize AI and tech startup news. Avoid crypto content.",
  "license": null,
  "compatibility": null,
  "metadata": null,
  "allowed_tools": null,
  "created_at": "2026-01-18T23:30:00Z",
  "updated_at": "2026-01-18T23:30:00Z"
}
```

### Progressive Disclosure (Agent Skills Spec)

Skills use Anthropic's three-stage progressive disclosure model:

**Stage 1: Metadata in System Prompt**
```
SkillLoader.get_metadata_for_prompt(agent_id)
    │
    └─ Returns compact section (~100 tokens/skill):

## Available Skills

You have access to the following skills. To use a skill:
1. Read its full instructions from `skills/{skill-name}.md` using the read_memory tool
2. Follow the instructions in the skill file
3. Prefix your response with `[Using skill: {skill-name}]`

- **newsletter-preferences**: User's content preferences for newsletter summaries
```

**Stage 2: Full Instructions On-Demand**
```
Agent reads skills/newsletter-preferences.md via read_memory
    │
    └─ SkillLoader.get_full_instructions(agent_id, "newsletter-preferences")
            │
            └─ Returns markdown with YAML frontmatter:

---
name: newsletter-preferences
description: User's content preferences for newsletter summaries
---
Prioritize AI and tech startup news. Avoid crypto content.
Focus on actionable insights.
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Progressive disclosure** | Minimizes prompt size. Agent loads full instructions only when needed. |
| **Name normalization** | Spec compliance. "My Skill" → "my-skill" for filesystem-safe paths. |
| **REST API (not WebSocket)** | Skills are static config, no streaming needed. Simpler implementation. |
| **Injected into system prompt** | Skills become part of agent's identity and instructions. |

---

## Architecture Summary

### System Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
├─────────────────────────────────────────────────────────────────┤
│  AgentBuilder.tsx ←→ useBuilderChat.ts (wizard websocket)       │
│  ChatPanel.tsx    ←→ useWebSocket.ts   (agent chat websocket)   │
│  MemoryEditApproval.tsx (HITL UI)                               │
│  SkillsPanel.tsx (skills CRUD)                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ WebSocket
┌───────────────────────────▼─────────────────────────────────────┐
│                     BACKEND (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│  api/v1/wizard.py  ─────→ BuilderWizard (meta-agent)            │
│  api/v1/chat.py    ─────→ RunAgentUseCase                       │
│  api/v1/skills.py  ─────→ Skills CRUD REST API                  │
│  api/dependencies.py      (DI container)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    APPLICATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  builder.py         : BuilderWizard (creates agents)            │
│  run_agent.py       : RunAgentUseCase                           │
│    ├─ get_or_create_agent() → deepagents.create_deep_agent()    │
│    ├─ run() → astream_events()                                  │
│    └─ resume() → inject HITL decision, continue                 │
│  services/skill_loader.py : SkillLoader (progressive disclosure)│
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  tools/registry.py  : ToolRegistryImpl (unified tool factory)   │
│  tools/builtin_*.py : Gmail, Memory, Slack, Web tools           │
│  tools/security.py  : detect_suspicious_patterns()              │
│  persistence/       : SQLite repos (agents, memory, credentials)│
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

```
User Input
    │
    ▼
WebSocket (JSON messages)
    │
    ▼
FastAPI Endpoint (chat.py / wizard.py)
    │
    ▼
Use Case (RunAgentUseCase / BuilderWizard)
    │
    ├─► Tool Registry → Tools (Gmail, Memory, Slack, MCP)
    │
    ▼
LangGraph Agent (create_deep_agent)
    │
    ├─► astream_events() → Streaming tokens/tool calls
    │
    ├─► interrupt_on → HITL pause
    │       │
    │       ▼
    │   Frontend approval UI
    │       │
    │       ▼
    │   resume() → Continue execution
    │
    ▼
Checkpointer (AsyncSqliteSaver) → Persistent state across restarts
```

### Key Implementation Files

| Concern | File |
|---------|------|
| Wizard conversation | `backend/application/builder.py` |
| Wizard config | `backend/config/wizard_prompt.md`, `tools.json`, `templates.json` |
| Agent execution | `backend/application/use_cases/run_agent.py` |
| Chat WebSocket | `backend/api/v1/chat.py` |
| Tool registration | `backend/infrastructure/tools/registry.py` |
| Memory tools | `backend/infrastructure/tools/builtin_memory.py` |
| Security patterns | `backend/infrastructure/tools/security.py` |
| Memory persistence | `backend/infrastructure/persistence/sqlite/memory_repo.py` |
| Skills API | `backend/api/v1/skills.py` |
| Skills loader | `backend/application/services/skill_loader.py` |
| Skills persistence | `backend/infrastructure/persistence/sqlite/skill_repo.py` |
| Frontend WebSocket | `frontend/src/hooks/useWebSocket.ts` |
| Memory approval UI | `frontend/src/components/chat/MemoryEditApproval.tsx` |
| Skills panel UI | `frontend/src/components/panels/SkillsPanel.tsx` |

---

## Sequence Diagram

```
User          Frontend           Backend              LangGraph         SQLite
  │               │                  │                    │                │
  │ "Create       │                  │                    │                │
  │  agent..."    │                  │                    │                │
  │──────────────►│                  │                    │                │
  │               │ WS: message      │                    │                │
  │               │─────────────────►│                    │                │
  │               │                  │ stream_chat()      │                │
  │               │                  │───────────────────►│                │
  │               │                  │                    │ Tool: create   │
  │               │                  │                    │───────────────►│
  │               │                  │                    │                │
  │               │◄─ token ─────────│◄───────────────────│                │
  │               │◄─ tool_call ─────│                    │                │
  │               │◄─ tool_result ───│                    │                │
  │               │◄─ complete ──────│                    │                │
  │◄──────────────│                  │                    │                │
  │               │                  │                    │                │
  │ "Summarize    │                  │                    │                │
  │  emails..."   │                  │                    │                │
  │──────────────►│                  │                    │                │
  │               │ WS: message      │                    │                │
  │               │─────────────────►│                    │                │
  │               │                  │ run()              │                │
  │               │                  │───────────────────►│                │
  │               │                  │                    │ list_emails    │
  │               │◄─ tool_call ─────│◄───────────────────│───────────────►│
  │               │◄─ tool_result ───│                    │◄───────────────│
  │               │                  │                    │                │
  │               │                  │                    │ write_memory   │
  │               │                  │                    │ (interrupt!)   │
  │               │                  │◄───────────────────│                │
  │               │◄─ memory_edit_req│                    │                │
  │◄──────────────│                  │                    │                │
  │               │                  │                    │                │
  │ [Approve]     │                  │                    │                │
  │──────────────►│                  │                    │                │
  │               │ WS: decision     │                    │                │
  │               │─────────────────►│                    │                │
  │               │                  │ save memory        │                │
  │               │                  │───────────────────────────────────►│
  │               │                  │                    │                │
  │               │                  │ resume()           │                │
  │               │                  │───────────────────►│                │
  │               │◄─ memory_complete│◄───────────────────│                │
  │               │◄─ tokens ────────│                    │                │
  │               │◄─ complete ──────│                    │                │
  │◄──────────────│                  │                    │                │
```

---

## Error Scenarios

| Scenario | System Behavior |
|----------|-----------------|
| **WebSocket disconnects** | Frontend reconnects. Agent state preserved in checkpointer. |
| **Memory write fails** | Error sent via WebSocket. Agent receives tool error, can retry. |
| **Invalid path** | Path validation rejects. Error returned before HITL. |
| **Content too large** | Size validation rejects (>100KB). Error returned before HITL. |
| **Missing credentials** | Tools that need credentials return helpful error messages. |
| **Server restart** | Checkpointer restores state. User can resume conversation. |

---

## v0.0.3 Feature Integration Points

| Feature | Integration Point |
|---------|-------------------|
| **Persistent conversations** | `AsyncSqliteSaver` via FastAPI lifespan in `main.py` |
| **Memory system** | `create_memory_tools()` in `registry.py` |
| **Skills** | `SkillLoader.get_metadata_for_prompt()` in `run_agent.py`, REST API in `skills.py` |
| **Slack** | `create_slack_tools()` in `registry.py` |
| **Wizard persistence** | `conversation_messages` table in `builder.py` |
| **Security** | `detect_suspicious_patterns()` in `chat.py` |

---

*v0.0.3 | January 18, 2026*
