# Agent Builder Recreation: Implementation Spec

## Stack

- **Agent harness:** `deepagents` SDK (pip install deepagents)
- **Email:** Google API client (Gmail, Calendar)
- **UI:** React + Tailwind, dark theme

---

## What `deepagents` Provides

For reference—these are abstracted by the SDK, not built by us:

| Primitive | Purpose |
|-----------|---------|
| Agent loop | Messages → LLM → tool calls → repeat |
| HITL | Interrupt/resume via `interrupt_on` config |
| Memory | Short-term (thread) + long-term (persistent) |
| Tool registry | Registration, validation, Anthropic format export |
| Subagents | Isolated delegation via `task` tool |
| Middleware | TodoList, Filesystem, Summarization, PromptCaching |
| Backends | State, Filesystem, Store (pluggable) |

---

## Deliverables

### 1. Email Assistant Agent

Configuration file that instantiates `create_deep_agent()` with:

| Config | Value |
|--------|-------|
| model | anthropic:claude-sonnet-4-20250514 |
| tools | Gmail tools (see below) |
| subagents | calendar_context |
| interrupt_on | send_email, draft_reply |
| system_prompt | Email triage assistant |

**Gmail Tools:**

| Tool | HITL |
|------|------|
| list_emails | No |
| get_email | No |
| search_emails | No |
| draft_reply | Yes |
| send_email | Yes |
| label_email | No |

**Sub-agent:**

| Name | Tools | Purpose |
|------|-------|---------|
| calendar_context | gcal_list_events, gcal_get_event | Check availability |

### 2. UI

React app matching screenshot layout:

```
┌──────────────┬─────────────────────────┐
│ TRIGGERS     │ TOOLBOX            +MCP │
│ + Add        │ [tools with HITL flags] │
├──────────────┼─────────────────────────┤
│ AGENT        │ SUB-AGENTS              │
│ Name         ├─────────────────────────┤
│ Instructions │ SKILLS                  │
└──────────────┴─────────────────────────┘
```

**Panels:** Triggers (orange), Toolbox (teal), Agent, Sub-agents (purple lines), Skills

**Interactions:** Edit instructions, toggle HITL badges, add/remove tools and subagents, chat drawer for testing

---

## Acceptance Criteria

- [ ] Agent triages inbox via list_emails → get_email loop
- [ ] draft_reply triggers HITL interrupt
- [ ] send_email triggers HITL interrupt  
- [ ] Resume with approve/edit/reject works
- [ ] calendar_context subagent checks availability
- [ ] UI layout matches screenshot
- [ ] UI chat pane invokes agent and handles HITL

---

## Reference

- deepagents: github.com/langchain-ai/deepagents
- HITL docs: docs.langchain.com/oss/python/deepagents/human-in-the-loop
- Screenshot: uploaded image