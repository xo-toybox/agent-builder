"""Slack integration tools for agents (v0.0.3).

Provides tools for listing channels and sending messages to Slack.
send_slack_message requires HITL approval.

Required Slack Bot Scopes:
- channels:read - List public channels
- groups:read - List private channels
- chat:write - Send messages
"""

from typing import Callable
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from langchain_core.tools import tool


def create_slack_tools(token: str) -> list[Callable]:
    """Create Slack tools with the provided bot token.

    Args:
        token: Slack bot token (xoxb-...)

    Returns:
        List of Slack tool functions
    """
    client = WebClient(token=token)

    @tool
    def list_slack_channels(limit: int = 100) -> str:
        """
        List available Slack channels.

        Use this to discover channels where you can send messages.

        Args:
            limit: Maximum number of channels to return (default 100)

        Returns:
            List of channels with id, name, and whether they are private
        """
        try:
            response = client.conversations_list(
                limit=limit, types="public_channel,private_channel"
            )
            channels = [
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "is_private": ch["is_private"],
                }
                for ch in response["channels"]
            ]
            if not channels:
                return "No channels found. The bot may not have access to any channels."

            result = "Available Slack channels:\n"
            for ch in channels:
                privacy = "(private)" if ch["is_private"] else ""
                result += f"- #{ch['name']} {privacy} [ID: {ch['id']}]\n"
            return result

        except SlackApiError as e:
            error_msg = e.response.get("error", str(e))
            if error_msg == "invalid_auth":
                return "Error: Invalid Slack token. Please reconfigure the Slack integration."
            elif error_msg == "missing_scope":
                return "Error: Bot token missing required scopes (channels:read, groups:read)."
            return f"Slack error: {error_msg}"

    @tool
    def send_slack_message(channel_id: str, text: str) -> str:
        """
        Send a message to a Slack channel. Requires user approval.

        Args:
            channel_id: The channel ID (e.g., "C1234567890"). Use list_slack_channels to find IDs.
            text: The message text to send

        Returns:
            Confirmation message or error
        """
        try:
            response = client.chat_postMessage(channel=channel_id, text=text)
            if response["ok"]:
                return f"Message sent successfully to channel {channel_id}."
            return f"Failed to send message: {response}"

        except SlackApiError as e:
            error_msg = e.response.get("error", str(e))
            if error_msg == "channel_not_found":
                return f"Error: Channel {channel_id} not found. Use list_slack_channels to find valid channels."
            elif error_msg == "not_in_channel":
                return f"Error: Bot is not in channel {channel_id}. Invite the bot first."
            elif error_msg == "invalid_auth":
                return "Error: Invalid Slack token. Please reconfigure the Slack integration."
            elif error_msg == "missing_scope":
                return "Error: Bot token missing chat:write scope."
            elif error_msg == "rate_limited":
                return "Error: Rate limited by Slack. Please wait before sending more messages."
            return f"Slack error: {error_msg}"

    # Mark as always requiring HITL approval
    send_slack_message.metadata = {"requires_hitl": True}

    return [list_slack_channels, send_slack_message]


def validate_slack_token(token: str) -> tuple[bool, str]:
    """Validate a Slack bot token.

    Args:
        token: Token to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not token:
        return False, "Token is required"

    if not token.startswith("xoxb-"):
        return False, "Token must start with 'xoxb-' (bot token)"

    try:
        client = WebClient(token=token)
        response = client.auth_test()
        if response["ok"]:
            return True, ""
        return False, "Token validation failed"
    except SlackApiError as e:
        error_msg = e.response.get("error", str(e))
        return False, f"Token validation failed: {error_msg}"
