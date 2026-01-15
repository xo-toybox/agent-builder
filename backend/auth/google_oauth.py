import json
import logging
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from backend.config import settings

logger = logging.getLogger(__name__)


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
]

TOKEN_PATH = Path("data/google_token.json")


def _get_client_config() -> dict:
    """Build OAuth client config from settings."""
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def get_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    flow = Flow.from_client_config(_get_client_config(), scopes=SCOPES)
    flow.redirect_uri = settings.google_redirect_uri

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code(code: str, redirect_uri: str | None = None) -> Credentials:
    """Exchange authorization code for credentials."""
    config = _get_client_config()
    actual_redirect_uri = redirect_uri or settings.google_redirect_uri
    client_id = config['web']['client_id']
    client_secret = config['web']['client_secret']

    # Log partial credentials for debugging (safe - doesn't expose full secret)
    logger.info(f"OAuth exchange - client_id prefix: {client_id[:30]}... (len={len(client_id)})")
    logger.info(f"OAuth exchange - client_secret length: {len(client_secret)}")
    logger.info(f"OAuth exchange - redirect_uri: {actual_redirect_uri}")

    flow = Flow.from_client_config(config, scopes=SCOPES)
    flow.redirect_uri = actual_redirect_uri

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error(f"Token exchange failed: {type(e).__name__}: {e}")
        raise

    credentials = flow.credentials
    _save_credentials(credentials)
    return credentials


def _save_credentials(credentials: Credentials) -> None:
    """Save credentials to file."""
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(
        json.dumps(
            {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
            }
        )
    )


def get_credentials() -> Credentials | None:
    """Load credentials from file, refreshing if needed."""
    if not TOKEN_PATH.exists():
        return None

    data = json.loads(TOKEN_PATH.read_text())
    credentials = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data.get("client_id", settings.google_client_id),
        client_secret=data.get("client_secret", settings.google_client_secret),
        scopes=data.get("scopes", SCOPES),
    )

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        from google.auth.transport.requests import Request

        try:
            credentials.refresh(Request())
            _save_credentials(credentials)
        except Exception:
            logger.exception("Failed to refresh credentials")
            return None

    return credentials


def clear_credentials() -> None:
    """Remove stored credentials."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


def is_authenticated() -> bool:
    """Check if valid credentials exist."""
    credentials = get_credentials()
    return credentials is not None and credentials.valid
