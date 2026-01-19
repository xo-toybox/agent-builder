"""Agent Builder - Main FastAPI application.

v0.0.3 - Generic agent builder platform with chat-based creation,
MCP tools, HITL approval, memory, skills, and persistent checkpoints.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.infrastructure.persistence.sqlite.database import init_db
from backend.infrastructure.persistence.sqlite.checkpointer import (
    set_checkpointer,
    clear_checkpointer,
)
from backend.api.v1 import router as api_v1_router
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Agent Builder v0.0.3...")

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

    # Initialize persistent checkpointer (v0.0.3)
    checkpoint_path = data_dir / "checkpoints.db"
    async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
        set_checkpointer(checkpointer)
        logger.info(f"Checkpointer initialized: {checkpoint_path}")

        yield

        # Cleanup
        clear_checkpointer()
    logger.info("Agent Builder stopped")


app = FastAPI(
    title="Agent Builder",
    version="0.0.3",
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
