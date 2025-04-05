"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the compliance review pipeline.

    All values can be overridden via environment variables. The NVIDIA API key
    is required when using the NIM provider but not for mock mode.
    """

    nvidia_api_key: str = ""
    nvidia_api_base: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.1-70b-instruct"

    default_framework: str = "dsa"
    llm_temperature: float = 0.1
    llm_max_retries: int = 3
    parse_max_retries: int = 2

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
