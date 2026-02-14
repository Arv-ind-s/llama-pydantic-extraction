"""
Application settings for the extraction pipeline.

Loads configuration from environment variables and .env file.
Uses pydantic-settings for type-safe config management.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


# Project root is two levels up from this file (config/settings.py → project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Central configuration — all values can be overridden via environment variables."""

    # LlamaParse API
    llama_cloud_api_key: str = Field(
        ...,  # required, no default
        description="LlamaCloud API key for LlamaParse access"
    )

    # Processing
    batch_size: int = Field(
        default=5,
        description="Number of PDFs to process in each batch"
    )
    max_retries: int = Field(
        default=3,
        description="Max retry attempts for failed API calls"
    )
    timeout: int = Field(
        default=300,
        description="Request timeout in seconds"
    )

    # Paths (relative to project root)
    input_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "input",
        description="Directory containing source PDF files"
    )
    output_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "output",
        description="Directory for validated JSON output"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    model_config = {
        "env_file": PROJECT_ROOT / ".env",  # auto-load .env from project root
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # ignore unknown env vars
    }


# Singleton instance — import this throughout the project
settings = Settings()
