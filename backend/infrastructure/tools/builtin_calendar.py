"""Calendar tools for Agent Builder.

Refactored from backend/tools/calendar.py for v0.0.2 infrastructure layer.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """Calendar event."""
    id: str
    summary: str
    start: str
    end: str
    location: str | None = None
    description: str | None = None
    attendees: list[str] = []
    status: str = "confirmed"


def _parse_event(event: dict) -> CalendarEvent:
    """Parse Google Calendar API event."""
    start = event.get("start", {})
    end = event.get("end", {})

    # Handle all-day events vs timed events
    start_str = start.get("dateTime") or start.get("date", "")
    end_str = end.get("dateTime") or end.get("date", "")

    attendees = [
        a.get("email", "")
        for a in event.get("attendees", [])
        if a.get("email")
    ]

    return CalendarEvent(
        id=event["id"],
        summary=event.get("summary", "(No title)"),
        start=start_str,
        end=end_str,
        location=event.get("location"),
        description=event.get("description"),
        attendees=attendees,
        status=event.get("status", "confirmed"),
    )


def create_calendar_tools(credentials: Credentials) -> list:
    """Create Calendar tools with injected credentials.

    Returns a list of LangChain tools for Calendar operations.
    """
    service = build("calendar", "v3", credentials=credentials)

    @tool
    def list_events(
        date: str = Field(description="Date to list events for (format: YYYY-MM-DD)"),
        days: int = Field(default=1, description="Number of days to include"),
    ) -> list[dict[str, Any]]:
        """List calendar events for a date range."""
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = start_date.replace(tzinfo=timezone.utc)
        except ValueError:
            return [{"error": f"Invalid date format: {date}. Use YYYY-MM-DD."}]

        end_date = start_date + timedelta(days=days)

        time_min = start_date.isoformat()
        time_max = end_date.isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        return [_parse_event(event).model_dump() for event in events]

    @tool
    def get_event(
        event_id: str = Field(description="The ID of the calendar event to retrieve"),
    ) -> dict[str, Any]:
        """Get detailed information about a specific calendar event."""
        try:
            event = service.events().get(calendarId="primary", eventId=event_id).execute()
            return _parse_event(event).model_dump()
        except HttpError as e:
            return {"error": f"Failed to get event: {e.reason}"}

    return [list_events, get_event]
