"""Agent chat endpoints."""

import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException

from backend.domain.exceptions import AgentNotFoundError, CredentialNotFoundError
from backend.application.use_cases.run_agent import RunAgentUseCase
from backend.api.dependencies import (
    get_run_agent_use_case,
    get_memory_fs,
    get_memory_repo,
    get_memory_edit_repo,
)
from backend.infrastructure.persistence.sqlite.memory_fs import MemoryFileSystem
from backend.infrastructure.persistence.sqlite.memory_repo import (
    MemoryRepository,
    MemoryEditRequestRepository,
)
from backend.infrastructure.tools.security import detect_suspicious_patterns

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: dict[str, WebSocket] = {}


@router.websocket("/{agent_id}")
async def agent_chat(
    websocket: WebSocket,
    agent_id: str,
    run_agent: RunAgentUseCase = Depends(get_run_agent_use_case),
    memory_fs: MemoryFileSystem = Depends(get_memory_fs),
    memory_repo: MemoryRepository = Depends(get_memory_repo),
    memory_edit_repo: MemoryEditRequestRepository = Depends(get_memory_edit_repo),
):
    """WebSocket endpoint for chatting with a specific agent.

    Streams tokens, tool calls, and HITL interrupts in real-time.
    v0.0.3: Enhanced with memory edit request handling.
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
                        memory_fs,
                        memory_repo,
                        memory_edit_repo,
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
                except Exception as e:
                    logger.exception("Agent error")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Agent execution failed: {e}"
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
                        memory_fs,
                        memory_repo,
                        memory_edit_repo,
                    )
                except Exception as e:
                    logger.exception("Resume error")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Agent resume failed: {e}"
                    })

            # v0.0.3: Handle memory edit decisions
            elif message.get("type") == "memory_edit_decision":
                await _handle_memory_decision(
                    message,
                    agent_id,
                    thread_id,
                    run_agent,
                    memory_repo,
                    memory_edit_repo,
                    memory_fs,
                    websocket,
                )

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
    memory_fs: MemoryFileSystem,
    memory_repo: MemoryRepository,
    memory_edit_repo: MemoryEditRequestRepository,
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
        await _send_hitl_interrupt(
            state, agent_id, websocket, memory_fs, memory_edit_repo
        )
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
    memory_fs: MemoryFileSystem,
    memory_repo: MemoryRepository,
    memory_edit_repo: MemoryEditRequestRepository,
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
        await _send_hitl_interrupt(
            state, agent_id, websocket, memory_fs, memory_edit_repo
        )
    else:
        await websocket.send_json({"type": "complete"})


async def _send_hitl_interrupt(
    state,
    agent_id: str,
    websocket: WebSocket,
    memory_fs: MemoryFileSystem,
    memory_edit_repo: MemoryEditRequestRepository,
):
    """Send HITL interrupt to client.

    v0.0.3: Enhanced handling for write_memory tool with suspicious pattern detection.
    """
    messages = state.values.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # v0.0.3: Special handling for write_memory
                if tool_name == "write_memory":
                    path = tool_args.get("path", "")
                    content = tool_args.get("content", "")
                    reason = tool_args.get("reason", "")

                    # Get current content for diff view
                    current_content = await memory_fs.read_safe(agent_id, path)

                    # Detect suspicious patterns
                    suspicious_flags = detect_suspicious_patterns(content)

                    # Create edit request record
                    edit_request = await memory_edit_repo.create(
                        agent_id=agent_id,
                        path=path,
                        operation="write",
                        proposed_content=content,
                        previous_content=current_content,
                        reason=reason,
                    )

                    # Send memory-specific interrupt
                    await websocket.send_json({
                        "type": "memory_edit_request",
                        "request_id": edit_request["id"],
                        "tool_call_id": tool_call["id"],
                        "path": path,
                        "operation": "write",
                        "current_content": current_content,
                        "proposed_content": content,
                        "reason": reason,
                        "suspicious_flags": suspicious_flags,
                    })
                else:
                    # Regular HITL interrupt
                    await websocket.send_json({
                        "type": "hitl_interrupt",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "args": tool_args,
                    })
                return


async def _handle_memory_decision(
    message: dict,
    agent_id: str,
    thread_id: str,
    run_agent: RunAgentUseCase,
    memory_repo: MemoryRepository,
    memory_edit_repo: MemoryEditRequestRepository,
    memory_fs: MemoryFileSystem,
    websocket: WebSocket,
):
    """Handle memory edit decision from frontend.

    v0.0.3: Process approve/reject/edit decisions for memory writes.

    Security: Re-validates path and checks agent authorization to prevent TOCTOU attacks.
    """
    request_id = message.get("request_id")
    decision = message.get("decision")  # approve, reject, edit
    edited_content = message.get("edited_content")
    tool_call_id = message.get("tool_call_id")

    try:
        # Get the edit request
        edit_request = await memory_edit_repo.get(request_id)
        if not edit_request:
            await websocket.send_json({
                "type": "error",
                "message": f"Memory edit request not found: {request_id}"
            })
            return

        # Security: Verify agent ID matches to prevent cross-agent manipulation
        if edit_request.get("agent_id") != agent_id:
            logger.warning(
                f"Agent ID mismatch in memory decision: expected {agent_id}, got {edit_request.get('agent_id')}"
            )
            await websocket.send_json({
                "type": "error",
                "message": "Unauthorized: agent ID mismatch"
            })
            return

        # Security: Re-validate path to prevent TOCTOU attacks
        path = edit_request["path"]
        if not memory_fs.validate_path(agent_id, path):
            logger.warning(f"Invalid path in memory decision: {path}")
            await websocket.send_json({
                "type": "error",
                "message": f"Invalid memory path: {path}"
            })
            return

        if decision == "approve":
            # Write to memory
            content = edited_content or edit_request["proposed_content"]

            # Security: Always validate content size (both edited and original proposed content)
            is_valid, error_msg = memory_fs.validate_content_size(content)
            if not is_valid:
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg
                })
                return

            await memory_repo.save(
                agent_id=agent_id,
                path=path,
                content=content,
                previous_content=edit_request["previous_content"],
            )
            await memory_edit_repo.resolve(request_id, "approved", edited_content)

            await websocket.send_json({
                "type": "memory_edit_complete",
                "request_id": request_id,
                "success": True,
                "path": path,
            })

        elif decision == "reject":
            await memory_edit_repo.resolve(request_id, "rejected")
            await websocket.send_json({
                "type": "memory_edit_complete",
                "request_id": request_id,
                "success": False,
                "path": path,
            })

        elif decision == "edit":
            # Update with edited content and approve
            if edited_content:
                # Security: Validate edited content size
                is_valid, error_msg = memory_fs.validate_content_size(edited_content)
                if not is_valid:
                    await websocket.send_json({
                        "type": "error",
                        "message": error_msg
                    })
                    return

                await memory_repo.save(
                    agent_id=agent_id,
                    path=path,
                    content=edited_content,
                    previous_content=edit_request["previous_content"],
                )
                await memory_edit_repo.resolve(request_id, "approved", edited_content)
                await websocket.send_json({
                    "type": "memory_edit_complete",
                    "request_id": request_id,
                    "success": True,
                    "path": path,
                })

        # Resume agent if we have a tool_call_id
        if tool_call_id:
            # Convert to regular HITL decision
            hitl_decision = "approve" if decision in ("approve", "edit") else "reject"
            agent, config = await run_agent.get_or_create_agent(agent_id, thread_id)

            # Resume streaming
            async for event in run_agent.resume(
                agent_id, thread_id, tool_call_id, hitl_decision, None
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

            await websocket.send_json({"type": "complete"})

    except Exception as e:
        logger.exception("Memory decision error")
        await websocket.send_json({
            "type": "error",
            "message": f"Memory operation failed: {e}"
        })


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
