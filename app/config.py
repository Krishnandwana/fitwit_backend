from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Gemini API
    GEMINI_API_KEY: str

    # OpenFoodFacts
    OPENFOODFACTS_API_URL: str = "https://world.openfoodfacts.org/api/v2"

    # App Settings
    APP_NAME: str = "FitWit"
    DEBUG: bool = True

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        case_sensitive = True


settings = Settings()
