from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmProvider(StrEnum):
    MOCK = "mock"
    OPENAI = "openai"


class Settings(BaseSettings):
    app_name: str = "cloudops-rag-eval"
    app_env: str = "local"
    log_level: str = "INFO"
    llm_provider: LlmProvider = LlmProvider.MOCK
    openai_api_key: SecretStr | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    docs_path: Path = Path("docs/corpus")
    chroma_path: Path = Path(".chroma")
    retrieval_top_k: int = Field(default=4, ge=1, le=8)
    min_relevance_score: float = Field(default=0.25, ge=0.0, le=1.0)
    max_question_chars: int = Field(default=1000, ge=16, le=4000)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
