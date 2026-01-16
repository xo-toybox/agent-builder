"""Trigger management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import get_agent_repo, get_trigger_manager

router = APIRouter(prefix="/triggers", tags=["triggers"])


class TriggerInfo(BaseModel):
    """Trigger information."""
    id: str
    type: str
    enabled: bool
    config: dict


class TriggerStatus(BaseModel):
    """Trigger status information."""
    id: str
    type: str
    enabled: bool
    running: bool
    config: dict


@router.get("/{agent_id}", response_model=list[TriggerStatus])
async def list_agent_triggers(
    agent_id: str,
    agent_repo=Depends(get_agent_repo),
    trigger_manager=Depends(get_trigger_manager)
):
    """List triggers for an agent with their running status."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    running_triggers = trigger_manager.list_running()

    return [
        TriggerStatus(
            id=t.id,
            type=t.type.value,
            enabled=t.enabled,
            running=t.id in running_triggers,
            config=t.config,
        )
        for t in agent.triggers
    ]


@router.post("/{agent_id}/{trigger_id}/start")
async def start_trigger(
    agent_id: str,
    trigger_id: str,
    agent_repo=Depends(get_agent_repo),
    trigger_manager=Depends(get_trigger_manager)
):
    """Start a trigger for an agent."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    trigger = next((t for t in agent.triggers if t.id == trigger_id), None)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    await trigger_manager.start(agent_id, trigger_id)

    # Update trigger enabled status
    trigger.enabled = True
    await agent_repo.save(agent)

    return {"success": True, "running": True}


@router.post("/{agent_id}/{trigger_id}/stop")
async def stop_trigger(
    agent_id: str,
    trigger_id: str,
    agent_repo=Depends(get_agent_repo),
    trigger_manager=Depends(get_trigger_manager)
):
    """Stop a trigger."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    trigger = next((t for t in agent.triggers if t.id == trigger_id), None)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    await trigger_manager.stop(trigger_id)

    # Update trigger enabled status
    trigger.enabled = False
    await agent_repo.save(agent)

    return {"success": True, "running": False}


@router.post("/{agent_id}/{trigger_id}/toggle")
async def toggle_trigger(
    agent_id: str,
    trigger_id: str,
    agent_repo=Depends(get_agent_repo),
    trigger_manager=Depends(get_trigger_manager)
):
    """Toggle a trigger on/off."""
    agent = await agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    trigger = next((t for t in agent.triggers if t.id == trigger_id), None)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    running_triggers = trigger_manager.list_running()
    is_running = trigger_id in running_triggers

    if is_running:
        await trigger_manager.stop(trigger_id)
        trigger.enabled = False
    else:
        await trigger_manager.start(agent_id, trigger_id)
        trigger.enabled = True

    await agent_repo.save(agent)

    return {"success": True, "running": not is_running, "enabled": trigger.enabled}
