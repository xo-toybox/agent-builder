"""API v1 routes for Agent Builder."""

from fastapi import APIRouter

from backend.api.v1 import agents, wizard, chat, tools, triggers, auth

router = APIRouter(prefix="/api/v1")

router.include_router(agents.router)
router.include_router(wizard.router)
router.include_router(chat.router)
router.include_router(tools.router)
router.include_router(triggers.router)
router.include_router(auth.router)

__all__ = ["router"]
