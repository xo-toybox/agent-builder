# Troubleshooting

## Connection Issues

### "Not Connected" in chat panel

**Cause:** WebSocket connection to backend failed.

**Solutions:**
1. Check backend is running: `uv run uvicorn backend.main:app --reload`
2. Refresh the browser
3. Check browser console for errors (F12 → Console)

### Google "Not Connected"

**Cause:** OAuth token expired or not set up.

**Solutions:**
1. Click **"Connect Google"** to re-authenticate
2. Verify redirect URI in Google Cloud Console matches `http://localhost:8000/api/v1/auth/callback`

## Agent Issues

### Agent doesn't respond

**Possible causes:**
- Backend crashed (check terminal)
- Missing `ANTHROPIC_API_KEY` in `.env`
- Rate limited by Anthropic API

**Solutions:**
1. Check backend terminal for errors
2. Verify API key: `echo $ANTHROPIC_API_KEY`
3. Wait a moment and retry

### Agent can't access emails

**Cause:** Google OAuth scope issue or token expired.

**Solutions:**
1. Re-authenticate with Google
2. Ensure Gmail API is enabled in Google Cloud Console
3. Check that you granted Gmail permissions during OAuth

### Slack messages fail

**Possible causes:**
- Invalid Slack token
- Bot not added to channel
- Token lacks required scopes

**Solutions:**
1. Verify token in agent editor → Slack tab
2. Add bot to channel: `/invite @your-bot-name`
3. Token needs scopes: `chat:write`, `channels:read`, `groups:read` (for private channels)

### Web search doesn't work

**Cause:** Missing API key.

**Solution:** Add to `.env`:
```bash
TAVILY_API_KEY=tvly-...    # from https://tavily.com
# OR
SERPAPI_KEY=...            # from https://serpapi.com
```
Restart backend after adding.

## Memory & Skills Issues

### Memory write rejected

**Cause:** Content flagged as suspicious.

**What to check:**
- Does content contain URLs? (highlighted in yellow)
- Does it have "always/never" instructions? (highlighted in red)

If the content is safe, you can still approve it manually.

### Skill not being used

**Possible causes:**
- Skill name doesn't match agent's understanding
- Description is unclear
- Instructions conflict with system prompt

**Solutions:**
1. Make skill description more specific
2. Ask agent: *"Do you have a skill for X?"*
3. Simplify skill instructions

## Data Issues

### Conversations lost

**Cause:** Database file deleted or corrupted.

**Location:** `data/agent_builder.db`

**Prevention:** Back up `data/` directory periodically.

### Agent settings not saving

**Cause:** SQLite write lock or permission issue.

**Solutions:**
1. Restart backend
2. Check file permissions on `data/` directory
3. Ensure only one backend instance is running

## Common Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| "Agent not found" | Agent ID doesn't exist | Refresh agent list |
| "Template cannot be deleted" | Trying to delete a template | Clone it first, then delete the clone |
| "Invalid JSON format" | Malformed edit in HITL dialog | Check JSON syntax |
| "Memory file not found" | Reading deleted memory | Agent's knowledge was cleared |
| "Rate limit exceeded" | Too many API calls | Wait 60 seconds |

## Getting Help

1. Check backend logs (terminal running uvicorn)
2. Check browser console (F12 → Console)
3. File an issue: https://github.com/anthropics/agent-builder/issues
