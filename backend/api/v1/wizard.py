"""Builder Wizard endpoints."""

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import logging

from backend.application.builder import BuilderWizard
from backend.api.dependencies import get_builder_wizard

router = APIRouter(prefix="/wizard", tags=["wizard"])
logger = logging.getLogger(__name__)


@router.websocket("/chat")
async def wizard_chat(
    websocket: WebSocket,
    wizard: BuilderWizard = Depends(get_builder_wizard)
):
    """WebSocket endpoint for builder wizard chat.

    Uses streaming to send tokens in real-time.
    """
    await websocket.accept()
    thread_id = str(uuid.uuid4())

    logger.info(f"Wizard chat connected: {thread_id}")

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid JSON: {e}"
                })
                continue

            if message.get("type") == "message":
                user_content = message.get("content", "")

                try:
                    async for event in wizard.stream_chat(thread_id, user_content):
                        await websocket.send_json(event)
                except Exception as e:
                    logger.error(f"Wizard error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message.get("type") == "clear":
                wizard.clear_conversation(thread_id)
                await websocket.send_json({
                    "type": "cleared"
                })

    except WebSocketDisconnect:
        logger.info(f"Wizard chat disconnected: {thread_id}")
        wizard.clear_conversation(thread_id)


@router.post("/chat")
async def wizard_chat_http(
    message: dict,
    wizard: BuilderWizard = Depends(get_builder_wizard)
):
    """HTTP endpoint for wizard chat (non-streaming).

    Use this for simple request/response interactions.
    """
    thread_id = message.get("thread_id", str(uuid.uuid4()))
    user_content = message.get("content", "")

    response = await wizard.chat(thread_id, user_content)

    return {
        "thread_id": thread_id,
        "response": response
    }
