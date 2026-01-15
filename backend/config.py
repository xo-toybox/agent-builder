from pydantic_settings import BaseSettings


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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
