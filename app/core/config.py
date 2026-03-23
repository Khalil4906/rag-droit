from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    google_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "models/gemini-embedding-001"

    dense_top_k: int = 20
    sparse_top_k: int = 20
    reranker_top_k: int = 6

    prompts_path: str = "./config/prompts.json"
    raw_data_path: str = "./data/raw"

    chunk_size: int = 500
    chunk_overlap: int = 50
    
    auth_username: str
    auth_password_hash: str
    jwt_secret: str
    jwt_expire_hours: int = 24

    api_base_url: str = "http://localhost:8000"
    allowed_origins: str = "*"  

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def get_asyncpg_url(self) -> str:
        return self.database_url.replace("postgres://", "postgresql://")

    def get_allowed_origins(self) -> list[str]:  # ← dans la classe
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()