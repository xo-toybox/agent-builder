"""Credentials management API endpoints (v0.0.3).

Provides REST endpoints for managing integration credentials (Slack, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import get_credential_store
from backend.infrastructure.persistence.sqlite.credential_store import SQLiteCredentialStore
from backend.infrastructure.tools.builtin_slack import validate_slack_token

router = APIRouter(prefix="/credentials", tags=["credentials"])


class SlackTokenRequest(BaseModel):
    """Request model for saving Slack token."""

    token: str


class SlackStatusResponse(BaseModel):
    """Response model for Slack configuration status."""

    configured: bool


@router.post("/slack", response_model=SlackStatusResponse)
async def save_slack_token(
    data: SlackTokenRequest,
    credential_store: SQLiteCredentialStore = Depends(get_credential_store),
):
    """Save Slack bot token.

    Validates the token with Slack API before saving.

    Returns 400 if token format is invalid.
    Returns 401 if token is rejected by Slack.
    """
    # Validate token format
    if not data.token.startswith("xoxb-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid token format. Slack bot tokens start with 'xoxb-'",
        )

    # Validate with Slack API
    is_valid, error_msg = validate_slack_token(data.token)
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail=f"Slack token validation failed: {error_msg}",
        )

    # Save encrypted
    await credential_store.save("slack", {"token": data.token})

    return SlackStatusResponse(configured=True)


@router.get("/slack/status", response_model=SlackStatusResponse)
async def get_slack_status(
    credential_store: SQLiteCredentialStore = Depends(get_credential_store),
):
    """Check if Slack is configured."""
    slack_creds = await credential_store.get("slack")
    return SlackStatusResponse(configured=slack_creds is not None)


@router.delete("/slack", status_code=204)
async def delete_slack_token(
    credential_store: SQLiteCredentialStore = Depends(get_credential_store),
):
    """Remove Slack configuration."""
    await credential_store.delete("slack")
    return None
