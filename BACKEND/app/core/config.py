from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    CHAT_MODEL: str = "llama3.1"
    EMBED_MODEL: str = "nomic-embed-text"
    CHROMA_PATH: str = "./chroma_store"
    UPLOAD_PATH: str = "./uploads"

    class Config:
        env_file = ".env"


settings = Settings()
