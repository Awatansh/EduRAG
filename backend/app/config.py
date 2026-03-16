"""
KB Agent — FastAPI Configuration
Centralized settings via pydantic-settings, loaded from .env
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── PostgreSQL ──────────────────────────────────────────────
    POSTGRES_USER: str = "kbagent"
    POSTGRES_PASSWORD: str = "kbagent_dev"
    POSTGRES_DB: str = "kbagent"
    DATABASE_URL: str = "postgresql+asyncpg://kbagent:kbagent_dev@localhost:5432/kbagent"

    # ── Qdrant ──────────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "kb_agent_chunks"

    # ── Redis ───────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    # ── LLM ──────────────────────────────────────────────────────
    LLM_PROVIDER: str = "groq"  # groq | gemini | openai | ollama
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_LLM_MODEL: str = "gemini-2.5-flash"
    OPENAI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # ── Embeddings ───────────────────────────────────────────────
    EMBEDDING_PROVIDER: str = "gemini"  # gemini | huggingface_local | openai
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # ── Storage ──────────────────────────────────────────────────
    LOCAL_STORAGE_PATH: str = "./storage/users"


settings = Settings()
