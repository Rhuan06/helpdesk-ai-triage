from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HelpDesk AI Triage"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./helpdesk.db"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()