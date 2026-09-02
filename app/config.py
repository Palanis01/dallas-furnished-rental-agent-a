from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dallas Furnished Rental - Agent A"
    app_version: str = "1.2.0"
    environment: str = "development"
    database_url: str = "sqlite:///./agent_a.db"
    agent_api_key: str = "change-me"

    # OpenAI public API. No Microsoft Entra ID is required.
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"

    default_max_queries: int = Field(default=5, ge=1, le=20)
    property_monthly_rent: int = 3200
    property_min_stay_days: int = 30
    property_furnished_finder_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
