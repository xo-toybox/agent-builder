"""Agent chat endpoints."""

import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException

from backend.domain.exceptions import AgentNotFoundError, CredentialNotFoundError
from backend.application.use_cases.run_agent import RunAgentUseCase
from backend.api.dependencies import get_run_agent_use_case

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: dict[str, WebSocket] = {}


@router.websocket("/{agent_id}")
async def agent_chat(
    websocket: WebSocket,
    agent_id: str,
    run_agent: RunAgentUseCase = Depends(get_run_agent_use_case)
):
    """WebSocket endpoint for chatting with a specific agent.

    Streams tokens, tool calls, and HITL interrupts in real-time.
    """
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket

    logger.info(f"Agent chat connected: {connection_id} for agent {agent_id}")

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
                    await _run_agent(
                        run_agent,
                        agent_id,
                        thread_id,
                        user_content,
                        websocket,
                    )
                except AgentNotFoundError:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Agent not found: {agent_id}"
                    })
                except CredentialNotFoundError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Not authenticated. Please login first."
                    })
                except Exception:
                    logger.exception("Agent error")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Agent execution failed. Please retry."
                    })

            elif message.get("type") == "hitl_decision":
                decision = message.get("decision")
                tool_call_id = message.get("tool_call_id")
                new_args = message.get("new_args")

                try:
                    await _resume_agent(
                        run_agent,
                        agent_id,
                        thread_id,
                        tool_call_id,
                        decision,
                        new_args,
                        websocket,
                    )
                except Exception:
                    logger.exception("Resume error")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Agent resume failed. Please retry."
                    })

    except WebSocketDisconnect:
        logger.info(f"Agent chat disconnected: {connection_id}")
    finally:
        active_connections.pop(connection_id, None)


async def _run_agent(
    run_agent: RunAgentUseCase,
    agent_id: str,
    thread_id: str,
    user_content: str,
    websocket: WebSocket,
):
    """Run the agent and stream results to WebSocket."""
    async for event in run_agent.run(agent_id, thread_id, user_content):
        event_type = event.get("event")

        if event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                content = _extract_content(chunk.content)
                if content:
                    await websocket.send_json({
                        "type": "token",
                        "content": content,
                    })

        elif event_type == "on_tool_start":
            await websocket.send_json({
                "type": "tool_call",
                "name": event.get("name", ""),
                "args": event.get("data", {}).get("input", {}),
            })

        elif event_type == "on_tool_end":
            result = event.get("data", {}).get("output")
            await websocket.send_json({
                "type": "tool_result",
                "name": event.get("name", ""),
                "result": result if isinstance(result, (dict, list, str)) else str(result),
            })

    # Check for HITL interrupt
    agent, config = await run_agent.get_or_create_agent(agent_id, thread_id)
    state = agent.get_state(config)

    if state.next:
        # Agent is waiting for human input
        await _send_hitl_interrupt(state, websocket)
    else:
        await websocket.send_json({"type": "complete"})


async def _resume_agent(
    run_agent: RunAgentUseCase,
    agent_id: str,
    thread_id: str,
    tool_call_id: str,
    decision: str,
    new_args: dict | None,
    websocket: WebSocket,
):
    """Resume agent after HITL decision."""
    async for event in run_agent.resume(
        agent_id, thread_id, tool_call_id, decision, new_args
    ):
        event_type = event.get("event")

        if event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                content = _extract_content(chunk.content)
                if content:
                    await websocket.send_json({
                        "type": "token",
                        "content": content,
                    })

        elif event_type == "on_tool_start":
            await websocket.send_json({
                "type": "tool_call",
                "name": event.get("name", ""),
                "args": event.get("data", {}).get("input", {}),
            })

        elif event_type == "on_tool_end":
            result = event.get("data", {}).get("output")
            await websocket.send_json({
                "type": "tool_result",
                "name": event.get("name", ""),
                "result": result if isinstance(result, (dict, list, str)) else str(result),
            })

    # Check for another HITL interrupt
    agent, config = await run_agent.get_or_create_agent(agent_id, thread_id)
    state = agent.get_state(config)

    if state.next:
        await _send_hitl_interrupt(state, websocket)
    else:
        await websocket.send_json({"type": "complete"})


async def _send_hitl_interrupt(state, websocket: WebSocket):
    """Send HITL interrupt to client."""
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


def _extract_content(content) -> str:
    """Extract text content from various formats."""
    if isinstance(content, list):
        parts = []
        for block in content:
            if hasattr(block, "text"):
                parts.append(block.text)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts)
    elif isinstance(content, str):
        return content
    return str(content)
