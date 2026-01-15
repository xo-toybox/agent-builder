# LangSmith Agent Builder: Design Reference

## Executive Summary

LangSmith Agent Builder is a no-code agent creation platform that launched GA on January 13, 2026. It represents LangChain's deliberate departure from visual workflow builders toward a conversational agent-first paradigm.

---

## Core Design Philosophy

### "Not Another Workflow Builder"

The foundational thesis: visual workflow builders are being squeezed from both ends.

| Complexity Level | Optimal Solution |
|------------------|------------------|
| Low | No-code agents (prompt + tools in a loop) |
| Medium | No-code workflows ← *shrinking zone* |
| High | Code (LangGraph) |

**Key insight:** As models improve, the ceiling for what agents can reliably handle rises, while the floor for "needs code" drops as AI-assisted coding democratizes. The middle ground—visual workflow builders—contracts from both sides.

### Two Pitfalls of Visual Workflow Builders

1. **Not actually low barrier** — Non-technical users still struggle with nodes, edges, and branching logic
2. **Complexity explodes visually** — Complex tasks quickly become unmanageable spaghetti graphs

### The Agent Alternative

Agents delegate decision-making to the LLM itself. Rather than mapping every branch and edge case upfront, agents reason dynamically and adapt to new information. Complexity lives in the prompt, not the graph topology.

---

## Component Architecture

Every Agent Builder agent consists of four core components:

```
┌─────────────────────────────────────────────────────────────┐
│                        AGENT                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   PROMPT    │  │    TOOLS    │  │      TRIGGERS       │ │
│  │             │  │    (MCP)    │  │                     │ │
│  │ The brain   │  │ External    │  │ Background events:  │ │
│  │ containing  │  │ services    │  │ - Email received    │ │
│  │ all logic   │  │ and data    │  │ - Slack message     │ │
│  │ in natural  │  │ connections │  │ - Scheduled time    │ │
│  │ language    │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                     SUB-AGENTS                          ││
│  │  Decompose complexity into focused, delegated tasks     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 1. Prompt

The "brain" of the agent. All complexity is pushed into natural language instructions rather than visual graph topology. Agent Builder addresses the prompt engineering challenge through:

- **Conversational creation flow** — Describe goals in plain language; the system asks clarifying questions and auto-generates the prompt
- **Built-in memory** — Agents remember corrections over time without manual prompt updates

### 2. Tools (MCP)

External service connections via Model Context Protocol. Agent Builder provides:

- Built-in integrations (Gmail, Slack, Linear, Google Calendar)
- Bring-your-own MCP servers for custom integrations
- Agent Authorization for secure OAuth connections

### 3. Triggers

Background activation beyond chat:

- Email received
- Slack message in specific channel
- Time-based schedules (daily briefings, weekly digests)

### 4. Sub-agents

Isolated task execution for complex workflows. Sub-agents have their own context windows, tools, and instructions. The main agent delegates via the `task` tool.

---

## Underlying Technology: `deepagents`

Agent Builder is built on the open-source `deepagents` package, which implements patterns observed in Claude Code and Manus.

### Built-in Capabilities

| Component | Purpose |
|-----------|---------|
| **Planning tool** (`write_todos`) | Long-horizon task decomposition |
| **Filesystem backend** | Context offloading for large results (>20K tokens) |
| **Sub-agent delegation** | Isolated execution with summary rollup |
| **Summarization middleware** | Auto-compress at 170K tokens |
| **Human-in-the-loop** | Interrupt/resume for sensitive operations |

### Middleware Stack

```
TodoListMiddleware        → Task planning and progress tracking
FilesystemMiddleware      → File operations and context offloading
SubAgentMiddleware        → Delegate tasks to isolated sub-agents
SummarizationMiddleware   → Auto-summarize when context exceeds limit
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

Decision types:
- **approve** — Execute with original arguments
- **edit** — Modify arguments before execution
- **reject** — Skip the tool call entirely

---

## Memory Architecture

### Short-term Memory
Conversation context for multi-turn execution within a session.

### Long-term Memory
Persistent storage for preferences, corrections, and learned patterns. Implemented via `CompositeBackend` routing specific paths to durable storage.

Use cases:
- Priority rules (sender patterns, keywords)
- Writing style preferences (tone, formality, signature)
- Contact context (relationship notes)

---

## Product Timeline

| Date | Milestone |
|------|-----------|
| October 7, 2025 | "Not Another Workflow Builder" manifesto published |
| October 29, 2025 | Agent Builder private preview launch |
| December 2, 2025 | Public beta release |
| January 13, 2026 | General availability |

---

## Authoritative Sources

### Primary Documentation

| Resource | URL |
|----------|-----|
| Agent Builder Docs | https://docs.langchain.com/langsmith/agent-builder |
| Deep Agents Overview | https://docs.langchain.com/oss/python/deepagents/overview |
| HITL Documentation | https://docs.langchain.com/oss/python/deepagents/human-in-the-loop |

### Blog Posts (Chronological)

| Title | Date | URL |
|-------|------|-----|
| Not Another Workflow Builder | Oct 7, 2025 | https://blog.langchain.com/not-another-workflow-builder/ |
| Introducing LangSmith's No Code Agent Builder | Oct 29, 2025 | https://blog.langchain.com/langsmith-agent-builder/ |
| Deep Agents | Jul 30, 2025 | https://blog.langchain.com/deep-agents/ |
| Agent Builder Public Beta | Dec 2, 2025 | https://blog.langchain.com/langsmith-agent-builder-now-in-public-beta/ |
| Agent Builder GA | Jan 13, 2026 | https://blog.langchain.com/langsmith-agent-builder-generally-available/ |

### Source Code

| Repository | Description | URL |
|------------|-------------|-----|
| deepagents | Core agent harness | https://github.com/langchain-ai/deepagents |
| deepagents-quickstarts | Example implementations | https://github.com/langchain-ai/deepagents-quickstarts |
| deepagentsjs | TypeScript version | https://github.com/langchain-ai/deepagentsjs |
| deep-agents-ui | Custom React UI | https://github.com/langchain-ai/deep-agents-ui |

### Related Reading

| Title | URL |
|-------|-----|
| How to Think About Agent Frameworks | https://blog.langchain.com/how-to-think-about-agent-frameworks/ |
| The Rise of Context Engineering | https://blog.langchain.com/the-rise-of-context-engineering/ |
| Agent Frameworks, Runtimes, and Harnesses | https://blog.langchain.com/agent-frameworks-runtimes-and-harnesses-oh-my/ |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Chat-based creation | Lower cognitive load than canvas; leverages model capability |
| Agent loop over DAG | Agents adapt dynamically; workflows require upfront edge-case mapping |
| Long-term memory | "Teach once, agent remembers" — eliminates manual prompt iteration |
| MCP for tools | Standard protocol; bring-your-own integrations |
| Workspace sharing | Clone + customize pattern enables team-wide scaling |

---

*Last updated: January 13, 2026*