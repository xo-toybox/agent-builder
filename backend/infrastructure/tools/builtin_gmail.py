"""Gmail tools for Agent Builder.

Refactored from backend/tools/gmail.py for v0.0.2 infrastructure layer.
"""

import base64
from email.mime.text import MIMEText
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class EmailSummary(BaseModel):
    """Summary of an email message."""
    id: str
    thread_id: str
    subject: str
    sender: str
    snippet: str
    date: str
    labels: list[str]
    is_unread: bool


class Email(BaseModel):
    """Full email message with body."""
    id: str
    thread_id: str
    subject: str
    sender: str
    to: list[str]
    cc: list[str]
    date: str
    body: str
    labels: list[str]
    is_unread: bool


class Draft(BaseModel):
    """Email draft."""
    id: str
    message_id: str
    thread_id: str


class SentEmail(BaseModel):
    """Sent email confirmation."""
    id: str
    thread_id: str


def _get_header(headers: list[dict], name: str) -> str:
    """Extract header value by name."""
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def _parse_email_summary(message: dict) -> EmailSummary:
    """Parse Gmail API message into EmailSummary."""
    headers = message.get("payload", {}).get("headers", [])
    labels = message.get("labelIds", [])

    return EmailSummary(
        id=message["id"],
        thread_id=message["threadId"],
        subject=_get_header(headers, "Subject") or "(no subject)",
        sender=_get_header(headers, "From"),
        snippet=message.get("snippet", ""),
        date=_get_header(headers, "Date"),
        labels=labels,
        is_unread="UNREAD" in labels,
    )


def _get_body(payload: dict) -> str:
    """Extract email body from payload."""
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                if part["body"].get("data"):
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
            elif part["mimeType"] == "text/html":
                if part["body"].get("data"):
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
            elif "parts" in part:
                body = _get_body(part)
                if body:
                    return body

    return ""


def _parse_email(message: dict) -> Email:
    """Parse Gmail API message into full Email."""
    headers = message.get("payload", {}).get("headers", [])
    labels = message.get("labelIds", [])

    to_header = _get_header(headers, "To")
    cc_header = _get_header(headers, "Cc")

    return Email(
        id=message["id"],
        thread_id=message["threadId"],
        subject=_get_header(headers, "Subject") or "(no subject)",
        sender=_get_header(headers, "From"),
        to=[addr.strip() for addr in to_header.split(",")] if to_header else [],
        cc=[addr.strip() for addr in cc_header.split(",")] if cc_header else [],
        date=_get_header(headers, "Date"),
        body=_get_body(message.get("payload", {})),
        labels=labels,
        is_unread="UNREAD" in labels,
    )


def create_gmail_tools(credentials: Credentials) -> list:
    """Create Gmail tools with injected credentials.

    Returns a list of LangChain tools for Gmail operations.
    """
    service = build("gmail", "v1", credentials=credentials)

    @tool
    def list_emails(
        max_results: int = Field(default=10, description="Maximum number of emails to return"),
        label: str = Field(default="INBOX", description="Gmail label to filter by"),
        unread_only: bool = Field(default=False, description="Only return unread emails"),
    ) -> list[dict[str, Any]]:
        """List emails from the inbox with optional filters."""
        query = ""
        if unread_only:
            query = "is:unread"

        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=[label], q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            full_msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata")
                .execute()
            )
            emails.append(_parse_email_summary(full_msg).model_dump())

        return emails

    @tool
    def get_email(
        email_id: str = Field(description="The ID of the email to retrieve"),
    ) -> dict[str, Any]:
        """Get full email content including body by email ID."""
        message = (
            service.users()
            .messages()
            .get(userId="me", id=email_id, format="full")
            .execute()
        )
        return _parse_email(message).model_dump()

    @tool
    def search_emails(
        query: str = Field(description="Gmail search query (e.g., 'from:john is:unread')"),
        max_results: int = Field(default=10, description="Maximum number of emails to return"),
    ) -> list[dict[str, Any]]:
        """Search emails using Gmail query syntax."""
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            full_msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata")
                .execute()
            )
            emails.append(_parse_email_summary(full_msg).model_dump())

        return emails

    @tool
    def draft_reply(
        email_id: str = Field(description="The ID of the email to reply to"),
        body: str = Field(description="The body of the reply"),
        cc: list[str] | None = Field(default=None, description="CC recipients"),
    ) -> dict[str, Any]:
        """Create a draft reply to an email. Requires human approval before sending."""
        # Get original email for reply headers
        original = (
            service.users()
            .messages()
            .get(userId="me", id=email_id, format="full")
            .execute()
        )

        headers = original.get("payload", {}).get("headers", [])
        subject = _get_header(headers, "Subject")
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        reply_to = _get_header(headers, "Reply-To") or _get_header(headers, "From")
        message_id = _get_header(headers, "Message-ID")
        references = _get_header(headers, "References") or ""

        # Build MIME message
        mime_message = MIMEText(body)
        mime_message["to"] = reply_to
        mime_message["subject"] = subject
        mime_message["In-Reply-To"] = message_id
        mime_message["References"] = f"{references} {message_id}".strip()

        if cc:
            mime_message["cc"] = ", ".join(cc)

        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        draft = (
            service.users()
            .drafts()
            .create(
                userId="me",
                body={
                    "message": {"raw": raw, "threadId": original["threadId"]},
                },
            )
            .execute()
        )

        return Draft(
            id=draft["id"],
            message_id=draft["message"]["id"],
            thread_id=draft["message"]["threadId"],
        ).model_dump()

    @tool
    def send_email(
        to: list[str] = Field(description="List of recipient email addresses"),
        subject: str = Field(description="Email subject"),
        body: str = Field(description="Email body"),
        cc: list[str] | None = Field(default=None, description="CC recipients"),
        reply_to_id: str | None = Field(default=None, description="ID of email to reply to"),
    ) -> dict[str, Any]:
        """Send an email. Requires human approval."""
        thread_id = None

        if reply_to_id:
            original = (
                service.users()
                .messages()
                .get(userId="me", id=reply_to_id, format="metadata")
                .execute()
            )
            thread_id = original["threadId"]

            headers = original.get("payload", {}).get("headers", [])
            message_id = _get_header(headers, "Message-ID")
            references = _get_header(headers, "References") or ""
        else:
            message_id = None
            references = ""

        mime_message = MIMEText(body)
        mime_message["to"] = ", ".join(to)
        mime_message["subject"] = subject

        if cc:
            mime_message["cc"] = ", ".join(cc)

        if message_id:
            mime_message["In-Reply-To"] = message_id
            mime_message["References"] = f"{references} {message_id}".strip()

        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        message_body: dict[str, Any] = {"raw": raw}
        if thread_id:
            message_body["threadId"] = thread_id

        sent = (
            service.users()
            .messages()
            .send(userId="me", body=message_body)
            .execute()
        )

        return SentEmail(
            id=sent["id"],
            thread_id=sent["threadId"],
        ).model_dump()

    @tool
    def label_email(
        email_id: str = Field(description="The ID of the email to modify"),
        add_labels: list[str] | None = Field(default=None, description="Labels to add"),
        remove_labels: list[str] | None = Field(default=None, description="Labels to remove"),
    ) -> str:
        """Modify email labels (e.g., mark as read by removing UNREAD, archive by removing INBOX)."""
        body: dict[str, Any] = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        service.users().messages().modify(userId="me", id=email_id, body=body).execute()

        return f"Labels updated for email {email_id}"

    # Mark email-sending tools as always requiring HITL approval
    send_email.metadata = {"requires_hitl": True}
    draft_reply.metadata = {"requires_hitl": True}

    return [list_emails, get_email, search_emails, draft_reply, send_email, label_email]
