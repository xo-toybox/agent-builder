# Agent Builder

A web-based email assistant agent builder with human-in-the-loop approval for sensitive actions.

## Features

- **Email Assistant Agent**: Triages inbox, drafts replies, sends emails with HITL approval
- **Gmail Integration**: Full OAuth flow with list, search, draft, send, and label operations
- **Calendar Integration**: Check availability via calendar_context subagent
- **Email Polling Trigger**: Polls for new emails at configurable intervals
- **Human-in-the-Loop**: Approve, edit, or reject sensitive tool calls (draft_reply, send_email)
- **Dark Theme UI**: React-based editor matching LangSmith Agent Builder design

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
# Edit .env with your credentials
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

5. **Open browser**

   Navigate to http://localhost:5173

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   React Frontend    │◄───►│   FastAPI Backend   │
│   (Vite + Tailwind) │ WS  │   + deepagents      │
└─────────────────────┘     └─────────────────────┘
                                     │
                                     ▼
                            ┌─────────────────────┐
                            │   Google APIs       │
                            │   Gmail + Calendar  │
                            └─────────────────────┘
```

## Project Structure

```
agent-builder/
├── backend/
│   ├── main.py              # FastAPI server + WebSocket
│   ├── agent.py             # Email assistant agent config
│   ├── config.py            # Environment settings
│   ├── persistence.py       # JSON file storage
│   ├── auth/                # Google OAuth
│   ├── tools/               # Gmail + Calendar tools
│   ├── triggers/            # Email polling
│   └── subagents/           # Calendar context subagent
├── frontend/
│   └── src/
│       ├── App.tsx          # Main application
│       ├── components/      # React components
│       ├── hooks/           # useWebSocket, useAgent
│       └── types/           # TypeScript types
├── data/                    # Persisted config (gitignored)
├── docs/                    # Design documents
└── pyproject.toml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/login` | Start Google OAuth flow |
| GET | `/auth/callback` | OAuth callback |
| GET | `/auth/status` | Check auth status |
| GET | `/api/agent` | Get agent config |
| PUT | `/api/agent` | Update agent config |
| GET | `/api/tools` | List available tools |
| PUT | `/api/tools/{name}/hitl` | Toggle HITL for tool |
| GET | `/api/triggers` | List triggers |
| POST | `/api/triggers/{id}/toggle` | Toggle trigger |
| WS | `/ws/chat` | Chat with agent |

## Gmail Tools

| Tool | HITL | Description |
|------|------|-------------|
| list_emails | No | List inbox emails |
| get_email | No | Get email by ID |
| search_emails | No | Search with Gmail query |
| draft_reply | **Yes** | Create draft reply |
| send_email | **Yes** | Send email |
| label_email | No | Modify labels |

## Development

```bash
# Run backend with auto-reload
uv run uvicorn backend.main:app --reload

# Run frontend with HMR
cd frontend && npm run dev

# Type check frontend
cd frontend && npm run build
```
