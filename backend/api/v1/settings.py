"""Global settings API endpoints.

Provides REST endpoints for managing workspace-level settings:
- Default model
- Tavily API key (for web search)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import get_credential_store
from backend.infrastructure.persistence.sqlite.credential_store import SQLiteCredentialStore

router = APIRouter(prefix="/settings", tags=["settings"])

# Available models for selection
AVAILABLE_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-5-20251101",
    "claude-haiku-4-20250514",
]

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class GlobalSettings(BaseModel):
    """Global workspace settings."""

    default_model: str = DEFAULT_MODEL
    tavily_api_key: str | None = None  # Masked in response


class GlobalSettingsResponse(BaseModel):
    """Response model with masked API key."""

    default_model: str
    tavily_api_key_configured: bool
    tavily_api_key_preview: str | None  # Shows first 8 chars


class UpdateSettingsRequest(BaseModel):
    """Request for updating settings (partial updates allowed)."""

    default_model: str | None = None
    tavily_api_key: str | None = None


def _mask_api_key(key: str | None) -> str | None:
    """Return first 8 chars of API key for preview."""
    if not key:
        return None
    if len(key) <= 8:
        return key[:2] + "****"
    return key[:8] + "****"


@router.get("", response_model=GlobalSettingsResponse)
async def get_settings(
    credential_store: SQLiteCredentialStore = Depends(get_credential_store),
):
    """Get current global settings."""
    settings_data = await credential_store.get("global_settings")

    if not settings_data:
        return GlobalSettingsResponse(
            default_model=DEFAULT_MODEL,
            tavily_api_key_configured=False,
            tavily_api_key_preview=None,
        )

    return GlobalSettingsResponse(
        default_model=settings_data.get("default_model", DEFAULT_MODEL),
        tavily_api_key_configured=bool(settings_data.get("tavily_api_key")),
        tavily_api_key_preview=_mask_api_key(settings_data.get("tavily_api_key")),
    )


@router.put("", response_model=GlobalSettingsResponse)
async def update_settings(
    data: UpdateSettingsRequest,
    credential_store: SQLiteCredentialStore = Depends(get_credential_store),
):
    """Update global settings (partial update - only provided fields are changed)."""
    # Get existing settings
    existing = await credential_store.get("global_settings") or {}

    # Update only provided fields
    if data.default_model is not None:
        if data.default_model not in AVAILABLE_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model. Must be one of: {AVAILABLE_MODELS}",
            )
        existing["default_model"] = data.default_model
    if data.tavily_api_key is not None:
        # Empty string clears the key
        if data.tavily_api_key == "":
            existing.pop("tavily_api_key", None)
        else:
            existing["tavily_api_key"] = data.tavily_api_key

    # Ensure default model is set
    if "default_model" not in existing:
        existing["default_model"] = DEFAULT_MODEL

    # Save encrypted
    await credential_store.save("global_settings", existing)

    return GlobalSettingsResponse(
        default_model=existing.get("default_model", DEFAULT_MODEL),
        tavily_api_key_configured=bool(existing.get("tavily_api_key")),
        tavily_api_key_preview=_mask_api_key(existing.get("tavily_api_key")),
    )


@router.get("/models", response_model=list[dict])
async def list_available_models():
    """List available models for selection."""
    return [
        {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
        {"id": "claude-opus-4-5-20251101", "name": "Claude Opus 4.5"},
        {"id": "claude-haiku-4-20250514", "name": "Claude Haiku 4"},
    ]
