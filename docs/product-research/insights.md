# LangSmith Agent Builder Analysis

Analysis of the official LangSmith Agent Builder to inform our v0.0.3+ development.

---

## User Journey

### 1. Agent Creation & Setup
- User creates agent from template or scratch
- Configures initial tools, triggers, sub-agents, skills
- Agent gets a name, description, and system instructions

### 2. Conversational Refinement
- User chats with agent to refine its behavior
- Agent can **modify its own configuration** through conversation
- User provides feedback, agent learns and adapts

### 3. Tool Discovery & Self-Configuration
- Agent can discover available tools and add them to itself
- Uses `Read Tools`, `Edit File`, `Read File` to modify its own setup
- Example: "Let me add these Slack reading tools to my configuration"

### 4. Feedback Loop
- User provides feedback in external channels (Slack threads)
- Agent reads feedback and updates its memory/behavior
- Continuous learning cycle

---

## Agent Architecture

### Self-Modifying Capabilities
The agent has tools to modify its own configuration:
- **Read File** - Read its own instruction files
- **Edit File** - Modify instructions, add learned preferences
- **Read Tools** - Discover available tools to add
- **Write to memory** - Store user preferences and learned data

### Memory System
- **File-based storage** - Memory stored as editable files (markdown)
- **User profile** - Stores resume, work history, preferences
- **Learned behaviors** - Search strategies, communication preferences
- **Skills** - Reusable instruction sets

### Sub-Agents
- Focused agents for specific tasks (e.g., `calendar_context`)
- Can be delegated to for specialized work
- Have their own tools and instructions

### Skills System
- Named instruction sets: `job-posting-tracker`, `job-search-strategies`
- Reusable across conversations
- Can be created/edited through conversation

---

## Agent Behavior Patterns

### 1. Transparency About Capabilities
Agent clearly communicates what it can and cannot do:

```
✅ What I can now do:
- Read channel history from your Slack channel
- Read thread messages (your replies to individual job postings)
- Monitor for your feedback when you tell me to check

⚠️ What I still can't do automatically:
- Real-time monitoring without being prompted
- Automatic emoji detection
```

### 2. Proactive Options
Agent presents actionable choices:

```
Should I:
A) Wait for your feedback on the current 9 postings first
B) Do a targeted search for higher-level/FDE-style roles now
C) Check Anthropic's specific posting you mentioned

What would you prefer?
```

### 3. Workflow Explanation
Agent explains how processes will work:

```
How this will work:
1. You reply to job threads in Slack with feedback
2. You tell me "check my Slack feedback" or "I've replied to some postings"
3. I'll read the channel history and thread messages to gather your feedback
4. I'll update my memory and search criteria based on your input
```

### 4. Expectation Setting
Agent sets realistic expectations:

```
Note: I want to set the right expectation - I don't have real-time
Slack monitoring capabilities built in yet. This means:
1. You'll need to explicitly tell me when you've left feedback in Slack
```

### 5. Proactive Automation Suggestions
Agent suggests future improvements:

```
For true automation (daily cron job), I could:
- Check Slack at the start of each run
- Gather any new feedback since last check
- Incorporate learnings into that day's search
```

---

## Tool Call UI Patterns

### Collapsible Tool Chips
- Tool calls shown as expandable chips with service icon
- Teal/green border, service logo, tool name
- Expands to show: ARGUMENTS, RESULT
- Multiple tool calls stack vertically

### Tool Call Structure
```
┌─────────────────────────────────┐
│ 🔗 Slack Send Channel Message ▼ │
├─────────────────────────────────┤
│ ARGUMENTS                       │
│   channel_id: C0A9S2KAN3B      │
│   message: [content...]         │
├─────────────────────────────────┤
│ RESULT                          │
│ {"success": true, ...}          │
└─────────────────────────────────┘
```

---

## Canvas/Configuration Panel

### Layout Structure
```
┌─────────────┐
│  TRIGGERS   │ ← Schedule, Slack, Gmail triggers
│  + Add      │
└─────────────┘
       │
       ▼
┌─────────────┐
│   TOOLBOX   │ ← Available tools with edit/delete
│ + Add  MCP  │
├─────────────┤
│ • Tool 1  ✏️🗑️│
│ • Tool 2  ✏️🗑️│
└─────────────┘
       │
       ▼
┌─────────────┐
│    AGENT    │ ← Name, description
│ INSTRUCTIONS│ ← System prompt (Edit button)
└─────────────┘
       │
       ▼
┌─────────────┐
│ SUB-AGENTS  │ ← Specialized sub-agents
│ + Add       │
├─────────────┤
│ • subagent ✏️🗑️│
└─────────────┘
       │
       ▼
┌─────────────┐
│   SKILLS    │ ← Reusable instruction sets
│ + Add       │
├─────────────┤
│ • skill-1  ✏️🗑️│
│ • skill-2  ✏️🗑️│
└─────────────┘
```

### Connection Lines
- Dotted lines connect panels showing data flow
- Visual representation of agent architecture

---

## Quality is Instruction-Driven, Not Model-Driven

A critical insight: the quality differences between LangSmith agents and ours are **primarily instruction-driven**, not model-driven. A well-instructed Claude 3.5 Sonnet can achieve similar quality to what we observed.

### Evidence It's Instructions

1. **Structured output patterns** - The ✅/⚠️ indicators, A/B/C options, numbered workflows are prompt-engineered behaviors
2. **Self-awareness language** - "What I can now do" / "What I still can't do" follows instructed transparency patterns
3. **Proactive suggestions** - "For true automation, I could..." follows a pattern of suggesting improvements
4. **Consistent formatting** - Every response follows the same communication structure

### What Their Instructions Likely Include

```markdown
## Communication Style
- Use ✅ for capabilities you have, ⚠️ for limitations
- Present options as A) B) C) when multiple paths exist
- Explain workflows step-by-step with numbered lists
- Set expectations about what requires manual intervention

## Self-Improvement
- When user corrects you, update your memory
- Explain what you're updating and why
- Confirm the update was made

## Proactive Behavior
- Suggest automation opportunities
- Offer to add tools when capabilities are needed
- Propose workflow improvements based on usage patterns
```

### The Real Differentiator: Self-Modification Architecture

The **self-modification tools** (Read File, Edit File, Read Tools) create a feedback loop where the agent can actually improve itself. This isn't model quality - it's architecture:

1. Agent encounters limitation
2. Agent uses `Read Tools` to discover available capabilities
3. Agent uses `Edit File` to update its own configuration
4. Agent behavior improves for future interactions

This creates compounding quality improvement that no amount of prompt engineering alone can achieve.

### Implications for Our Implementation

| Aspect | Current State | Recommended Change |
|--------|---------------|-------------------|
| Instruction patterns | Basic system prompt | Add communication style, transparency, proactive behavior sections |
| Self-modification | Memory write only (HITL) | Consider read-only self-introspection tools |
| Feedback loop | User approves memory | Agent can read its own config to understand capabilities |

---

## Key Differentiators from Our Implementation

| Feature | LangSmith | Our v0.0.3 |
|---------|-----------|------------|
| Self-modification | Agent can edit its own config | Memory write only |
| User messages | Light gray background | Purple background |
| Tool calls | Collapsible chips | Full message blocks |
| Canvas | Connected node graph | Static panels |
| Sub-agents | Full support | Data structure only |
| Threads | Multiple conversation threads | Single thread |
| Tool discovery | Agent can list/add tools | Fixed at creation |

---

## Recommendations for v0.0.4+

### High Priority
1. **Self-modification tools** - Let agents edit their own instructions
2. **Better tool call UI** - Collapsible chips instead of full messages
3. **Transparency patterns** - ✅/⚠️ indicators, capability disclosure
4. **Proactive options** - A/B/C choice patterns in agent responses

### Medium Priority
5. **Threads** - Multiple conversation threads per agent
6. **Sub-agent execution** - Actually delegate to sub-agents
7. **Canvas connections** - Visual node graph with dotted lines
8. **Inline edit/delete** - Tool and skill management in canvas

### Agent Instruction Patterns to Adopt
```markdown
## Communication Style
- Use ✅ for capabilities, ⚠️ for limitations
- Present options as A) B) C) when multiple paths exist
- Explain workflows step-by-step
- Set expectations about what requires manual intervention

## Self-Improvement
- When user corrects you, update your memory
- Explain what you're updating and why
- Confirm the update was made

## Proactive Suggestions
- Suggest automation opportunities
- Offer to add tools when capabilities are needed
- Propose workflow improvements based on usage patterns
```

---

*Analysis conducted: January 17, 2026*
*Source: LangSmith Agent Builder at smith.langchain.com*
