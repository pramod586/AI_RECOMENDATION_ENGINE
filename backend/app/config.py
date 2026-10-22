import os
from pathlib import Path

from dotenv import load_dotenv


# ==================================================
# Environment Configuration
# ==================================================

# Project backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# .env file location
ENV_FILE = BASE_DIR / ".env"

# Load environment variables from backend/.env
load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


class Settings:

    # ==================================================
    # Application
    # ==================================================

    APP_NAME = os.getenv(
        "APP_NAME",
        "AI Knowledge Assistant API",
    )

    APP_VERSION = os.getenv(
        "APP_VERSION",
        "1.0.0",
    )

    ENVIRONMENT = os.getenv(
        "ENVIRONMENT",
        "development",
    )

    # ==================================================
    # Database
    # ==================================================

    DATABASE_URL = os.getenv(
        "DATABASE_URL"
    )

    # ==================================================
    # Gemini AI
    # ==================================================

    GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY"
    )

    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "gemini-embedding-001",
    )

    # ==================================================
    # JWT Authentication
    # ==================================================

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY"
    )

    JWT_ALGORITHM = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    JWT_EXPIRE_MINUTES = int(
        os.getenv(
            "JWT_EXPIRE_MINUTES",
            "60",
        )
    )

    # ==================================================
    # CORS
    # ==================================================

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:8080",
        ).split(",")
        if origin.strip()
    ]


# ==================================================
# Global Settings Instance
# ==================================================

settings = Settings()
