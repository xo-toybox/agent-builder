# Memory & Skills

Agents can learn from your feedback and remember preferences across sessions.

## Memory

### How It Works

When you correct your agent, it may propose saving that learning:

```
You: Actually, I prefer bullet points over paragraphs

Agent: Got it! Would you like me to remember this preference
       for future responses?

       [Approve] [Edit] [Reject]
```

If approved, the agent stores this in its knowledge files and applies it going forward.

### What Gets Stored

- Communication preferences (tone, format, length)
- Domain knowledge (your team members, project names)
- Behavioral rules ("never email after 6pm")

### Viewing Memory

1. Open agent editor
2. Check the **Memory** section (coming in v0.0.4)

Currently, you can ask the agent: *"What do you remember about my preferences?"*

### Security

All memory writes require your approval. The system highlights suspicious patterns:
- URLs or external links
- Instructions containing "always" or "never"
- Code or scripts

Review these carefully before approving.

## Skills

Reusable instructions for specific tasks.

### Creating a Skill

1. Open agent editor
2. Click **Skills** tab
3. Click **"+ Add Skill"**
4. Fill in:
   - **Name**: Short identifier (e.g., "summarize_email")
   - **Description**: When to use it
   - **Instructions**: Step-by-step guidance

### Example Skill

```yaml
Name: weekly_summary
Description: Generate weekly email summary for team

Instructions: |
  When asked for a weekly summary:
  1. Search emails from the past 7 days
  2. Group by sender/project
  3. Highlight action items
  4. Format as bullet points
  5. Keep under 500 words
```

### When to Use Skills vs Memory

| Use Memory For | Use Skills For |
|----------------|----------------|
| Preferences ("I like bullet points") | Procedures ("How to write a summary") |
| Facts ("My manager is Alice") | Templates ("Email format for clients") |
| Rules ("Don't email on weekends") | Multi-step workflows |

### Skill Visibility

When an agent uses a skill, you'll see:
```
[Using skill: weekly_summary]
```

This helps you understand why the agent behaved a certain way.

## Persistence

Both memory and skills persist across:
- Browser refreshes
- Server restarts
- Multiple sessions

Your agent picks up exactly where you left off.
