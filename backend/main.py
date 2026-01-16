"""Agent Builder - Main FastAPI application.

v0.0.2 - Generic agent builder platform with chat-based creation,
MCP tools, and HITL approval.
"""

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.config import settings
from backend.infrastructure.persistence.sqlite.database import init_db
from backend.api.v1 import router as api_v1_router

# Legacy imports for backward compatibility
from backend.persistence import load_config, save_config
from backend.auth import (
    get_auth_url,
    exchange_code,
    get_credentials,
    clear_credentials,
    is_authenticated,
)
from backend.agent import create_email_agent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global state for legacy WebSocket
active_connections: dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Agent Builder v0.0.2...")

    # Ensure data directory exists
    data_dir = Path(settings.database_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Seed templates if needed
    try:
        from backend.migration.seed_templates import seed_templates
        await seed_templates()
    except ImportError:
        logger.info("Template seeding not yet implemented")
    except Exception as e:
        logger.warning(f"Template seeding failed: {e}")

    yield

    # Cleanup
    logger.info("Agent Builder stopped")


app = FastAPI(
    title="Agent Builder",
    version="0.0.2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API routes
app.include_router(api_v1_router)


# ============================================================================
# Legacy Auth Routes (for backward compatibility)
# ============================================================================


@app.get("/auth/login")
async def auth_login():
    """Redirect to Google OAuth."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    auth_url = get_auth_url()
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
async def auth_callback(code: str):
    """Handle OAuth callback."""
    try:
        redirect_uri = f"http://localhost:{settings.port}/auth/callback"
        exchange_code(code, redirect_uri=redirect_uri)
        return RedirectResponse(url=settings.frontend_url)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/google/callback")
async def auth_google_callback(code: str):
    """Handle OAuth callback (alternate path)."""
    try:
        redirect_uri = f"http://localhost:{settings.port}/auth/google/callback"
        exchange_code(code, redirect_uri=redirect_uri)
        return RedirectResponse(url=settings.frontend_url)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/status")
async def auth_status():
    """Check authentication status and return user info if authenticated."""
    authenticated = is_authenticated()
    if not authenticated:
        return {"authenticated": False, "email": None}

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


@app.post("/auth/logout")
async def auth_logout():
    """Clear stored credentials."""
    clear_credentials()
    return {"success": True}


# ============================================================================
# Legacy API Routes (for backward compatibility with v0.0.1 frontend)
# ============================================================================


TOOL_DESCRIPTIONS = {
    "list_emails": "List emails from inbox with optional filters",
    "get_email": "Get full email content by ID",
    "search_emails": "Search emails using Gmail query syntax",
    "draft_reply": "Create a draft reply to an email",
    "send_email": "Send an email",
    "label_email": "Modify email labels (mark read, archive)",
    "list_events": "List calendar events for a date range",
    "get_event": "Get calendar event details by ID",
}


@app.get("/api/agent")
async def get_agent_config():
    """Get current agent configuration (legacy)."""
    config = load_config()
    return config.model_dump()


class UpdateAgentRequest(BaseModel):
    name: str | None = None
    instructions: str | None = None


@app.put("/api/agent")
async def update_agent_config(request: UpdateAgentRequest):
    """Update agent configuration (legacy)."""
    config = load_config()

    if request.name is not None:
        config.name = request.name
    if request.instructions is not None:
        config.instructions = request.instructions

    save_config(config)
    return config.model_dump()


class ToolInfo(BaseModel):
    name: str
    description: str
    enabled: bool
    hitl: bool


@app.get("/api/tools")
async def get_tools() -> list[ToolInfo]:
    """List available tools with HITL status (legacy)."""
    config = load_config()

    tools = []
    for tool_name, description in TOOL_DESCRIPTIONS.items():
        tools.append(
            ToolInfo(
                name=tool_name,
                description=description,
                enabled=tool_name in config.tools,
                hitl=tool_name in config.hitl_tools,
            )
        )

    return tools


class ToggleHITLRequest(BaseModel):
    enabled: bool


@app.put("/api/tools/{tool_name}/hitl")
async def toggle_tool_hitl(tool_name: str, request: ToggleHITLRequest):
    """Toggle HITL for a tool (legacy)."""
    config = load_config()

    if request.enabled:
        if tool_name not in config.hitl_tools:
            config.hitl_tools.append(tool_name)
    else:
        if tool_name in config.hitl_tools:
            config.hitl_tools.remove(tool_name)

    save_config(config)
    return {"success": True, "hitl_tools": config.hitl_tools}


@app.get("/api/triggers")
async def get_triggers():
    """List configured triggers (legacy)."""
    config = load_config()
    return [t.model_dump() for t in config.triggers]


@app.post("/api/triggers/{trigger_id}/toggle")
async def toggle_trigger(trigger_id: str):
    """Enable/disable a trigger (legacy)."""
    config = load_config()
    trigger = next((t for t in config.triggers if t.id == trigger_id), None)

    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    trigger.enabled = not trigger.enabled
    save_config(config)

    return {"success": True, "enabled": trigger.enabled}


@app.get("/api/subagents")
async def get_subagents():
    """List configured subagents (legacy)."""
    config = load_config()
    return [s.model_dump() for s in config.subagents]


# ============================================================================
# Legacy WebSocket Chat (for backward compatibility)
# ============================================================================


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for chat with the agent (legacy v0.0.1 format)."""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    thread_id = str(uuid.uuid4())

    logger.info(f"WebSocket connected: {connection_id}")

    try:
        if not is_authenticated():
            await websocket.send_json({
                "type": "error",
                "message": "Not authenticated. Please login first.",
            })
            return

        credentials = get_credentials()
        if not credentials:
            await websocket.send_json({
                "type": "error",
                "message": "Failed to load credentials.",
            })
            return

        agent, _checkpointer = create_email_agent(credentials)
        config = {"configurable": {"thread_id": thread_id}}

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError as e:
                await websocket.send_json({"type": "error", "message": f"Invalid JSON: {e}"})
                continue

            if message["type"] == "message":
                user_content = message["content"]

                try:
                    await _run_agent(agent, config, user_content, websocket)
                except Exception as e:
                    logger.error(f"Agent error: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})

            elif message["type"] == "hitl_decision":
                decision = message["decision"]
                tool_call_id = message.get("tool_call_id")
                new_args = message.get("new_args")

                try:
                    await _resume_agent(agent, config, decision, tool_call_id, new_args, websocket)
                except Exception as e:
                    logger.error(f"Resume error: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    finally:
        active_connections.pop(connection_id, None)


async def _run_agent(agent, config: dict, user_content: str, websocket: WebSocket):
    """Run the agent and stream results to WebSocket."""
    input_messages = {"messages": [{"role": "user", "content": user_content}]}

    async for event in agent.astream_events(input_messages, config, version="v2"):
        event_type = event.get("event")

        if event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                content = _extract_content(chunk.content)
                if content:
                    await websocket.send_json({"type": "token", "content": content})

        elif event_type == "on_tool_start":
            tool_name = event.get("name", "")
            tool_input = event.get("data", {}).get("input", {})
            await websocket.send_json({"type": "tool_call", "name": tool_name, "args": tool_input})

        elif event_type == "on_tool_end":
            tool_name = event.get("name", "")
            tool_output = event.get("data", {}).get("output")
            await websocket.send_json({
                "type": "tool_result",
                "name": tool_name,
                "result": tool_output if isinstance(tool_output, (dict, list, str)) else str(tool_output),
            })

    state = agent.get_state(config)
    if state.next:
        messages = state.values.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    await websocket.send_json({
                        "type": "hitl_interrupt",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                    })
                    return

    await websocket.send_json({"type": "complete"})


async def _resume_agent(agent, config: dict, decision: str, tool_call_id: str | None, new_args: dict | None, websocket: WebSocket):
    """Resume agent after HITL decision."""
    from langchain_core.messages import ToolMessage, AIMessage

    if decision == "reject":
        agent.update_state(
            config,
            {"messages": [ToolMessage(content="Tool call rejected by user", tool_call_id=tool_call_id)]},
        )
        await websocket.send_json({"type": "tool_result", "name": "rejected", "result": "Tool call was rejected by user"})
        await websocket.send_json({"type": "complete"})
        return

    elif decision == "edit" and new_args:
        state = agent.get_state(config)
        messages = state.values.get("messages", [])

        updated_messages = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                updated_tool_calls = []
                for tc in msg.tool_calls:
                    if tc["id"] == tool_call_id:
                        updated_tool_calls.append({**tc, "args": new_args})
                    else:
                        updated_tool_calls.append(tc)
                updated_msg = AIMessage(content=msg.content, tool_calls=updated_tool_calls, id=msg.id)
                updated_messages.append(updated_msg)
            else:
                updated_messages.append(msg)

        agent.update_state(config, {"messages": updated_messages})

    async for event in agent.astream_events(None, config, version="v2"):
        event_type = event.get("event")

        if event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                content = _extract_content(chunk.content)
                if content:
                    await websocket.send_json({"type": "token", "content": content})

        elif event_type == "on_tool_start":
            tool_name = event.get("name", "")
            tool_input = event.get("data", {}).get("input", {})
            await websocket.send_json({"type": "tool_call", "name": tool_name, "args": tool_input})

        elif event_type == "on_tool_end":
            tool_name = event.get("name", "")
            tool_output = event.get("data", {}).get("output")
            await websocket.send_json({
                "type": "tool_result",
                "name": tool_name,
                "result": tool_output if isinstance(tool_output, (dict, list, str)) else str(tool_output),
            })

    state = agent.get_state(config)
    if state.next:
        messages = state.values.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    await websocket.send_json({
                        "type": "hitl_interrupt",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                    })
                    return

    await websocket.send_json({"type": "complete"})


def _extract_content(content) -> str:
    """Extract text content from various formats."""
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            elif isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
        return "".join(text_parts)
    elif isinstance(content, str):
        return content
    return str(content)


# ============================================================================
# Entry Point
# ============================================================================


def run():
    """Run the server."""
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
