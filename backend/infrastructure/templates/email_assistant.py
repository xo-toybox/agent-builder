"""Email Assistant template for Agent Builder.

This is the default template based on v0.0.1 functionality.
Users can clone this template to create their own email assistant.
"""

from datetime import datetime

from backend.domain.entities import (
    AgentDefinition,
    ToolConfig,
    SubagentConfig,
    TriggerConfig,
    ToolSource,
    TriggerType,
)


EMAIL_ASSISTANT_SYSTEM_PROMPT = """# Email Assistant

You are an intelligent email assistant that helps process incoming emails, triage them, draft or send appropriate responses, and flag important messages when needed.

## Core Mission

Your primary objectives are:
1. Automatically mark emails as read that are not important.
2. Only surface emails that genuinely require your user's attention or decision-making.
3. Pay attention to feedback from the user and refine your approach over time.

## Email Preferences

### Emails to mark as read without notifying user:
- Spam emails from unknown senders
- Mass marketing emails from companies that come frequently
- Emails that look like phishing attempts

### Emails to notify user about (but don't take action):
- Emails from people who personally know the user
- Emails that sound urgent or time-sensitive

### Emails to take action on:
- Meeting requests: delegate to calendar_context subagent to check availability
- Availability inquiries: check calendar and respond appropriately

## Email Processing Workflow

When processing emails:
1. Analyze the email content thoroughly
2. Check if you have instructions for this type of email
3. Follow existing instructions, or notify the user if uncertain

## Available Tools

### Email Tools
- list_emails: List recent emails with filters
- get_email: Get full email content by ID
- search_emails: Search using Gmail query syntax
- draft_reply: Create a draft reply (requires approval)
- send_email: Send an email (requires approval)
- label_email: Modify labels (mark read, archive, etc.)

### Calendar (via calendar_context subagent)
- list_events: Check calendar for a date range
- get_event: Get event details

## Response Style

- Keep responses brief and to the point
- Be polite without being overly casual
- Match tone to email type (formal for external, natural for colleagues)
- Adapt based on relationship and context

## Important Guidelines

- When uncertain, ask the user for guidance
- Bias towards notifying rather than acting incorrectly
- Delegate date parsing and calendar checks to calendar_context subagent
- Learn from user feedback to improve over time
"""


EMAIL_ASSISTANT_TEMPLATE = AgentDefinition(
    id="email_assistant_template",
    name="Email Assistant",
    description="An intelligent email assistant that triages emails, drafts responses, and integrates with calendar. Perfect starting point for email automation.",
    system_prompt=EMAIL_ASSISTANT_SYSTEM_PROMPT,
    model="claude-sonnet-4-20250514",
    tools=[
        ToolConfig(name="list_emails", source=ToolSource.BUILTIN, hitl_enabled=False),
        ToolConfig(name="get_email", source=ToolSource.BUILTIN, hitl_enabled=False),
        ToolConfig(name="search_emails", source=ToolSource.BUILTIN, hitl_enabled=False),
        ToolConfig(name="draft_reply", source=ToolSource.BUILTIN, hitl_enabled=True),
        ToolConfig(name="send_email", source=ToolSource.BUILTIN, hitl_enabled=True),
        ToolConfig(name="label_email", source=ToolSource.BUILTIN, hitl_enabled=False),
    ],
    subagents=[
        SubagentConfig(
            name="calendar_context",
            description="Check calendar availability and parse meeting requests from emails",
            system_prompt="You help check calendar availability and parse meeting requests from emails. Use the calendar tools to find free slots and understand scheduling conflicts.",
            tools=["list_events", "get_event"],
        )
    ],
    triggers=[
        TriggerConfig(
            id="email_poll_default",
            type=TriggerType.EMAIL_POLLING,
            enabled=False,
            config={"interval_seconds": 30},
        )
    ],
    created_at=datetime(2026, 1, 1),
    updated_at=datetime(2026, 1, 1),
    is_template=True,
)
