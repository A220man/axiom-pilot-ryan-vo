"""Application configuration via pydantic-settings."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "axiom-pilot-ryan-vo"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # Security
    secret_key: str = Field(default="", description="Must be set in production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Session/Cookie
    session_cookie_name: str = "session"
    session_cookie_secure: bool = False
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"
    csrf_cookie_name: str = "csrf_token"

    # OIDC / Keycloak
    oidc_enabled: bool = True
    oidc_issuer_url: str = "http://127.0.0.1:8080/realms/axiom-pilot"
    oidc_client_id: str = "axiom-pilot"
    oidc_client_secret: str = Field(default="", description="Must be set in production")
    oidc_redirect_uri: str = "http://127.0.0.1:8000/auth/callback"
    oidc_scopes: list[str] = ["openid", "profile", "email", "roles"]
    oidc_logout_uri: str = "http://127.0.0.1:8080/realms/axiom-pilot/protocol/openid-connect/logout"

    # Frontend URL (for CORS and redirects)
    frontend_url: str = "http://127.0.0.1:5173"

    # LLM (optional)
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    llm_timeout_seconds: int = 30

    # Demo mode (localhost only)
    demo_mode: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_production(self) -> None:
        """Validate required settings for production."""
        if self.is_production:
            if not self.secret_key:
                raise ValueError("SECRET_KEY must be set in production")
            if not self.oidc_client_secret:
                raise ValueError("OIDC_CLIENT_SECRET must be set in production")
            if self.demo_mode:
                raise ValueError("Demo mode cannot be enabled in production")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()