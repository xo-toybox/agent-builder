# Tools Reference

Tools are capabilities your agent can use. Some require your approval (HITL = Human-in-the-Loop).

## Gmail Tools

| Tool | Approval | Description |
|------|----------|-------------|
| `list_emails` | No | List recent emails from inbox |
| `get_email` | No | Read full email content by ID |
| `search_emails` | No | Search using Gmail query syntax |
| `draft_reply` | **Yes** | Create a draft reply |
| `send_email` | **Yes** | Send an email |
| `label_email` | No | Add/remove labels, mark read/unread |

### Gmail Search Examples

```
from:boss@company.com          # From specific sender
is:unread                      # Unread only
subject:urgent                 # Subject contains "urgent"
after:2024/01/01              # After date
has:attachment                 # Has attachments
```

## Calendar Tools

| Tool | Approval | Description |
|------|----------|-------------|
| `list_events` | No | List events in date range |
| `get_event` | No | Get event details |

## Slack Tools

Requires Slack token configuration. See [Getting Started](./getting-started.md).

| Tool | Approval | Description |
|------|----------|-------------|
| `list_slack_channels` | No | List available channels |
| `send_slack_message` | **Yes** | Post message to channel |

## Memory Tools

| Tool | Approval | Description |
|------|----------|-------------|
| `write_memory` | **Yes** | Save to agent's knowledge |
| `read_memory` | No | Read from knowledge files |
| `list_memory` | No | List all knowledge files |

## Web Tools

| Tool | Approval | Description |
|------|----------|-------------|
| `web_search` | No | Search the internet |

**Note:** Requires `TAVILY_API_KEY` or `SERPAPI_KEY` environment variable.

## HITL Approval Flow

When a tool requires approval, you'll see a dialog with:

1. **Tool name** - What action is being taken
2. **Parameters** - The data being used (email content, recipient, etc.)
3. **Options**:
   - **Approve** - Execute as-is
   - **Edit** - Modify parameters before executing
   - **Reject** - Cancel the action

### Editing Before Approval

Click **Edit** to modify the parameters (shown as JSON). Common edits:
- Fix typos in email drafts
- Change recipients
- Adjust message tone

### Suspicious Pattern Warnings

The system highlights potentially risky content:
- External URLs
- Instructions to "always" or "never" do something
- Code snippets

Review highlighted content carefully before approving.

## Enabling/Disabling Tools

1. Open agent editor
2. Go to **Toolbox** tab
3. Toggle tools on/off
4. Check **"Requires Approval"** for sensitive tools
5. Click **Save Changes**
