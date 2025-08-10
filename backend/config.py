"""
Configuration settings for the FastAPI backend
"""
import os
from typing import List


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
        "http://localhost:1420",  # Tauri dev server
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

    # Claude CLI Configuration
    # Set CLAUDE_CLI_PATH environment variable to specify custom Claude CLI location
    # If not set, the system will try common locations:
    # - ~/.claude/local (official Claude CLI)
    # - /usr/local/bin (system-wide installs)
    # - ~/node_modules/.bin (npm local installs)


settings = Settings()
