import os
from pathlib import Path
from typing import Any, List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ROOT_DIR = _BACKEND_DIR.parent
_ENV_FILES = [
    str(_ROOT_DIR / ".env"),
    str(_BACKEND_DIR / ".env"),
    ".env",
    "../.env",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Metadata
    PROJECT_NAME: str = "MetaRadar"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"

    # Database & Redis
    # Local-dev defaults only. Override via .env for any shared or deployed environment.
    DATABASE_URL: str = "postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar"
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> Any:
        if isinstance(v, str):
            import urllib.parse
            v_stripped = v.strip()
            prefix = ""
            for p in ("postgres://", "postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://", "postgresql+asyncpg://"):
                if v_stripped.startswith(p):
                    prefix = p
                    break

            if prefix:
                rest = v_stripped[len(prefix):]
                if "@" in rest:
                    creds, _, host_part = rest.rpartition("@")
                    if ":" in creds:
                        user, _, password = creds.partition(":")
                        encoded_pass = urllib.parse.quote(urllib.parse.unquote(password), safe="")
                        return f"postgresql+asyncpg://{user}:{encoded_pass}@{host_part}"
                return "postgresql+asyncpg://" + rest
        return v

    # Security & CORS
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-change-in-production"
    SESSION_LIFETIME_SECONDS: int = 28800      # 8 hours absolute
    SESSION_IDLE_TIMEOUT_SECONDS: int = 3600   # 1 hour idle
    SESSION_COOKIE_SECURE: bool = False       # True in HTTPS production
    SESSION_COOKIE_SAMESITE: Optional[str] = None  # None | "lax" | "strict" | "none" (defaults to "none" in prod, "lax" in dev)
    DEMO_MODE: bool = True                    # Enables /auth/demo-login
    DEMO_AUTO_SEED_USERS: bool = True
    DEMO_USER_PASSWORD: Optional[str] = None
    DEMO_PASSWORD_MEDICAL_AFFAIRS: str = "MedAffairs2026!"
    DEMO_PASSWORD_REGULATORY: str = "Regulatory2026!"
    DEMO_PASSWORD_SAFETY: str = "Safety2026!"
    DEMO_PASSWORD_MARKET_ACCESS: str = "Access2026!"
    DEMO_PASSWORD_COMMUNICATIONS: str = "Comms2026!"
    DEMO_PASSWORD_LEADERSHIP: str = "Leader2026!"
    DEMO_PASSWORD_ADMIN: str = "Admin2026!"
    DEMO_PASSWORD_DEVELOPER: str = "Dev2026!"
    AUTH_RATE_LIMIT_PER_MINUTE: int = 5
    CORS_ORIGINS: str = "http://localhost:3000"
    METARADAR_API_KEY: Optional[str] = None
    MUTATION_RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod")

    @property
    def effective_session_cookie_samesite(self) -> str:
        if self.SESSION_COOKIE_SAMESITE:
            val = self.SESSION_COOKIE_SAMESITE.lower().strip()
            if val in ("lax", "strict", "none"):
                return val
        return "none" if self.is_production else "lax"

    @property
    def effective_session_cookie_secure(self) -> bool:
        if self.SESSION_COOKIE_SECURE:
            return True
        if self.effective_session_cookie_samesite == "none":
            return True
        return self.is_production

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


    # LLM Provider & Hardware Settings
    LLM_PROVIDER: str = "local"  # local | xai | auto
    LOCAL_LLM_MODEL: str = "google/gemma-3-4b-it"
    LLM_DEVICE: str = "auto"
    LLM_DTYPE: str = "int4"
    MAX_CONTEXT_TOKENS: int = 2048
    MAX_OUTPUT_TOKENS: int = 512

    # Cloud AI Provider Settings (Gemini free tier)
    AI_PROVIDER: str = "auto"  # auto | local | gemini | off
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT_S: float = 60.0
    GEMINI_MAX_RETRIES: int = 3

    # Hosted Fallback Settings (Grok / xAI)
    ENABLE_GROK_FALLBACK: bool = False
    XAI_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None

    @property
    def effective_xai_api_key(self) -> Optional[str]:
        return self.XAI_API_KEY or self.GROK_API_KEY

    # Local Models Directory & GGUF Configuration
    MODELS_DIR: str = str(_ROOT_DIR / "models")
    LOCAL_GGUF_MODEL: Optional[str] = None
    LOCAL_GGUF_PATH: Optional[str] = None

    # Ollama Sidecar
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:4b"   # matches LOCAL_LLM_MODEL name in Ollama registry

    # Embedding Model Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL_REVISION: str = "e4bb823e5956b6277b069d276b978c48a73507c7"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_MAX_SEQ_LENGTH: int = 256

    # Retention
    RAW_SIGNAL_RETENTION_DAYS: int = 30

    # NewsAPI Key (supports NEWSAPI_KEY or NEWS_API_KEY)
    NEWSAPI_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None

    @property
    def effective_newsapi_key(self) -> Optional[str]:
        return self.NEWSAPI_KEY or self.NEWS_API_KEY

    # NCBI PubMed API Key & Identifiers
    NCBI_API_KEY: Optional[str] = None
    NCBI_TOOL: str = "MetaRadar"
    NCBI_EMAIL: str = "metaradar@example.com"

    # OpenFDA API Key (optional for higher rate limits)
    OPENFDA_API_KEY: Optional[str] = None

    # Autonomous Background Scheduler Settings
    ENABLE_BACKGROUND_SCHEDULER: bool = True
    SCHEDULER_CT_INTERVAL_MINUTES: int = 60
    SCHEDULER_PUBMED_INTERVAL_MINUTES: int = 60
    SCHEDULER_EMA_INTERVAL_MINUTES: int = 30
    SCHEDULER_FDA_INTERVAL_MINUTES: int = 30
    SCHEDULER_NEWS_INTERVAL_MINUTES: int = 15
    SCHEDULER_BIOPHARMA_DIVE_INTERVAL_MINUTES: int = 30
    SCHEDULER_FIERCE_PHARMA_INTERVAL_MINUTES: int = 30
    SCHEDULER_ET_PHARMA_INTERVAL_MINUTES: int = 30
    SCHEDULER_JITTER_PERCENT: int = 10
    SCHEDULER_MAX_BACKOFF_MINUTES: int = 120
    SCHEDULER_FAILURE_THRESHOLD: int = 3
    SCHEDULER_STALE_MULTIPLIER: float = 2.5


settings = Settings()


def validate_production_settings() -> None:
    """
    Verifies that the application is not running in production with insecure defaults.
    Raises RuntimeError if production is misconfigured.
    """
    if settings.is_production:
        if settings.SECRET_KEY in ("dev-secret-change-in-production", ""):
            raise RuntimeError("FATAL: Cannot run in production with default SECRET_KEY.")
        if settings.DEMO_MODE:
            raise RuntimeError("FATAL: DEMO_MODE must be False in production.")
        if any("*" in origin for origin in settings.cors_origins_list):
            raise RuntimeError("FATAL: Wildcard CORS origin is forbidden in production.")


def configuration_error_for(source_id: str) -> Optional[str]:
    """Pure, side-effect-free evaluator for connector and model configuration state."""
    src = source_id.lower().strip()
    if src == "newsapi":
        key = (settings.NEWSAPI_KEY or settings.NEWS_API_KEY or "").strip()
        if not key or key.lower() in ("your_newsapi_key_here", "placeholder", "xxx", "none"):
            return "CONFIGURATION_ERROR: NEWSAPI_KEY missing (required) — get a key at https://newsapi.org/register (NewsAPI developer account) and set NEWSAPI_KEY in .env"
    if src in ("grok", "xai") and settings.ENABLE_GROK_FALLBACK:
        key = (settings.effective_xai_api_key or "").strip()
        if not key or key.lower() in ("your_xai_api_key_here", "placeholder", "xxx", "none"):
            return "CONFIGURATION_ERROR: XAI_API_KEY missing (required when ENABLE_GROK_FALLBACK=true) — get a key from https://console.x.ai and set XAI_API_KEY in .env"
    return None


