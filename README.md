# Agent Builder

A generic agent builder platform that can create any AI agent through natural language conversation. Build, configure, and deploy AI agents with flexible tools, triggers, and human-in-the-loop approval flows.

## v0.0.2 - Generic Agent Builder

This version transforms Agent Builder from a hardcoded email assistant (v0.0.1) into a platform that can generate any agent type.

### Key Features

- **Chat-based Agent Creation** - Describe what you want, AI builds the agent
- **Multiple Agents** - Create and manage multiple independent agents
- **Flexible Tools** - Built-in Gmail/Calendar tools + MCP server integration
- **Configurable Triggers** - Email polling, webhooks, scheduled runs
- **HITL Approvals** - Human approval for sensitive actions
- **Templates** - Clone pre-built templates like the Email Assistant
- **SQLite Persistence** - Reliable storage replacing JSON files

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud project with Gmail and Calendar APIs enabled
- Anthropic API key

### Setup

1. **Clone and install dependencies**

```bash
cd agent-builder

# Backend
uv sync

# Frontend
cd frontend && npm install && cd ..
```

2. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your credentials:
# - ANTHROPIC_API_KEY
# - GOOGLE_CLIENT_ID
# - GOOGLE_CLIENT_SECRET
```

3. **Google OAuth Setup**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project or select existing
   - Enable Gmail API and Google Calendar API
   - Create OAuth 2.0 credentials (Web application)
   - Add `http://localhost:8000/auth/callback` to authorized redirect URIs
   - Copy Client ID and Secret to `.env`

4. **Run the application**

```bash
# Terminal 1: Backend
uv run uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

5. **Open browser**: Navigate to http://localhost:5173

## Architecture (v0.0.2)

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
│  Use Cases: CreateAgent, RunAgent, CloneTemplate, ManageTriggers │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Domain Layer                             │
│  Entities: Agent, Tool, Trigger, HITL | Ports: Repositories      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                        │
│  SQLite Persistence | MCP Client | Built-in Tools | Triggers     │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
agent-builder/
├── backend/
│   ├── main.py                      # FastAPI app + legacy routes
│   ├── config.py                    # Environment settings
│   ├── domain/                      # Domain Layer (Hexagonal)
│   │   ├── entities.py              # Agent, Tool, Trigger, HITL
│   │   ├── ports.py                 # Repository protocols
│   │   └── services.py              # Service protocols
│   ├── application/                 # Application Layer
│   │   ├── use_cases/               # CreateAgent, CloneTemplate, etc.
│   │   └── builder.py               # Builder Wizard agent
│   ├── infrastructure/              # Infrastructure Layer
│   │   ├── persistence/sqlite/      # SQLite repositories
│   │   ├── tools/                   # Tool registry + MCP client
│   │   └── templates/               # Agent templates
│   ├── api/v1/                      # API routes
│   │   ├── agents.py                # Agent CRUD
│   │   ├── wizard.py                # Builder wizard chat
│   │   ├── chat.py                  # Agent chat
│   │   └── tools.py                 # Tool management
│   └── migration/                   # Migration scripts
├── frontend/
│   └── src/
│       ├── App.tsx                  # Multi-view routing
│       ├── pages/                   # AgentList, AgentBuilder
│       ├── hooks/                   # useAgents, useBuilderChat
│       └── types/                   # TypeScript types
├── data/                            # SQLite DB (gitignored)
└── docs/
    ├── roadmap.md                   # Project roadmap
    └── v0.0.2-agent-builder/
        └── design.md                # Full design document
```

## API Endpoints

### v0.0.2 API (`/api/v1/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/agents` | List all agents |
| GET | `/api/v1/agents/templates` | List templates |
| GET | `/api/v1/agents/{id}` | Get agent details |
| POST | `/api/v1/agents` | Create new agent |
| POST | `/api/v1/agents/{id}/clone` | Clone an agent |
| DELETE | `/api/v1/agents/{id}` | Delete an agent |
| WS | `/api/v1/wizard/chat` | Builder wizard chat |
| WS | `/api/v1/chat/{agent_id}` | Chat with agent |
| GET | `/api/v1/tools/builtin` | List built-in tools |
| GET | `/api/v1/tools/mcp` | List MCP servers |

### Legacy API (backward compatible)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/login` | Start Google OAuth |
| GET | `/auth/status` | Check auth status |
| GET | `/api/agent` | Get legacy config |
| WS | `/ws/chat` | Legacy chat endpoint |

## Built-in Tools

### Gmail Tools
| Tool | HITL | Description |
|------|------|-------------|
| list_emails | No | List inbox emails |
| get_email | No | Get email by ID |
| search_emails | No | Search with Gmail query |
| draft_reply | **Yes** | Create draft reply |
| send_email | **Yes** | Send email |
| label_email | No | Modify labels |

### Calendar Tools
| Tool | HITL | Description |
|------|------|-------------|
| list_events | No | List calendar events |
| get_event | No | Get event details |

## Creating an Agent

1. **From Template**: Clone the Email Assistant template and customize
2. **Via Builder**: Use the chat-based wizard to describe what you need
3. **Via API**: POST to `/api/v1/agents` with full configuration

### Builder Example

```
You: I want an agent that monitors my inbox and summarizes important emails

Builder: I can help you create that! Let me ask a few questions:
1. What emails should be considered "important"?
2. Should it send you summaries or just organize them?
3. Do you want it to run continuously or on-demand?
```

## Development

```bash
# Run backend with auto-reload
uv run uvicorn backend.main:app --reload

# Run frontend with HMR
cd frontend && npm run dev

# Type check frontend
cd frontend && npm run build
```

## Documentation

- [Design Document](docs/v0.0.2-agent-builder/design.md) - Full architecture and implementation details
- [Roadmap](docs/roadmap.md) - Project roadmap and future plans

## License

MIT
