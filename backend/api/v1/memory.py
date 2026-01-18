"""Memory management API endpoints (v0.0.3).

Provides REST endpoints for viewing and managing agent memory files.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import get_memory_repo, get_memory_fs
from backend.infrastructure.persistence.sqlite.memory_repo import MemoryRepository
from backend.infrastructure.persistence.sqlite.memory_fs import MemoryFileSystem

router = APIRouter(prefix="/agents/{agent_id}/memory", tags=["memory"])


class MemoryFileResponse(BaseModel):
    """Response model for a memory file."""

    path: str
    content_type: str
    created_at: str
    updated_at: str
    size_bytes: int


class MemoryFileDetailResponse(BaseModel):
    """Response model for memory file with content."""

    path: str
    content: str
    content_type: str
    updated_at: str


class MemoryListResponse(BaseModel):
    """Response model for list of memory files."""

    files: list[MemoryFileResponse]


@router.get("", response_model=MemoryListResponse)
async def list_memory_files(
    agent_id: str,
    memory_repo: MemoryRepository = Depends(get_memory_repo),
):
    """List all memory files for an agent.

    Returns metadata for each file (path, type, timestamps, size).
    """
    # Get all files from knowledge directory
    paths = await memory_repo.list_files(agent_id, "knowledge")

    files = []
    for path in paths:
        file_data = await memory_repo.get(agent_id, path)
        if file_data:
            content = file_data.get("content", "")
            files.append(
                MemoryFileResponse(
                    path=file_data["path"],
                    content_type=file_data.get("content_type", "text/markdown"),
                    created_at=file_data["created_at"].isoformat(),
                    updated_at=file_data["updated_at"].isoformat(),
                    size_bytes=len(content.encode("utf-8")),
                )
            )

    return MemoryListResponse(files=files)


@router.get("/{path:path}", response_model=MemoryFileDetailResponse)
async def get_memory_file(
    agent_id: str,
    path: str,
    memory_repo: MemoryRepository = Depends(get_memory_repo),
):
    """Get a specific memory file with content.

    Args:
        agent_id: Agent ID
        path: File path (e.g., "knowledge/preferences.md")
    """
    file_data = await memory_repo.get(agent_id, path)
    if not file_data:
        raise HTTPException(status_code=404, detail=f"Memory file not found: {path}")

    return MemoryFileDetailResponse(
        path=file_data["path"],
        content=file_data["content"],
        content_type=file_data.get("content_type", "text/markdown"),
        updated_at=file_data["updated_at"].isoformat(),
    )


@router.delete("/{path:path}", status_code=204)
async def delete_memory_file(
    agent_id: str,
    path: str,
    memory_repo: MemoryRepository = Depends(get_memory_repo),
):
    """Delete a memory file.

    Args:
        agent_id: Agent ID
        path: File path to delete
    """
    deleted = await memory_repo.delete_file(agent_id, path)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory file not found: {path}")

    return None
