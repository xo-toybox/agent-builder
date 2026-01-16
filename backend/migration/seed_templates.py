"""Seed templates into the database.

Run this on startup to ensure templates are available.
"""

import logging
from backend.infrastructure.persistence.sqlite.database import AsyncSessionLocal
from backend.infrastructure.persistence.sqlite.agent_repo import SQLiteAgentRepository
from backend.infrastructure.templates.email_assistant import EMAIL_ASSISTANT_TEMPLATE

logger = logging.getLogger(__name__)


async def seed_templates():
    """Seed default templates into the database.

    Only creates templates that don't already exist.
    """
    async with AsyncSessionLocal() as session:
        repo = SQLiteAgentRepository(session)

        # Check if email assistant template exists
        existing = await repo.get(EMAIL_ASSISTANT_TEMPLATE.id)

        if not existing:
            logger.info("Seeding Email Assistant template...")
            await repo.save(EMAIL_ASSISTANT_TEMPLATE)
            logger.info("Email Assistant template created")
        else:
            logger.info("Email Assistant template already exists")
