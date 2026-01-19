# LangSmith Agent Builder Reference

Reference documentation for LangChain's Agent Builder platform. Used to inform our design decisions.

---

## Executive Summary

LangSmith Agent Builder is a no-code agent building platform that launched GA on January 13, 2026. Unlike visual workflow builders (n8n, Zapier, OpenAI Agent Builder), it creates true LLM-powered agents that reason dynamically rather than following predetermined paths.

**Key differentiation:** All complexity is pushed into the prompt, not into visual workflow logic.

---

## Core Design Philosophy

### "Not Another Workflow Builder"

Visual workflow builders are being squeezed from both ends:

| Complexity Level | Optimal Solution |
|------------------|------------------|
| Low | No-code agents (prompt + tools in a loop) |
| Medium | No-code workflows ← *shrinking zone* |
| High | Code (LangGraph) |

As models improve, the ceiling for what agents can reliably handle rises, while the floor for "needs code" drops as AI-assisted coding democratizes.

### Two Pitfalls of Visual Workflow Builders

1. **Not actually low barrier** — Non-technical users still struggle with nodes, edges, and branching logic
2. **Complexity explodes visually** — Complex tasks quickly become unmanageable spaghetti graphs

### The Agent Alternative

Agents delegate decision-making to the LLM itself. Rather than mapping every branch upfront, agents reason dynamically. Complexity lives in the prompt, not the graph topology.

---

## Component Architecture

Every agent consists of four core components:

```
┌─────────────────────────────────────────────────────────────┐
│                        AGENT                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   PROMPT    │  │    TOOLS    │  │      TRIGGERS       │ │
│  │             │  │    (MCP)    │  │                     │ │
│  │ The brain   │  │ External    │  │ Background events:  │ │
│  │ containing  │  │ services    │  │ - Email received    │ │
│  │ all logic   │  │ and data    │  │ - Slack message     │ │
│  │             │  │ connections │  │ - Scheduled time    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                     SUB-AGENTS                          ││
│  │  Decompose complexity into focused, delegated tasks     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

| Component | Description |
|-----------|-------------|
| **Prompt** | The brain. All logic in natural language. Auto-generated through conversational setup. |
| **Tools** | External connections via MCP. OAuth integrations for Gmail, Slack, Calendar, Linear, LinkedIn. |
| **Triggers** | When agents run: chat, schedules (cron), or events (new email, Slack message). |
| **Subagents** | Specialized child agents for subtasks. Context isolation prevents pollution. |

---

## Underlying Technology: `deepagents`

Built on the open-source `deepagents` package, implementing patterns from Claude Code and Manus.

### Middleware Stack

```
TodoListMiddleware        → Task planning and progress tracking
FilesystemMiddleware      → File operations and context offloading (>20K tokens)
SubAgentMiddleware        → Delegate tasks to isolated sub-agents
SummarizationMiddleware   → Auto-summarize when context exceeds 170K tokens
PatchToolCallsMiddleware  → Fix dangling tool calls from interruptions
HumanInTheLoopMiddleware  → Pause execution for human approval
```

### Human-in-the-Loop Configuration

```python
interrupt_on={
    "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
    "create_event": {"allowed_decisions": ["approve", "reject"]},
    "read_email": False,  # No approval needed
}
```

---

## Memory Architecture

### Short-term Memory
Conversation context for multi-turn execution within a session.

### Long-term Memory
Persistent storage for preferences, corrections, and learned patterns via `CompositeBackend`.

Use cases:
- Priority rules (sender patterns, keywords)
- Writing style preferences (tone, formality, signature)
- Contact context (relationship notes)

---

## Feature Set (at GA)

### P0: Core Features
- Conversational agent creation with auto-generated prompts
- Built-in memory (short-term + long-term with self-updating prompts)
- MCP tool integrations (Gmail, Calendar, Slack, Linear, LinkedIn, Web search)
- Trigger system (chat, scheduled, event-based)
- Subagent orchestration with context isolation
- Human-in-the-loop approvals with Agent Inbox

### P1: Fast Follow
- Expanded OAuth (Salesforce, Gong, Notion)
- Agent templates library
- Usage analytics and run history

### P2: Roadmap
- Remote MCP server connections
- Workspace sharing and collaboration
- Multi-model support
- Programmatic API invocation

---

## Example Use Cases

### Daily Briefing Agent
```
Prompt: "Send me a daily meeting brief at 8 AM"

1. Reads calendar for today's meetings
2. Searches for participant info (LinkedIn, company news)
3. Pulls relevant CRM notes
4. Generates prep document
5. Sends via email/Slack (with approval)
```

### Slack Bug Triage Agent
```
Prompt: "Create Linear tickets when bugs are mentioned in #product-feedback"

1. Monitors Slack channel for bug-related messages
2. Extracts: description, severity, reporter
3. Searches for related existing tickets
4. Creates Linear issue with context
5. Requests approval, threads confirmation to Slack
```

### Email Triage Agent
```
Prompt: "Prioritize my inbox and draft responses to urgent messages"

1. Reads incoming emails
2. Classifies by priority (urgent, normal, low, spam)
3. Labels appropriately
4. Drafts responses for urgent emails (queued for approval)
5. Summarizes inbox status daily
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Agents created | 1,000+ in first 30 days |
| Agent completion rate | >70% deployed |
| Time to first agent | <10 minutes |
| User retention | >40% WAU/MAU |
| NPS | >30 |

---

## Timeline

| Date | Milestone |
|------|-----------|
| October 7, 2025 | "Not Another Workflow Builder" manifesto |
| October 29, 2025 | Private preview launch |
| December 2, 2025 | Public beta |
| January 13, 2026 | General availability |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Chat-based creation | Lower cognitive load than canvas; leverages model capability |
| Agent loop over DAG | Agents adapt dynamically; workflows require upfront edge-case mapping |
| Long-term memory | "Teach once, agent remembers" — eliminates manual prompt iteration |
| MCP for tools | Standard protocol; bring-your-own integrations |

---

## Authoritative Sources

### Documentation
- [Agent Builder Docs](https://docs.langchain.com/langsmith/agent-builder)
- [Deep Agents Overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [HITL Documentation](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop)

### Blog Posts
- [Not Another Workflow Builder](https://blog.langchain.com/not-another-workflow-builder/) (Oct 7, 2025)
- [Introducing Agent Builder](https://blog.langchain.com/langsmith-agent-builder/) (Oct 29, 2025)
- [Deep Agents](https://blog.langchain.com/deep-agents/) (Jul 30, 2025)
- [Agent Builder GA](https://blog.langchain.com/langsmith-agent-builder-generally-available/) (Jan 13, 2026)

### Source Code
- [deepagents](https://github.com/langchain-ai/deepagents) - Core agent harness
- [deepagents-quickstarts](https://github.com/langchain-ai/deepagents-quickstarts) - Examples
- [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) - React UI

---

*Consolidated from LangSmith PRD and design research. Last updated: January 2026*
