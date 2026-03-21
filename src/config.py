from datetime import date
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LinkedInCredentials(BaseSettings):
    """Minimal settings for LinkedIn-only commands (no Gemini key required)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    linkedin_email: str = ""
    linkedin_password: str = ""
    linkedin_access_token: str
    linkedin_member_sub: str = ""  # OpenID `sub` from id_token if userinfo API is denied
    dry_run: bool = False

    @field_validator("linkedin_access_token", mode="before")
    @classmethod
    def _strip_access_token(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("linkedin_member_sub", mode="before")
    @classmethod
    def _strip_member_sub(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class AppConfig(BaseSettings):
    """Application configuration loaded from environment and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str
    linkedin_email: str = ""
    linkedin_password: str = ""
    linkedin_access_token: str
    linkedin_member_sub: str = ""

    @field_validator("linkedin_access_token", mode="before")
    @classmethod
    def _strip_access_token(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("linkedin_member_sub", mode="before")
    @classmethod
    def _strip_member_sub(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    chroma_persist_dir: str = "./data/chroma"
    post_calendar_path: str = "./data/post_calendar.csv"
    schedule_hour: int = Field(default=12, ge=0, le=23)
    schedule_minute: int = Field(default=15, ge=0, le=59)
    timezone: str = "Europe/Madrid"
    dry_run: bool = False
    # If set: row = (days since this date in TIMEZONE) mod N + 1 (day 1 = start date; N = CSV rows).
    # If unset: row = (day-of-year - 1) mod N + 1 (does not count workflow runs).
    calendar_sequence_start: Optional[date] = None

    @field_validator("calendar_sequence_start", mode="before")
    @classmethod
    def _empty_calendar_sequence_start(cls, v: object) -> object:
        if v is None or v == "":
            return None
        return v
