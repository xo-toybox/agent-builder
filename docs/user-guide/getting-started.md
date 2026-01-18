# Getting Started

## Prerequisites

- Google account (for Gmail/Calendar access)
- Slack workspace (optional, for Slack integration)

## First-Time Setup

### 1. Start the Application

Open http://localhost:5173 in your browser.

### 2. Connect Google Account

1. Click **"Login with Google"** in the bottom-left sidebar
2. Sign in with your Google account
3. Grant access to Gmail and Calendar

You'll see your email address in the sidebar when connected.

### 3. (Optional) Connect Slack

1. Open any agent's editor
2. Click the **Slack** tab in the right panel
3. Enter your Slack Bot Token ([how to create a Slack app](https://api.slack.com/start/quickstart))
4. Click **Save**

**Getting a Slack token:**
- Create a Slack app at https://api.slack.com/apps
- Add Bot Token Scopes: `chat:write`, `channels:read`, `groups:read`
- Install to your workspace
- Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. (Optional) Enable Web Search

For agents to search the web, add one of these to your `.env`:

```bash
TAVILY_API_KEY=tvly-...    # Get from https://tavily.com
# OR
SERPAPI_KEY=...            # Get from https://serpapi.com
```

## Creating Your First Agent

### Option A: Use a Template

1. Click **"+ New Agent"** in the sidebar
2. Select **"Email Assistant"** or **"Research Assistant"**
3. The agent is ready to use immediately

### Option B: Build from Scratch

1. Click the **"+"** button next to "My Agents" in the sidebar
2. Describe what you want in natural language:
   ```
   "I want an agent that summarizes my unread emails every morning"
   ```
3. Answer the builder's clarifying questions
4. Click **"Create Agent"** when satisfied

## Chatting with Your Agent

1. Select an agent from **"My Agents"** in the sidebar
2. Type in the chat panel on the left
3. The agent will respond and may use tools (Gmail, Calendar, etc.)

### Approving Actions

Some actions require your approval:
- Sending emails
- Posting to Slack
- Saving to agent memory

You'll see an approval dialog with options to **Approve**, **Edit**, or **Reject**.

## Next Steps

- [Creating Agents](./creating-agents.md) - Builder wizard details
- [Memory & Skills](./memory-and-skills.md) - Teaching your agent
- [Tools Reference](./tools-reference.md) - Available capabilities
