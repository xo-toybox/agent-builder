# API Reference

Base URL: `http://localhost:8000`

## REST Endpoints

### Agents

#### List Agents
```
GET /api/v1/agents
GET /api/v1/agents?is_template=false
```

#### List Templates
```
GET /api/v1/agents/templates
```

#### Get Agent
```
GET /api/v1/agents/{agent_id}
```

#### Create Agent
```
POST /api/v1/agents
Content-Type: application/json

{
  "name": "My Agent",
  "description": "Agent description",
  "system_prompt": "You are a helpful assistant.",
  "model": "claude-sonnet-4-20250514",
  "tools": [
    {"name": "list_emails", "source": "builtin", "hitl_enabled": false}
  ]
}
```

#### Update Agent
```
PUT /api/v1/agents/{agent_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "system_prompt": "New instructions..."
}
```

#### Clone Agent
```
POST /api/v1/agents/{agent_id}/clone
Content-Type: application/json

{"new_name": "Cloned Agent"}
```

#### Delete Agent
```
DELETE /api/v1/agents/{agent_id}
```
Returns 400 if agent is a template.

### Skills

#### List Skills
```
GET /api/v1/agents/{agent_id}/skills
```

#### Create Skill
```
POST /api/v1/agents/{agent_id}/skills
Content-Type: application/json

{
  "name": "summarize_email",
  "description": "Summarize long emails",
  "instructions": "When summarizing..."
}
```

#### Get Skill
```
GET /api/v1/agents/{agent_id}/skills/{skill_id}
```

#### Update Skill
```
PUT /api/v1/agents/{agent_id}/skills/{skill_id}
Content-Type: application/json

{
  "name": "updated_name",
  "description": "Updated description",
  "instructions": "Updated instructions..."
}
```

#### Delete Skill
```
DELETE /api/v1/agents/{agent_id}/skills/{skill_id}
```

### Memory

#### List Memory Files
```
GET /api/v1/agents/{agent_id}/memory
```

#### Get Memory File
```
GET /api/v1/agents/{agent_id}/memory/{path}
```

#### Delete Memory File
```
DELETE /api/v1/agents/{agent_id}/memory/{path}
```

### Credentials

#### Check Slack Status
```
GET /api/v1/credentials/slack/status
```

#### Save Slack Token
```
POST /api/v1/credentials/slack
Content-Type: application/json

{"token": "xoxb-..."}
```

#### Remove Slack Token
```
DELETE /api/v1/credentials/slack
```

### Tools

#### List Built-in Tools
```
GET /api/v1/tools/builtin
```

#### List MCP Servers
```
GET /api/v1/tools/mcp
```

### Settings

#### Get Global Settings
```
GET /api/v1/settings
```

Response:
```json
{
  "default_model": "claude-sonnet-4-20250514",
  "tavily_api_key_set": true
}
```

#### Update Global Settings
```
PUT /api/v1/settings
Content-Type: application/json

{
  "default_model": "claude-sonnet-4-20250514",
  "tavily_api_key": "tvly-..."
}
```

#### List Available Models
```
GET /api/v1/settings/models
```

### Auth

#### Start OAuth
```
GET /api/v1/auth/login
```
Redirects to Google OAuth.

#### OAuth Callback
```
GET /api/v1/auth/callback?code=...
```

#### Check Auth Status
```
GET /api/v1/auth/status
```

#### Logout
```
POST /api/v1/auth/logout
```

## WebSocket Endpoints

### Agent Chat
```
WS /api/v1/chat/{agent_id}
```

**Client → Server:**
```json
{"type": "message", "content": "Hello"}
{"type": "hitl_decision", "decision": "approve", "tool_call_id": "..."}
{"type": "memory_edit_decision", "decision": "approve", "request_id": "...", "tool_call_id": "..."}
```

**Server → Client:**
```json
{"type": "message", "role": "assistant", "content": "Hi there!"}
{"type": "tool_call", "name": "list_emails", "args": {...}}
{"type": "tool_result", "name": "list_emails", "content": "..."}
{"type": "hitl_interrupt", "tool_call_id": "...", "name": "send_email", "args": {...}}
{"type": "memory_edit_request", "request_id": "...", "tool_call_id": "...", "path": "...", "content": "..."}
{"type": "done"}
{"type": "error", "message": "..."}
```

### Builder Wizard
```
WS /api/v1/wizard/chat
```

Same message format as agent chat, plus:
```json
{"type": "agent_created", "agent_id": "...", "name": "..."}
```

## Error Responses

```json
{
  "detail": "Agent not found"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request (e.g., deleting template) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate skill name) |
| 500 | Server error |
