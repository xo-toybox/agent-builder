# Agent Builder Roadmap

## v0.0.1 - Email Assistant (Complete)
Hardcoded email assistant with Gmail/Calendar tools, HITL approval, and canvas UI.

## v0.0.2 - Generic Agent Builder (Current)
Transform into a platform that can generate any agent a user needs.

**Reference:** [LangSmith Agent Builder](https://www.blog.langchain.com/langsmith-agent-builder-generally-available/)

**Design:** [v0.0.2 Design Document](./v0.0.2-agent-builder/design.md)

### Implemented ✓
- [x] Clone template to create agents
- [x] Agent chat with streaming responses
- [x] HITL approval flow (Approve/Edit/Reject)
- [x] Tool execution (list_emails, draft_reply, get_email, search_emails)
- [x] Agent editor UI (toolbox, triggers panel, instructions, subagents)
- [x] SQLite persistence for agents and conversations
- [x] Templates system (Email Assistant)

### Blockers (Must fix before release)
- [x] **Builder wizard WebSocket disconnected** - FIXED
  - Root cause: Vite proxy didn't handle WebSocket on `/api/v1/wizard/chat`
  - Fix: Added `ws: true` to `/api` proxy config in `vite.config.ts`
- [x] **No error feedback to users** - FIXED
  - Fix: Added react-hot-toast notification system
  - Shows success/error toasts for clone, delete, and API errors
- [x] **Builder wizard create_agent tool failing** - FIXED
  - Root cause: LangChain `astream` provides incomplete tool call args in chunks
  - Fix: Changed `stream_chat()` in `builder.py` to use `ainvoke` instead of `astream`
  - Also simplified tool signature from nested Pydantic model to flat parameters
- [x] **Agent edit page showing wrong tools/subagents** - FIXED
  - Root cause: `Canvas` component used legacy global data from `useAgent()` instead of `selectedAgent`
  - Fix: Updated `App.tsx` to use `selectedAgent?.tools` and `selectedAgent?.subagents`
  - Now correctly displays each agent's custom configuration

### Should Fix (v0.0.2 polish)
- [x] **Sidebar navigation non-functional** - FIXED
  - Root cause: Sidebar component was completely static with hardcoded "Email Assistant"
  - Fix: Rewrote `Sidebar.tsx` to accept dynamic props (agents, selectedAgentId, onSelectAgent, onNavigate)
  - Now shows all user agents, highlights selected, and all navigation buttons work
- [ ] Save Changes button lacks visual feedback
- [ ] Raw JSON displayed alongside formatted tool results
- [ ] Example suggestions not clickable in builder wizard

### Deferred to v0.0.3
- [ ] Additional MCP tools (Calendar events, Slack, Notion, Google Drive)
- [ ] Trigger execution (email polling, webhooks) - currently stubbed
- [ ] Long-term memory persistence across sessions
- [ ] Subagent orchestration - data structures exist, execution logic pending

## v0.0.3 - Expanded Integrations
- Multiple MCP tool integrations
- Working trigger system (schedule, events)
- Persistent memory across sessions
- Full subagent orchestration

## Future
- Multi-user support
- Cloud deployment
- Agent marketplace

---
*Last updated: January 15, 2026*
