"""
Configuration settings for the FastAPI backend
"""
import os
from typing import List

from dotenv import load_dotenv

# Simplified: load a .env from the current working directory if present.
# Note: scripts/dev.sh already sources repo root .env before starting the backend.
try:
    load_dotenv(override=False)
except Exception:
    # Don't fail if dotenv isn't available in some environments
    pass


class Settings:
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Tauri Next.js FastAPI Backend"
    VERSION: str = "1.0.0"

    # Server Configuration
    HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    RELOAD: bool = os.getenv("BACKEND_RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("BACKEND_LOG_LEVEL", "info")

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "tauri://localhost",
        # Tauri dev server
        "http://localhost:1420",
    ]

    # Add custom origins from environment
    if os.getenv("CORS_ORIGINS"):
        CORS_ORIGINS.extend(os.getenv("CORS_ORIGINS", "").split(","))

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./codeverse.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"

    # Security Configuration (for future use)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # STT / Transcription
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_STT_MODEL: str = os.getenv("OPENAI_STT_MODEL", "gpt-4o-transcribe")
    TRANSCRIBE_TIMEOUT_SECONDS: int = int(os.getenv("TRANSCRIBE_TIMEOUT_SECONDS", "20"))
    STT_TIMEOUT_SECONDS: int = int(os.getenv("STT_TIMEOUT_SECONDS", "15"))
    MAX_AUDIO_BYTES: int = int(os.getenv("MAX_AUDIO_BYTES", str(10 * 1024 * 1024)))
    MAX_AUDIO_SECONDS: int = int(os.getenv("MAX_AUDIO_SECONDS", "60"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
