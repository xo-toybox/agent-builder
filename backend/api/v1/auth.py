"""Authentication endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse

from backend.config import settings
from backend.auth import (
    get_auth_url,
    exchange_code,
    get_credentials,
    clear_credentials,
    is_authenticated,
)
from backend.api.dependencies import get_credential_store

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/login")
async def auth_login():
    """Redirect to Google OAuth."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    auth_url = get_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def auth_callback(
    code: str,
    credential_store=Depends(get_credential_store),
):
    """Handle OAuth callback."""
    try:
        redirect_uri = f"http://localhost:{settings.port}/api/v1/auth/callback"
        exchange_code(code, redirect_uri=redirect_uri)

        # Persist credentials to SQLite for v1 chat stack
        credentials = get_credentials()
        if credentials:
            await credential_store.save("google", {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
            })

        return RedirectResponse(url=settings.frontend_url)
    except Exception as e:
        logger.exception("OAuth callback error")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")


@router.get("/status")
async def auth_status():
    """Check authentication status and return user info if authenticated."""
    authenticated = is_authenticated()
    if not authenticated:
        return {"authenticated": False, "email": None}

    # Get user email from Gmail API
    try:
        credentials = get_credentials()
        if credentials:
            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=credentials)
            profile = service.users().getProfile(userId="me").execute()
            return {
                "authenticated": True,
                "email": profile.get("emailAddress"),
            }
    except Exception as e:
        logger.error(f"Failed to get user email: {e}")

    return {"authenticated": authenticated, "email": None}


@router.post("/logout")
async def auth_logout():
    """Clear stored credentials."""
    clear_credentials()
    return {"success": True}
