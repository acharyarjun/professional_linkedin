from pydantic_settings import BaseSettings
from pydantic import Field


class AppConfig(BaseSettings):
    gemini_api_key: str = Field(..., env='GEMINI_API_KEY')
    linkedin_email: str = Field(..., env='LINKEDIN_EMAIL')
    linkedin_password: str = Field(..., env='LINKEDIN_PASSWORD')
    chroma_persist_dir: str = Field(default='./data/chroma', env='CHROMA_PERSIST_DIR')
    post_calendar_path: str = Field(default='./data/post_calendar.csv', env='POST_CALENDAR_PATH')
    schedule_hour: int = Field(default=12, env='SCHEDULE_HOUR')
    schedule_minute: int = Field(default=15, env='SCHEDULE_MINUTE')
    timezone: str = Field(default='Europe/Madrid', env='TIMEZONE')
    dry_run: bool = Field(default=False, env='DRY_RUN')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
