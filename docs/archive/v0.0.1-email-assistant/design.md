# Agent Builder v0.0.1 Design Document

## Overview

v0.0.1 delivers a functional email assistant agent with a web-based configuration UI. The agent triages incoming emails, drafts responses, and integrates with Google Calendar for scheduling—all with human-in-the-loop approval for sensitive actions.

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend (Vite + React)                     │
│  ┌──────────────┬─────────────────────────┐  ┌────────────────────────┐ │
│  │ TRIGGERS     │ TOOLBOX            +MCP │  │     Chat Drawer        │ │
│  │ Gmail Poll   │ [tools + HITL badges]   │  │  ┌──────────────────┐  │ │
│  ├──────────────┼─────────────────────────┤  │  │ Message List     │  │ │
│  │ AGENT        │ SUB-AGENTS              │  │  ├──────────────────┤  │ │
│  │ Name         ├─────────────────────────┤  │  │ HITL Approval    │  │ │
│  │ Instructions │ SKILLS                  │  │  │ [Approve|Edit|X] │  │ │
│  └──────────────┴─────────────────────────┘  │  └──────────────────┘  │ │
└─────────────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI + Python)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ OAuth Flow  │  │ WebSocket   │  │ Email       │  │ Agent Runner    │ │
│  │ /auth/*     │  │ /ws/chat    │  │ Polling     │  │ deepagents      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                                                              │           │
│                              ┌───────────────────────────────┘           │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     Email Assistant Agent                          │  │
│  │  model: claude-sonnet-4-20250514                                   │  │
│  │  tools: [gmail_*, calendar_*]                                      │  │
│  │  interrupt_on: {draft_reply, send_email}                           │  │
│  │  subagents: [calendar_context]                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         External Services                                │
│  ┌─────────────────────┐           ┌─────────────────────────────────┐  │
│  │ Gmail API           │           │ Google Calendar API             │  │
│  │ - list messages     │           │ - list events                   │  │
│  │ - get message       │           │ - get event                     │  │
│  │ - send message      │           │                                 │  │
│  │ - modify labels     │           │                                 │  │
│  └─────────────────────┘           └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
agent-builder/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, routes, WebSocket
│   ├── config.py               # Environment config (Pydantic Settings)
│   ├── persistence.py          # Agent config file persistence
│   ├── agent.py                # Email assistant agent definition
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── gmail.py            # Gmail tools
│   │   └── calendar.py         # Calendar tools
│   ├── auth/
│   │   ├── __init__.py
│   │   └── google_oauth.py     # OAuth2 flow + token refresh
│   ├── triggers/
│   │   ├── __init__.py
│   │   └── email_polling.py    # Background polling task
│   └── subagents/
│       ├── __init__.py
│       └── calendar_context.py # Calendar availability subagent
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts          # Vite config with proxy to backend
│   ├── tailwind.config.js      # Tailwind config with light theme colors
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx             # Main app with layout
│       ├── index.css           # Tailwind imports + light theme
│       ├── vite-env.d.ts
│       ├── types/
│       │   └── index.ts        # TypeScript types
│       ├── hooks/
│       │   ├── useWebSocket.ts # WebSocket hook with HITL support
│       │   └── useAgent.ts     # Agent config hook with mock data fallback
│       └── components/
│           ├── layout/
│           │   ├── Sidebar.tsx     # Left navigation sidebar
│           │   ├── Header.tsx      # Top header bar
│           │   └── Canvas.tsx      # Canvas with floating panels
│           └── chat/
│               └── ChatPanel.tsx   # Embedded chat panel with HITL
├── data/
│   ├── agent_config.json       # Persisted agent configuration
│   └── google_token.json       # OAuth tokens (gitignored)
├── .env                        # Environment variables (gitignored)
├── pyproject.toml
└── docs/
    ├── v0.0.1-email-assistant/
    │   ├── impl.md             # Implementation spec
    │   ├── design.md           # This file
    │   └── system-instruction.md
    └── v0.0.2-roadmap.md
```

---

## Backend Design

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Runtime | Python | 3.12+ |
| Package Manager | uv | latest |
| Web Framework | FastAPI | 0.115+ |
| Agent Harness | deepagents | 0.3.5+ |
| Google APIs | google-api-python-client | 2.x |
| OAuth | google-auth-oauthlib | 1.x |
| WebSocket | fastapi + websockets | built-in |
| Validation | Pydantic | 2.x |

### Dependencies (pyproject.toml)

```toml
[project]
name = "agent-builder"
version = "0.0.1"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "deepagents>=0.3.5",
    "google-api-python-client>=2.150.0",
    "google-auth-oauthlib>=1.2.0",
    "pydantic-settings>=2.6.0",
    "langchain-anthropic>=0.3.0",
]
```

### Configuration (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Anthropic
    anthropic_api_key: str

    # Agent
    polling_interval_seconds: int = 30

    model_config = {"env_file": ".env"}

settings = Settings()
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/login` | Redirect to Google OAuth |
| GET | `/auth/callback` | OAuth callback, store tokens |
| GET | `/auth/status` | Check if authenticated |
| POST | `/auth/logout` | Clear tokens |
| GET | `/api/agent` | Get agent configuration |
| PUT | `/api/agent` | Update agent configuration |
| GET | `/api/tools` | List available tools |
| PUT | `/api/tools/{name}/hitl` | Toggle HITL for tool |
| GET | `/api/triggers` | List triggers |
| POST | `/api/triggers/{id}/toggle` | Enable/disable trigger |
| WS | `/ws/chat` | Chat with agent (streaming) |

### WebSocket Protocol

**Client → Server:**
```typescript
// Send message
{ "type": "message", "content": "Check my inbox" }

// HITL decision
{ "type": "hitl_decision", "tool_call_id": "xyz", "decision": "approve" }
{ "type": "hitl_decision", "tool_call_id": "xyz", "decision": "edit", "new_args": {...} }
{ "type": "hitl_decision", "tool_call_id": "xyz", "decision": "reject" }
```

**Server → Client:**
```typescript
// Streaming token
{ "type": "token", "content": "Hello" }

// Tool call (non-HITL)
{ "type": "tool_call", "name": "list_emails", "args": {...} }

// Tool result
{ "type": "tool_result", "name": "list_emails", "result": {...} }

// HITL interrupt
{ "type": "hitl_interrupt", "tool_call_id": "xyz", "name": "send_email", "args": {...} }

// Agent complete
{ "type": "complete", "content": "Done processing emails" }

// Error
{ "type": "error", "message": "..." }
```

### Gmail Tools

| Tool | Description | HITL |
|------|-------------|------|
| `list_emails` | List recent emails with optional filters | No |
| `get_email` | Get full email content by ID | No |
| `search_emails` | Search emails with Gmail query syntax | No |
| `draft_reply` | Create draft reply to email | **Yes** |
| `send_email` | Send email | **Yes** |
| `label_email` | Add/remove labels (archive, mark read) | No |

**Tool Schemas:**

```python
@tool
def list_emails(
    max_results: int = 10,
    label: str = "INBOX",
    unread_only: bool = False
) -> list[EmailSummary]:
    """List emails from inbox."""

@tool
def get_email(email_id: str) -> Email:
    """Get full email content including body and attachments."""

@tool
def search_emails(query: str, max_results: int = 10) -> list[EmailSummary]:
    """Search emails using Gmail query syntax (e.g., 'from:john is:unread')."""

@tool
def draft_reply(
    email_id: str,
    body: str,
    cc: list[str] | None = None
) -> Draft:
    """Create a draft reply. Requires human approval."""

@tool
def send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    reply_to_id: str | None = None
) -> SentEmail:
    """Send an email. Requires human approval."""

@tool
def label_email(
    email_id: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None
) -> None:
    """Modify email labels (e.g., mark as read, archive)."""
```

### Calendar Tools

| Tool | Description | HITL |
|------|-------------|------|
| `list_events` | List calendar events for date range | No |
| `get_event` | Get event details by ID | No |

```python
@tool
def list_events(
    date: str,  # Format: YYYY-MM-DD
    days: int = 1
) -> list[CalendarEvent]:
    """List calendar events for a date range."""

@tool
def get_event(event_id: str) -> CalendarEvent:
    """Get detailed event information."""
```

### Agent Configuration

```python
from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic

def create_email_agent(google_credentials):
    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    # Gmail tools with credentials injected
    gmail_tools = create_gmail_tools(google_credentials)
    calendar_tools = create_calendar_tools(google_credentials)

    # Calendar context subagent
    calendar_subagent = {
        "name": "calendar_context",
        "description": "Check calendar availability and parse meeting requests",
        "system_prompt": "You help check calendar availability...",
        "tools": calendar_tools,
    }

    agent = create_deep_agent(
        model=model,
        system_prompt=SYSTEM_INSTRUCTION,  # From system-instruction.md
        tools=gmail_tools,
        subagents=[calendar_subagent],
        interrupt_on={
            "draft_reply": {"allowed_decisions": ["approve", "edit", "reject"]},
            "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
        },
    )

    return agent
```

### Email Polling Trigger

```python
import asyncio
from datetime import datetime

class EmailPollingTrigger:
    def __init__(self, agent, gmail_service, interval_seconds: int = 30):
        self.agent = agent
        self.gmail = gmail_service
        self.interval = interval_seconds
        self.last_check = datetime.now()
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            new_emails = await self._check_new_emails()
            if new_emails:
                await self._process_emails(new_emails)
            await asyncio.sleep(self.interval)

    async def stop(self):
        self.running = False

    async def _check_new_emails(self) -> list[Email]:
        query = f"after:{int(self.last_check.timestamp())} is:unread"
        self.last_check = datetime.now()
        return await self.gmail.search(query)

    async def _process_emails(self, emails: list[Email]):
        for email in emails:
            await self.agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": f"New email received:\n{email.to_prompt()}"
                }]
            })
```

---

## Frontend Design

### Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| Language | TypeScript |
| State | React hooks (useState, useContext) |
| WebSocket | Native WebSocket API |

### Color Palette (Light Theme)

```css
:root {
  --bg-primary: #f8f9fa;      /* Main background */
  --bg-secondary: #ffffff;    /* Panel backgrounds */
  --bg-tertiary: #f3f4f6;     /* Input backgrounds */
  --bg-canvas: #fafafa;       /* Canvas background */
  --border: #e5e7eb;          /* Borders */
  --text-primary: #111827;    /* Primary text */
  --text-secondary: #6b7280;  /* Secondary text */
  --text-muted: #9ca3af;      /* Muted text */

  /* Accent colors matching LangSmith */
  --accent-orange: #f97316;   /* Triggers, HITL badges */
  --accent-teal: #0d9488;     /* Toolbox, MCP, Connect */
  --accent-purple: #7c3aed;   /* Subagents */
  --accent-blue: #3b82f6;     /* Skills */
  --accent-green: #22c55e;    /* Success/Approve */
  --accent-red: #ef4444;      /* Error/Reject */
}
```

### Layout Structure (Canvas Flow)

The UI uses a canvas flow layout with floating panels connected by dashed lines, matching the LangSmith Agent Builder design:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                                                        │
│ │ Sidebar  │  ┌─────────────────────────────────────────────────────────────────┐   │
│ │          │  │ Header: Email Assistant [Editing] [Private]  [Threads] [⚙] [Save]│   │
│ │ Feed     │  └─────────────────────────────────────────────────────────────────┘   │
│ │          │  ┌───────────────────────┬──────────────────────────────────────────┐  │
│ │ MY AGENTS│  │ Chat Panel            │           Canvas (Flow Layout)           │  │
│ │ • Email  │  │ ┌───────────────────┐ │  ┌─────────────┐      ┌─────────────────┐│  │
│ │          │  │ │ Hide Chat  Clear  │ │  │ TRIGGERS    │ ─ ─ ─│ TOOLBOX    +MCP ││  │
│ │ EXPLORE  │  │ ├───────────────────┤ │  │ Schedule    │      │ List Emails     ││  │
│ │ Templates│  │ │                   │ │  │ Slack       │      │ Get Email       ││  │
│ │ Workspace│  │ │    ┌────┐         │ │  │ Gmail    ▾  │  ┌──►│ Search Emails   ││  │
│ │          │  │ │    │ EA │         │ │  │ +Connect    │  │   │ Draft Reply  ⚠  ││  │
│ │          │  │ │    └────┘         │ │  │ Polling ON  │  │   │ Send Email   ⚠  ││  │
│ │          │  │ │ Chat with Email   │ │  └──────┬──────┘  │   └────────┬────────┘│  │
│ │          │  │ │    Assistant      │ │         │         │            │         │  │
│ │          │  │ │                   │ │         ▼         │            │         │  │
│ │          │  │ │                   │ │  ┌─────────────────────┐       │         │  │
│ │ Docs     │  │ │                   │ │  │ AGENT               │───────┘         │  │
│ │ Settings │  │ │ ┌───────────────┐ │ │  │ Email Assistant     │                 │  │
│ │          │  │ │ │ Ask agent...  │ │ │  │ Instructions   Edit │──┐              │  │
│ │ [Login]  │  │ │ └───────────────┘ │ │  └─────────────────────┘  │              │  │
│ └──────────┘  │ │ [Quick Actions]   │ │                           │              │  │
│               │ └───────────────────┘ │         ┌─────────────────┘              │  │
│               │                       │         ▼                                │  │
│               │                       │  ┌─────────────┐  ┌─────────────────────┐│  │
│               │                       │  │ SUB-AGENTS  │  │ SKILLS          +Add││  │
│               │                       │  │calendar_ctx │  │ No skills           ││  │
│               │                       │  └─────────────┘  └─────────────────────┘│  │
│               └───────────────────────┴──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘

Legend: ─ ─ ─  Dashed connection lines (purple/teal)
        ⚠      "Review Required" badge (HITL enabled)
```

### Component Hierarchy

```
App
├── Sidebar
│   ├── Logo (Agent Builder)
│   ├── Navigation (Feed, My Agents, Explore)
│   ├── AgentList
│   └── UserSection (Login with Google)
├── MainContent
│   ├── Header
│   │   ├── BackButton
│   │   ├── AgentName + Badges (Editing, Private)
│   │   ├── Threads Button
│   │   ├── ChatToggle
│   │   ├── Settings
│   │   └── SaveChanges
│   └── ContentArea
│       ├── ChatPanel (embedded, toggleable)
│       │   ├── Header (Hide Chat, Clear)
│       │   ├── MessageList
│       │   │   ├── EmptyState (EA icon)
│       │   │   ├── UserMessage
│       │   │   ├── AssistantMessage
│       │   │   ├── ToolMessage
│       │   │   └── HITLMessage
│       │   ├── HITLApprovalInline
│       │   │   ├── ArgsPreview/Editor
│       │   │   └── DecisionButtons [Approve|Edit|Reject]
│       │   ├── MessageInput
│       │   └── QuickActions (Change instructions, Add subagent, Add tools)
│       └── Canvas (flow layout)
│           ├── SVG ConnectionLines (dashed)
│           ├── TriggersCard (orange accent)
│           │   ├── Schedule/Slack/Gmail options
│           │   ├── Connect Gmail button
│           │   └── Polling toggle
│           ├── ToolboxCard (teal accent)
│           │   ├── ToolList with icons
│           │   ├── "Review Required" badges
│           │   └── MCP button
│           ├── AgentCard
│           │   ├── Name + Description
│           │   └── Instructions preview + Edit
│           ├── SubagentsCard
│           └── SkillsCard
```

### Key Components

**TriggersPanel.tsx**
```tsx
interface Trigger {
  id: string;
  type: "gmail_polling";
  enabled: boolean;
  config: {
    interval_seconds: number;
    account: string;
  };
}

function TriggersPanel() {
  const [triggers, setTriggers] = useState<Trigger[]>([]);

  return (
    <Panel accent="orange" title="TRIGGERS" action={<AddButton />}>
      {triggers.map(trigger => (
        <TriggerItem
          key={trigger.id}
          trigger={trigger}
          onToggle={() => toggleTrigger(trigger.id)}
        />
      ))}
    </Panel>
  );
}
```

**ToolboxPanel.tsx**
```tsx
interface Tool {
  name: string;
  description: string;
  enabled: boolean;
  hitl: boolean;
}

function ToolboxPanel() {
  const [tools, setTools] = useState<Tool[]>([]);

  return (
    <Panel accent="teal" title="TOOLBOX" action={<AddMCPButton />}>
      {tools.map(tool => (
        <ToolItem
          key={tool.name}
          tool={tool}
          onToggle={() => toggleTool(tool.name)}
          onHITLToggle={() => toggleHITL(tool.name)}
        />
      ))}
    </Panel>
  );
}
```

**HITLApproval.tsx**
```tsx
interface HITLInterruptProps {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  onDecision: (decision: "approve" | "edit" | "reject", newArgs?: Record<string, unknown>) => void;
}

function HITLApproval({ toolCallId, toolName, args, onDecision }: HITLInterruptProps) {
  const [editing, setEditing] = useState(false);
  const [editedArgs, setEditedArgs] = useState(args);

  return (
    <div className="bg-yellow-900/20 border border-yellow-500/50 rounded-lg p-4">
      <div className="text-yellow-500 font-medium mb-2">
        Approval Required: {toolName}
      </div>

      {editing ? (
        <JsonEditor value={editedArgs} onChange={setEditedArgs} />
      ) : (
        <pre className="bg-black/30 p-2 rounded text-sm">
          {JSON.stringify(args, null, 2)}
        </pre>
      )}

      <div className="flex gap-2 mt-4">
        <Button variant="success" onClick={() => onDecision("approve")}>
          Approve
        </Button>
        <Button variant="secondary" onClick={() => setEditing(true)}>
          Edit
        </Button>
        {editing && (
          <Button variant="primary" onClick={() => onDecision("edit", editedArgs)}>
            Confirm Edit
          </Button>
        )}
        <Button variant="danger" onClick={() => onDecision("reject")}>
          Reject
        </Button>
      </div>
    </div>
  );
}
```

**useWebSocket.ts**
```typescript
function useWebSocket(url: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [connected, setConnected] = useState(false);
  const [pendingHITL, setPendingHITL] = useState<HITLInterrupt | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "token":
          // Append to last assistant message
          break;
        case "hitl_interrupt":
          setPendingHITL(data);
          break;
        case "complete":
          // Finalize message
          break;
      }
    };

    return () => ws.close();
  }, [url]);

  const sendMessage = (content: string) => {
    wsRef.current?.send(JSON.stringify({ type: "message", content }));
  };

  const sendHITLDecision = (toolCallId: string, decision: string, newArgs?: unknown) => {
    wsRef.current?.send(JSON.stringify({
      type: "hitl_decision",
      tool_call_id: toolCallId,
      decision,
      new_args: newArgs
    }));
    setPendingHITL(null);
  };

  return { messages, connected, pendingHITL, sendMessage, sendHITLDecision };
}
```

---

## Data Flow

### 1. User Authenticates

```
Browser                    Backend                    Google
   │                          │                          │
   │──GET /auth/login────────►│                          │
   │◄─Redirect to Google──────│                          │
   │──────────────────────────────────────OAuth consent─►│
   │◄─────────────────────────────────────code redirect──│
   │──GET /auth/callback?code=───────────────────────────│
   │                          │──exchange code──────────►│
   │                          │◄─tokens─────────────────│
   │◄─Set session cookie──────│                          │
```

### 2. Chat Message Flow

```
React                      FastAPI                   deepagents
  │                           │                          │
  │──WS: {type:"message"}────►│                          │
  │                           │──agent.astream()────────►│
  │◄─WS: {type:"token"}───────│◄─stream tokens──────────│
  │◄─WS: {type:"tool_call"}───│◄─tool call──────────────│
  │                           │──execute tool───────────►│
  │◄─WS: {type:"tool_result"}─│◄─result─────────────────│
  │◄─WS: {type:"complete"}────│◄─final response─────────│
```

### 3. HITL Interrupt Flow

```
React                      FastAPI                   deepagents
  │                           │                          │
  │                           │◄─interrupt (send_email)──│
  │◄─WS: {type:"hitl_interrupt"}──│                      │
  │                           │                          │
  │  [User reviews & decides] │                          │
  │                           │                          │
  │──WS: {type:"hitl_decision", decision:"approve"}─────►│
  │                           │──resume with decision───►│
  │◄─WS: {type:"tool_result"}─│◄─email sent─────────────│
  │◄─WS: {type:"complete"}────│◄─final response─────────│
```

---

## Security Considerations

### v0.0.1 Scope

| Concern | Mitigation |
|---------|------------|
| OAuth tokens | Store in server-side session, not exposed to frontend |
| CSRF | Use SameSite cookies, validate Origin header on WebSocket |
| API keys | Environment variables only, never in code |
| User input | Sanitize before display, escape in emails |

### Deferred to v0.0.2+

- Token encryption at rest
- PII redaction in logs
- Rate limiting
- Prompt injection mitigation

---

## Testing Strategy

### Backend

| Type | Tool | Coverage |
|------|------|----------|
| Unit | pytest | Tools, agent config |
| Integration | pytest-asyncio | WebSocket, OAuth flow |
| Mocks | unittest.mock | Gmail/Calendar APIs |

### Frontend

| Type | Tool | Coverage |
|------|------|----------|
| Unit | Vitest | Hooks, utilities |
| Component | React Testing Library | Panels, chat |
| E2E | Playwright (v0.0.2) | Full flows |

---

## Development Workflow

### Local Setup

```bash
# Backend
cd agent-builder
uv sync
cp .env.example .env  # Add credentials
uv run uvicorn backend.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Environment Variables

```bash
# .env
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
ANTHROPIC_API_KEY=xxx
```

---

## Acceptance Criteria

- [x] OAuth flow initiates correctly (redirects to Google)
- [x] OAuth callback endpoint handles token exchange
- [x] OAuth flow completes successfully with test user added in Google Cloud Console
- [x] Agent triages inbox via `list_emails` tool
- [x] `draft_reply` triggers HITL interrupt with preview
- [ ] `send_email` triggers HITL interrupt with preview
- [x] Resume with approve/edit/reject works correctly
- [ ] `calendar_context` subagent checks availability when asked
- [ ] Email polling trigger detects new emails
- [x] UI layout matches LangSmith Agent Builder design (canvas flow)
- [x] UI chat panel invokes agent and streams responses
- [x] Light theme applied consistently across all components
- [x] WebSocket connection shows authentication status
- [x] Tools load from backend with "Review Required" badges
- [x] Subagents display in canvas (calendar_context)
- [x] Chat panel toggle (Hide/Show Chat) works
- [x] Backend serves real agent config and tool data
- [x] Logged-in user email displayed in sidebar

---

## Design Decisions

| Question | Decision | Notes |
|----------|----------|-------|
| Skills panel | Placeholder UI only | Functional skills deferred to v0.0.2 |
| Agent persistence | JSON file | Simple file-based storage; DB deferred to v0.0.2 |
| Multi-user | Deferred | Single-user only for v0.0.1; multi-user on long-term roadmap |

### Agent Config Persistence

Agent configuration (name, instructions, tools, subagents, triggers) persists to a JSON file:

```
data/
└── agent_config.json
```

```python
# backend/persistence.py
from pathlib import Path
import json
from pydantic import BaseModel

CONFIG_PATH = Path("data/agent_config.json")

class AgentConfig(BaseModel):
    name: str = "Email Assistant"
    instructions: str = ""
    tools: list[str] = []
    hitl_tools: list[str] = ["draft_reply", "send_email"]
    subagents: list[dict] = []
    triggers: list[dict] = []

def load_config() -> AgentConfig:
    if CONFIG_PATH.exists():
        return AgentConfig.model_validate_json(CONFIG_PATH.read_text())
    return AgentConfig()

def save_config(config: AgentConfig) -> None:
    CONFIG_PATH.parent.mkdir(exist_ok=True)
    CONFIG_PATH.write_text(config.model_dump_json(indent=2))
```

---

### Requires Manual Setup
1. **Google OAuth** - Add test user in Google Cloud Console (app is in testing mode)
2. **Environment Variables** - Create `.env` with Google OAuth and Anthropic credentials


*Last updated: January 14, 2026*
