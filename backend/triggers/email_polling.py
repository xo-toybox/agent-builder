import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


logger = logging.getLogger(__name__)


class EmailPollingTrigger:
    """Polls Gmail for new emails and triggers the agent."""

    def __init__(
        self,
        credentials: Credentials,
        interval_seconds: int = 30,
        on_new_email: Callable[[dict], Any] | None = None,
    ):
        self.credentials = credentials
        self.interval = interval_seconds
        self.on_new_email = on_new_email
        self.last_check = datetime.now(timezone.utc)
        self.running = False
        self._task: asyncio.Task | None = None
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build("gmail", "v1", credentials=self.credentials)
        return self._service

    async def start(self) -> None:
        """Start the polling loop."""
        if self.running:
            logger.warning("Polling already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Email polling started (interval: {self.interval}s)")

    async def stop(self) -> None:
        """Stop the polling loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Email polling stopped")

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self.running:
            try:
                await self._check_new_emails()
            except Exception as e:
                logger.error(f"Error checking emails: {e}")

            await asyncio.sleep(self.interval)

    async def _check_new_emails(self) -> None:
        """Check for new unread emails since last check."""
        # Capture check time at start to avoid missing emails that arrive during processing
        check_start_time = datetime.now(timezone.utc)

        # Convert to Unix timestamp for Gmail query
        timestamp = int(self.last_check.timestamp())
        query = f"is:unread after:{timestamp}"

        # Run in executor since gmail client is sync
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=10)
            .execute(),
        )

        messages = results.get("messages", [])

        if messages:
            logger.info(f"Found {len(messages)} new emails")

        for msg in messages:
            try:
                # Get full message
                full_msg = await loop.run_in_executor(
                    None,
                    lambda msg_id=msg["id"]: self.service.users()
                    .messages()
                    .get(userId="me", id=msg_id, format="full")
                    .execute(),
                )

                if self.on_new_email:
                    await self._handle_new_email(full_msg)

            except Exception as e:
                logger.exception(f"Error processing email {msg['id']}: {e}")

        # Update last check time to when we started this check
        # This ensures emails arriving during processing are caught next poll
        self.last_check = check_start_time

    async def _handle_new_email(self, message: dict) -> None:
        """Handle a new email by triggering the callback."""
        # Parse email for display
        headers = message.get("payload", {}).get("headers", [])
        subject = next(
            (h["value"] for h in headers if h["name"].lower() == "subject"),
            "(no subject)",
        )
        sender = next(
            (h["value"] for h in headers if h["name"].lower() == "from"),
            "Unknown",
        )

        email_info = {
            "id": message["id"],
            "thread_id": message["threadId"],
            "subject": subject,
            "sender": sender,
            "snippet": message.get("snippet", ""),
        }

        logger.info(f"New email: {subject} from {sender}")

        if self.on_new_email:
            if asyncio.iscoroutinefunction(self.on_new_email):
                await self.on_new_email(email_info)
            else:
                self.on_new_email(email_info)
