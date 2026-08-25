from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    royale_api_key: str = ""
    royale_api_base: str = "https://proxy.royaleapi.dev/v1"
    openrouter_api_key: Optional[str] = None
    openrouter_primary_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    openrouter_fallback_model: str = "google/gemma-4-26b-a4b-it:free"
    database_url: str = "sqlite:///./data/royal_advice.db"
    debug: bool = False
    verify_ssl: bool = True

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
