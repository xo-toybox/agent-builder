"""FastAPI dependencies for Agent Builder.

Provides dependency injection for repositories, use cases, and services.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.persistence.sqlite.database import get_session
from backend.infrastructure.persistence.sqlite.agent_repo import SQLiteAgentRepository
from backend.infrastructure.persistence.sqlite.mcp_repo import SQLiteMCPRepository
from backend.infrastructure.persistence.sqlite.hitl_repo import SQLiteHITLRepository
from backend.infrastructure.persistence.sqlite.conversation_repo import SQLiteConversationRepository
from backend.infrastructure.persistence.sqlite.credential_store import SQLiteCredentialStore
from backend.infrastructure.persistence.sqlite.memory_repo import (
    MemoryRepository,
    MemoryEditRequestRepository,
)
from backend.infrastructure.persistence.sqlite.skill_repo import SkillRepository
from backend.infrastructure.persistence.sqlite.memory_fs import MemoryFileSystem
from backend.infrastructure.persistence.sqlite.wizard_repo import WizardConversationRepository
from backend.infrastructure.tools.registry import ToolRegistryImpl
from backend.application.builder import BuilderWizard
from backend.application.use_cases.run_agent import RunAgentUseCase
from backend.application.services.skill_loader import SkillLoader


# v0.0.3: Removed singleton pattern - MemoryFileSystem now created per-request
# to avoid stale session references


# Repository dependencies

async def get_agent_repo(session: AsyncSession = Depends(get_session)):
    """Get AgentRepository instance."""
    return SQLiteAgentRepository(session)


async def get_mcp_repo(session: AsyncSession = Depends(get_session)):
    """Get MCPRepository instance."""
    return SQLiteMCPRepository(session)


async def get_hitl_repo(session: AsyncSession = Depends(get_session)):
    """Get HITLRepository instance."""
    return SQLiteHITLRepository(session)


async def get_conversation_repo(session: AsyncSession = Depends(get_session)):
    """Get ConversationRepository instance."""
    return SQLiteConversationRepository(session)


async def get_credential_store(session: AsyncSession = Depends(get_session)):
    """Get CredentialStore instance."""
    return SQLiteCredentialStore(session)


async def get_memory_repo(session: AsyncSession = Depends(get_session)):
    """Get MemoryRepository instance (v0.0.3)."""
    return MemoryRepository(session)


async def get_memory_edit_repo(session: AsyncSession = Depends(get_session)):
    """Get MemoryEditRequestRepository instance (v0.0.3)."""
    return MemoryEditRequestRepository(session)


async def get_skill_repo(session: AsyncSession = Depends(get_session)):
    """Get SkillRepository instance (v0.0.3)."""
    return SkillRepository(session)


async def get_skill_loader(skill_repo=Depends(get_skill_repo)):
    """Get SkillLoader service instance (v0.0.3: progressive disclosure)."""
    return SkillLoader(skill_repo)


async def get_wizard_conversation_repo(session: AsyncSession = Depends(get_session)):
    """Get WizardConversationRepository instance (v0.0.3)."""
    return WizardConversationRepository(session)


async def get_memory_fs(
    agent_repo=Depends(get_agent_repo),
    memory_repo=Depends(get_memory_repo),
    skill_repo=Depends(get_skill_repo),
    skill_loader=Depends(get_skill_loader),
):
    """Get MemoryFileSystem instance (v0.0.3).

    Creates fresh instance per-request to avoid stale session references.
    Now includes SkillLoader for progressive disclosure of skills.
    """
    return MemoryFileSystem(agent_repo, skill_repo, memory_repo, skill_loader)


# Service dependencies

async def get_tool_registry(
    mcp_repo=Depends(get_mcp_repo),
    memory_fs=Depends(get_memory_fs),
    credential_store=Depends(get_credential_store),
):
    """Get ToolRegistry instance (v0.0.3: with memory and Slack tools support)."""
    return ToolRegistryImpl(mcp_repo, memory_fs, credential_store)


async def get_builder_wizard(
    agent_repo=Depends(get_agent_repo),
    conversation_repo=Depends(get_wizard_conversation_repo),
):
    """Get BuilderWizard instance (v0.0.3: with persistent conversation state)."""
    return BuilderWizard(agent_repo, conversation_repo)


async def get_run_agent_use_case(
    agent_repo=Depends(get_agent_repo),
    credential_store=Depends(get_credential_store),
    tool_registry=Depends(get_tool_registry),
    skill_loader=Depends(get_skill_loader),
):
    """Get RunAgentUseCase instance (v0.0.3: with progressive disclosure skills)."""
    return RunAgentUseCase(agent_repo, credential_store, tool_registry, skill_loader)


# Trigger manager - singleton
_trigger_manager = None


async def get_trigger_manager():
    """Get TriggerManager instance (singleton).

    TODO: Implement proper TriggerManager when we build out triggers.
    For now, returns a stub implementation.
    """
    global _trigger_manager
    if _trigger_manager is None:
        _trigger_manager = TriggerManagerStub()
    return _trigger_manager


class TriggerManagerStub:
    """Stub implementation of TriggerManager.

    To be replaced with full implementation in Phase 7.
    """

    def __init__(self):
        # Maps trigger_id -> agent_id
        self._running: dict[str, str] = {}

    async def start(self, agent_id: str, trigger_id: str) -> None:
        self._running[trigger_id] = agent_id

    async def stop(self, trigger_id: str) -> None:
        self._running.pop(trigger_id, None)

    async def stop_all(self, agent_id: str) -> None:
        # Filter and remove only triggers for this agent
        triggers_to_remove = [
            tid for tid, aid in self._running.items() if aid == agent_id
        ]
        for tid in triggers_to_remove:
            del self._running[tid]

    def list_running(self) -> list[str]:
        return list(self._running.keys())
