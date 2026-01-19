# Agent Builder

Build AI agents through natural language conversation. Create, customize, and deploy agents with Gmail, Calendar, Slack, and memory capabilities.

## Quick Start

```bash
# Backend
uv sync
cp .env.example .env  # Add ANTHROPIC_API_KEY, Google OAuth credentials
uv run uvicorn backend.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

## Documentation

### For Users

- [Getting Started](docs/user-guide/getting-started.md) - Setup and first agent
- [Creating Agents](docs/user-guide/creating-agents.md) - Builder wizard and templates
- [Memory & Skills](docs/user-guide/memory-and-skills.md) - Teaching your agent
- [Tools Reference](docs/user-guide/tools-reference.md) - Available capabilities
- [Troubleshooting](docs/user-guide/troubleshooting.md) - Common issues

### For Developers

- [Architecture](docs/dev/architecture.md) - System design
- [API Reference](docs/dev/api-reference.md) - REST and WebSocket endpoints
- [Adding Tools](docs/dev/adding-tools.md) - Extend agent capabilities
- [MCP Integration](docs/dev/mcp-integration.md) - External tool servers

### Project

- [Roadmap](docs/roadmap.md) - Feature plans
- [v0.0.3 PRD](docs/v0.0.3-agent-learning/prd.md) - Current version requirements

## Features

- **Chat-based agent creation** - Describe what you need, AI builds it
- **Templates** - Email Assistant, Research Assistant
- **Memory** - Agents learn from corrections
- **Skills** - Reusable instruction sets
- **HITL Approvals** - Human approval for sensitive actions
- **Tools** - Gmail, Calendar, Slack, Web Search
- **MCP Support** - Extend with external tool servers

## License

MIT
