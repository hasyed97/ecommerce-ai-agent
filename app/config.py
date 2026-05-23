"""Environment and application settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["openai", "gemini"]

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: LLMProvider = Field(
        default="openai",
        validation_alias=AliasChoices("LLM_PROVIDER", "llm_provider"),
    )

    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY"),
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("OPENAI_MODEL"),
    )

    google_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        validation_alias=AliasChoices("GEMINI_MODEL", "GOOGLE_MODEL"),
    )

    langfuse_public_key: str = Field(
        default="",
        validation_alias=AliasChoices("LANGFUSE_PUBLIC_KEY"),
    )
    langfuse_secret_key: str = Field(
        default="",
        validation_alias=AliasChoices("LANGFUSE_SECRET_KEY"),
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_BASE_URL"),
    )

    return_window_days: int = Field(
        default=30,
        validation_alias=AliasChoices("RETURN_WINDOW_DAYS"),
    )
    max_injection_score: float = Field(
        default=0.5,
        validation_alias=AliasChoices("MAX_INJECTION_SCORE"),
    )

    products_path: Path = DATA_DIR / "products.json"
    orders_path: Path = DATA_DIR / "orders.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
