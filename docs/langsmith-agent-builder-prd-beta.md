# LangSmith Agent Builder - Private Preview PRD

**Version:** 0.1  
**Release Date:** October 29, 2025  
**Status:** Private Preview (Invite-Only Beta)

---

## Executive Summary

LangSmith Agent Builder is a no-code agent building platform that enables non-technical users to create, deploy, and manage AI agents without writing code. Unlike visual workflow builders (n8n, Zapier, OpenAI Agent Builder), Agent Builder creates true LLM-powered agents that reason dynamically rather than following predetermined paths.

**Key differentiation:** All complexity is pushed into the prompt, not into visual workflow logic. Agents delegate decision-making to the LLM, enabling dynamic responses to complex, multi-step tasks.

---

## Problem Statement

### Current Challenges

1. **High barrier to entry:** Building agents requires programming expertise, limiting adoption to technical teams
2. **Visual workflow limitations:** Existing no-code tools use deterministic workflows that fail for complex, dynamic tasks—users must map every scenario upfront
3. **Prompt engineering complexity:** Writing effective prompts requires specialized knowledge most users lack
4. **Static behavior:** Traditional workflows don't improve with feedback; they must be manually rebuilt

### Target Users

- Business users with repetitive productivity tasks
- Operations teams managing cross-platform workflows
- Technical users seeking rapid prototyping without code
- Teams already using LangSmith for agent development

---

## Core Architecture

### Four Components (All P0)

Every agent in LangSmith Agent Builder consists of four core components:

| Component | Description |
|-----------|-------------|
| **Prompt** | The brain of the agent. Contains all logic describing what the agent should do. All complexity lives here, not in visual workflows. Auto-generated through conversational setup. |
| **Tools** | External connections via MCP (Model Context Protocol). OAuth integrations for Gmail, Slack, Calendar, Linear, LinkedIn. Users can also bring custom MCP servers. |
| **Triggers** | Define when agents run: chat invocation, time-based schedules (daily, weekly, cron), or event-based (new email, Slack message in channel). |
| **Subagents** | Specialized child agents for specific subtasks. Enable modular design and context isolation for complex workflows. |

### Underlying Technology: `deepagents`

Agent Builder is built on the `deepagents` package, which implements patterns from Claude Code, Deep Research, and Manus:

```
deepagents capabilities:
├── Planning (TodoListMiddleware)
│   └── Task decomposition and progress tracking
├── File System (FilesystemMiddleware)  
│   └── Context offloading for large tool results (>20K tokens)
├── Subagents (SubAgentMiddleware)
│   └── Isolated task delegation with context separation
├── Summarization (SummarizationMiddleware)
│   └── Auto-summarization when context exceeds 170K tokens
└── Human-in-the-Loop (HumanInTheLoopMiddleware)
    └── Approval workflows for sensitive actions
```

---

## Private Preview Feature Set

### P0: Must Have (Launch)

#### 1. Conversational Agent Creation
- Natural language interface for describing agent goals
- Guided follow-up questions to clarify requirements
- Auto-generation of detailed system prompts from user input
- Automatic tool selection and configuration based on described needs

#### 2. Built-in Memory System
- **Short-term memory:** Conversation context within a session
- **Long-term memory:** Captures user corrections and preferences
- **Self-updating prompts:** Agent updates its own instructions based on feedback
- **Tool memory:** Remembers tool configurations across sessions

#### 3. MCP Tool Integrations
Built-in OAuth integrations:
- Gmail (read, send, label, draft)
- Google Calendar (read, create events)
- Slack (read channels, send messages)
- Linear (create/update issues)
- LinkedIn (profile lookup)
- Web search (information retrieval)

#### 4. Trigger System
- **Chat:** Manual invocation through conversation
- **Scheduled:** Time-based (daily, weekly, custom cron expressions)
- **Event-based:** React to new emails, Slack messages in specific channels

#### 5. Subagent Orchestration
- Create specialized subagents for specific subtasks
- Context isolation between parent and child agents
- Subagents return summaries to parent, preventing context pollution

#### 6. Human-in-the-Loop Approvals
- Configurable approval gates for sensitive actions (sending emails, posting messages)
- Review and edit capability before execution
- Agent Inbox for monitoring threads with status indicators (idle, busy, interrupted, errored)

### P1: Should Have (Fast Follow)

- Expanded OAuth integrations (Salesforce, Gong, Notion)
- Agent templates library for common use cases
- Basic usage analytics and run history
- Improved error messaging and debugging

### P2: Post-Preview Roadmap

- Remote MCP server connections (bring your own tools)
- Workspace sharing and collaboration
- Multi-model support (OpenAI models)
- Programmatic API invocation
- Agent cloning and templates

---

## User Experience Flow

```
1. Describe Goal
   └── User: "Send me a daily summary of my schedule with meeting prep"

2. Guided Refinement  
   └── System asks: "What time should I send this? What info do you want about attendees?"

3. Tool Connection
   └── User authenticates Gmail, Calendar via OAuth

4. Configure Triggers
   └── User sets daily trigger at 8 AM

5. Test & Iterate
   └── User runs agent, provides feedback: "Include LinkedIn profiles for external attendees"
   └── Agent updates its memory/instructions

6. Deploy
   └── Agent runs autonomously, requests approval before sending
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Agents created | 1,000+ in first 30 days |
| Agent completion rate | >70% of created agents deployed |
| Time to first agent | <10 minutes average |
| User retention (weekly) | >40% WAU/MAU |
| NPS from beta users | >30 |

---

## Example Use Cases

### Daily Briefing Agent
```
Prompt: "Send me a daily meeting brief at 8 AM"

Behavior:
1. Reads calendar for today's meetings
2. For each meeting:
   - Searches for participant info (LinkedIn, company news)
   - Pulls relevant CRM notes if available
   - Summarizes previous interactions
3. Generates prep document
4. Sends via email or Slack (with approval if configured)
```

### Slack Bug Triage Agent
```
Prompt: "Create Linear tickets when bugs are mentioned in #product-feedback"

Behavior:
1. Monitors Slack channel for bug-related messages
2. Extracts: description, severity indicators, reporter
3. Searches for related existing tickets
4. Creates Linear issue with:
   - Title derived from message
   - Description with Slack context
   - Auto-assigned labels
5. Requests approval before posting
6. Threads confirmation back to Slack
```

### Email Triage Agent
```
Prompt: "Prioritize my inbox and draft responses to urgent messages"

Behavior:
1. Reads incoming emails
2. Classifies by priority (urgent, normal, low, spam)
3. Labels emails appropriately
4. For urgent emails:
   - Drafts response based on context
   - Queues for user approval
5. Summarizes inbox status daily
```

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent hallucination/errors | High | Human-in-the-loop approvals for sensitive actions; clear error messaging |
| OAuth security concerns | High | Scoped permissions; secure token storage; audit logs; admin-approved tools |
| Prompt quality issues | Medium | Guided creation flow; system generates prompts from conversation |
| Tool integration failures | Medium | Graceful degradation; retry logic; status monitoring in Agent Inbox |
| Context window overflow | Medium | FilesystemMiddleware auto-offloads large results; SummarizationMiddleware compresses history |

---

## Timeline

| Date | Milestone |
|------|-----------|
| Oct 29, 2025 | Private Preview launch (invite-only) |
| Nov 2025 | Expand beta pool, gather feedback, iterate on UX |
| Dec 2025 | Public Beta with expanded features |
| Q1 2026 | GA release target |

---

## Key Decisions & Rationale

### Why agents, not workflows?

> "A visual workflow builder is not 'low' barrier to entry. Complex tasks quickly get too complicated to manage in a visual builder. Rather than follow a predetermined path, agents can delegate more decision-making to an LLM, allowing for more dynamic responses."

### Why conversational creation?

> "Good prompts require detail and specificity, but most people lack prompt engineering experience. We make it easier by starting with a conversation instead of a blank canvas."

### Why built-in memory?

> "Prompts need to evolve as you discover edge cases. If you correct the agent, it will now remember that correction so you don't have to prompt it to do so again."

---

## References

- Blog announcement: https://blog.langchain.com/langsmith-agent-builder/
- deepagents package: https://github.com/langchain-ai/deepagents
- Open Agent Platform (predecessor): https://github.com/langchain-ai/open-agent-platform
