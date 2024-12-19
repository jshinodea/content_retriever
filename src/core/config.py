"""
Configuration Settings Module

This module manages application configuration and environment variables.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """Application settings and environment variables."""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API Keys
    TAVILY_API_KEY: str
    HF_ACCESS_TOKEN: str
    
    # Database settings
    CASSANDRA_HOSTS: list[str] = ["localhost"]
    CASSANDRA_KEYSPACE: str = "content_retriever"
    CASSANDRA_PORT: int = 9042
    CASSANDRA_USERNAME: Optional[str] = None
    CASSANDRA_PASSWORD: Optional[str] = None
    
    # LLM settings
    TEXT_MODEL_ID: str = "meta-llama/Llama-2-70b-chat-hf"
    VISION_MODEL_ID: str = "meta-llama/Llama-2-13b-chat-hf"
    
    # Web scraping settings
    DEFAULT_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Content settings
    MAX_CONTENT_LENGTH: int = 1000000  # 1MB
    SUPPORTED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

# Create settings instance
settings = Settings() 