"""SQLite implementation of CredentialStore with encryption."""

import json
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.infrastructure.persistence.sqlite.models import CredentialModel

logger = logging.getLogger(__name__)


class SQLiteCredentialStore:
    """SQLite implementation of the CredentialStore port.

    Credentials are encrypted using Fernet symmetric encryption
    before being stored in the database.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        # Initialize Fernet cipher if encryption key is set
        if settings.encryption_key:
            self._fernet = Fernet(settings.encryption_key.encode())
        else:
            self._fernet = None
            logger.warning(
                "ENCRYPTION_KEY not set - credentials will be stored unencrypted. "
                "This is insecure and should only be used in development."
            )

    def _encrypt(self, data: dict) -> str:
        """Encrypt credential data."""
        json_data = json.dumps(data)
        if self._fernet:
            return self._fernet.encrypt(json_data.encode()).decode()
        # Fallback to plain text if no encryption key (development only)
        return json_data

    def _decrypt(self, encrypted_data: str) -> dict:
        """Decrypt credential data."""
        if self._fernet:
            decrypted = self._fernet.decrypt(encrypted_data.encode()).decode()
            return json.loads(decrypted)
        # Fallback to plain text parsing if no encryption key
        return json.loads(encrypted_data)

    async def save(self, provider: str, credentials: dict) -> None:
        """Save credentials for a provider (encrypted)."""
        encrypted = self._encrypt(credentials)

        existing = await self.session.get(CredentialModel, provider)

        if existing:
            existing.encrypted_data = encrypted
            existing.updated_at = datetime.utcnow()
        else:
            model = CredentialModel(
                provider=provider,
                encrypted_data=encrypted,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.session.add(model)

        await self.session.commit()

    async def get(self, provider: str) -> dict | None:
        """Get credentials for a provider."""
        model = await self.session.get(CredentialModel, provider)

        if not model:
            return None

        return self._decrypt(model.encrypted_data)

    async def delete(self, provider: str) -> None:
        """Delete credentials for a provider."""
        model = await self.session.get(CredentialModel, provider)
        if model:
            await self.session.delete(model)
            await self.session.commit()
