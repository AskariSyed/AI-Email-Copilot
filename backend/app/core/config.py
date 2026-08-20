
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Email Copilot"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = (
        "postgresql://copilot:copilot_password@localhost:5432/email_copilot"
    )

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/auth/google/callback"

    # AI APIs
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str | None = None
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Reranking Options
    ENABLE_RERANKING: bool = True
    RERANK_CANDIDATE_COUNT: int = 20
    RERANK_FINAL_COUNT: int = 5

    # Security
    SECRET_KEY: str = "super_secret_temporary_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Observability
    LOG_LEVEL: str = "INFO"
    VERBOSE_DIAGNOSTICS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


settings = Settings()
