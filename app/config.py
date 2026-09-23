from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    royale_api_key: str = ""
    royale_api_base: str = "https://proxy.royaleapi.dev/v1"
    gemini_api_key: Optional[str] = None
    llm_primary_model: str = "gemini-3.1-flash-lite"
    llm_fallback_model: str = ""
    groq_api_key: Optional[str] = None
    groq_fallback_model: str = ""
    database_url: str = "sqlite:///./data/royal_advice.db"
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "royal-advice/0.1"
    # Comma-separated list of allowed frontend origins in production. Ignored
    # while debug=True, where all origins are allowed for local dev.
    cors_origins: str = "http://localhost:5173"
    debug: bool = False
    verify_ssl: bool = True

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_allow_origins(self) -> List[str]:
        if self.debug:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
