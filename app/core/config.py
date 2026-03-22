from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"

    dense_top_k: int = 20
    sparse_top_k: int = 20
    reranker_top_k: int = 6

    prompts_path: str = "./config/prompts.json"
    raw_data_path: str = "./data/raw"

    chunk_size: int = 500
    chunk_overlap: int = 50

    api_base_url: str = "https://rag-droit-production.up.railway.app"
    allowed_origins: str = "*"  # ← dans la classe

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