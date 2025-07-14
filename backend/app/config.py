import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str
    
    # Vector Store Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384
    TOP_K_RETRIEVAL: int = 5
    
    # Text Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Data Paths
    LEGAL_DOCS_PATH: str = "data/legal_docs"
    PROCESSED_CHUNKS_PATH: str = "data/processed_chunks.json"
    VECTOR_INDEX_PATH: str = "data/vector_cache/faiss_index"
    
    # Model Configuration
    GEMINI_MODEL: str = "gemini-1.5-pro"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 2048
    
    # Cache Settings
    ENABLE_REDIS_CACHE: bool = False
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()