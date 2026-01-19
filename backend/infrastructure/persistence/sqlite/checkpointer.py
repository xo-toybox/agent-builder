"""LangGraph persistent checkpointer for conversation state.

Uses AsyncSqliteSaver for SQLite-backed persistence.
Checkpointer is managed via FastAPI lifespan context manager.
"""

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Global reference set by lifespan handler
_checkpointer: AsyncSqliteSaver | None = None


def set_checkpointer(checkpointer: AsyncSqliteSaver) -> None:
    """Set the global checkpointer (called from lifespan)."""
    global _checkpointer
    _checkpointer = checkpointer


def get_checkpointer() -> AsyncSqliteSaver:
    """Get the checkpointer instance.

    Returns:
        The AsyncSqliteSaver instance set during app startup.

    Raises:
        RuntimeError: If called before lifespan initialization.
    """
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. App lifespan not started.")
    return _checkpointer


def clear_checkpointer() -> None:
    """Clear the global checkpointer (called from lifespan cleanup)."""
    global _checkpointer
    _checkpointer = None
