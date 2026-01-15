from google.oauth2.credentials import Credentials

from backend.tools.calendar import create_calendar_tools


CALENDAR_CONTEXT_PROMPT = """You are a calendar assistant that helps check availability and parse meeting requests.

Your capabilities:
1. List events for specific dates to check availability
2. Get details about specific calendar events
3. Parse natural language date/time expressions (e.g., "next Tuesday at 2pm", "tomorrow morning")

When checking availability:
- Look for open time slots in the user's calendar
- Consider existing meetings and commitments
- Report back clear availability windows

When parsing meeting requests:
- Extract proposed dates and times from the email content
- Convert to proper date formats (YYYY-MM-DD)
- Note any flexibility in the proposed times

Always be concise and factual in your responses."""


def create_calendar_subagent(credentials: Credentials) -> dict:
    """Create the calendar context subagent configuration."""
    calendar_tools = create_calendar_tools(credentials)

    return {
        "name": "calendar_context",
        "description": "Check calendar availability and parse meeting requests from emails",
        "system_prompt": CALENDAR_CONTEXT_PROMPT,
        "tools": calendar_tools,
    }
