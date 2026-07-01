"""
PIA — Centralized Configuration
Loads from .env, provides typed access to all settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- API Keys ---
    google_api_key: str = Field(default="", description="Google Gemini API key")

    # --- ChromaDB ---
    chroma_persist_dir: str = Field(default="./chroma_data")

    # --- MongoDB ---
    use_mongodb: bool = Field(default=False)
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="pia_db")

    # --- JSON Store (fallback) ---
    json_store_dir: str = Field(default="./json_data")

    # --- Models ---
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    llm_model: str = Field(default="gemini-2.5-flash")
    llm_temperature: float = Field(default=0.2)

    # --- Retrieval ---
    dense_weight: float = Field(default=0.5)
    bm25_weight: float = Field(default=0.5)
    retrieval_top_k: int = Field(default=20)
    rerank_top_k: int = Field(default=5)

    # --- Chunking (doc-type-aware) ---
    chunk_size_interview: int = Field(default=512)
    chunk_overlap_interview: int = Field(default=64)
    chunk_size_jd: int = Field(default=768)
    chunk_overlap_jd: int = Field(default=128)
    chunk_size_aptitude: int = Field(default=1024)
    chunk_overlap_aptitude: int = Field(default=128)

    # --- Server ---
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    frontend_url: str = Field(default="http://localhost:5173")

    # --- Data ---
    data_dir: str = Field(default="./data")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_chunk_config(self, doc_type: str) -> dict:
        """Return chunk_size and chunk_overlap for a given doc type."""
        configs = {
            "interview_experience": {
                "chunk_size": self.chunk_size_interview,
                "chunk_overlap": self.chunk_overlap_interview,
            },
            "job_description": {
                "chunk_size": self.chunk_size_jd,
                "chunk_overlap": self.chunk_overlap_jd,
            },
            "aptitude_material": {
                "chunk_size": self.chunk_size_aptitude,
                "chunk_overlap": self.chunk_overlap_aptitude,
            },
        }
        return configs.get(doc_type, {
            "chunk_size": self.chunk_size_interview,
            "chunk_overlap": self.chunk_overlap_interview,
        })

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)

    @property
    def json_store_path(self) -> Path:
        return Path(self.json_store_dir)

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)


# Singleton settings instance
settings = Settings()
