"""
Configuration module for CSV Chat Agent.
Loads from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # App metadata
    APP_NAME: str = "CSV Chat Agent API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Paths (not from env)
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    RAW_DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "raw")
    PROCESSED_DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "processed")
    VECTOR_STORE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "vector_store")
    LOGS_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")

    # CORS (not from env)
    CORS_ORIGINS: list = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
        ]
    )

    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 60

    # Model configuration (not from env)
    INTENT_MODEL: str = "mistral:7b"
    CHAT_MODEL: str = "llama3.1:8b"
    CHART_MODEL: str = "qwen2.5:7b"
    SUMMARY_MODEL: str = "llama3.1:8b"

    # Embeddings (HuggingFace)
    EMBEDDINGS_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector Store (ChromaDB)
    VECTOR_STORE_TYPE: str = "chroma"
    CHROMA_PERSIST_DIR: str = Field(default_factory=lambda: str(Path(__file__).parent.parent.parent / "data" / "vector_store" / "chroma_db"))

    # RAG Configuration
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 5

    # File upload (not from env)
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_EXTENSIONS: list = Field(default=[".csv", ".xlsx", ".xls"])

    # Conversation (not from env)
    MAX_CONVERSATION_TURNS: int = 20
    CONVERSATION_MEMORY_TYPE: str = "buffer"  # buffer | persistent

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | standard

    def ensure_dirs(self):
        """Create necessary directories if they don't exist."""
        for dir_path in [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.VECTOR_STORE_DIR,
            self.LOGS_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
settings.ensure_dirs()
