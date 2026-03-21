from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LinkedInCredentials(BaseSettings):
    """Minimal settings for LinkedIn-only commands (no Gemini key required)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    linkedin_email: str
    linkedin_password: str
    dry_run: bool = False


class AppConfig(BaseSettings):
    """Application configuration loaded from environment and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str
    linkedin_email: str
    linkedin_password: str
    chroma_persist_dir: str = "./data/chroma"
    post_calendar_path: str = "./data/post_calendar.csv"
    schedule_hour: int = Field(default=12, ge=0, le=23)
    schedule_minute: int = Field(default=15, ge=0, le=59)
    timezone: str = "Europe/Madrid"
    dry_run: bool = False
