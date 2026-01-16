from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Anthropic
    anthropic_api_key: str = ""

    # Agent
    polling_interval_seconds: int = 30

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Database (v0.0.2)
    database_path: Path = Path("data/agent_builder.db")
    debug: bool = False

    # Encryption key for credentials (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    encryption_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
