"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_AUDIO_MODEL: str = os.getenv("OPENAI_AUDIO_MODEL", "gpt-4o-audio-preview")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/medcases")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


settings = Settings()
