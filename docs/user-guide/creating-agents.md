# Creating Agents

## Templates

Pre-configured agents you can clone and customize:

| Template | Description | Tools Included |
|----------|-------------|----------------|
| **Email Assistant** | Triages inbox, drafts replies, checks calendar | Gmail, Calendar, Memory |
| **Research Assistant** | Web research with preference learning | Web Search, Memory |

To use a template:
1. Click **"+ New Agent"**
2. Select the template
3. Optionally rename it
4. Start chatting

## Builder Wizard

Create custom agents through conversation.

### How It Works

1. Click the **"+"** button next to "My Agents" in the sidebar
2. Describe your needs in plain language
3. The builder asks clarifying questions
4. Review the proposed configuration
5. Click **"Create Agent"**

### Example Conversation

```
You: I need an agent that monitors my inbox for meeting requests
     and checks my calendar before responding

Builder: I can help with that! A few questions:
         1. Should it auto-respond or draft for your review?
         2. What times are you generally available?
         3. Should it handle rescheduling requests too?

You: Draft for review, weekdays 9-5 PM, yes handle reschedules

Builder: Got it. I'll create an agent with:
         - Gmail tools (read, draft)
         - Calendar tools (check availability)
         - HITL approval for all responses

         Ready to create?
```

### Tips

- Be specific about what requires your approval
- Mention tools you want (Slack, Calendar, etc.)
- Describe edge cases ("if urgent, notify me immediately")

## Editing Agents

After creation, customize in the editor:

### Instructions Tab
Edit the agent's system prompt directly. This controls its personality and behavior.

### Toolbox Tab
Enable/disable tools and set which require approval (HITL).

### Triggers Tab
Set up automated runs (scheduled, webhook, email polling). *UI available, execution coming in v0.0.4*

### Subagents Tab
Add specialized sub-agents for delegation. *UI available, orchestration coming in v0.0.4*

## Deleting Agents

1. Go to **"My Agents"** in sidebar
2. Click the trash icon next to the agent
3. Confirm deletion

**Note:** Templates cannot be deleted.
