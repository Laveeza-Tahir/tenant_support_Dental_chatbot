from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional
import os

class Settings(BaseSettings):
    # MongoDB connection
    mongo_uri: str
    mongo_db: str = "saas_chatbot_platform"
    
    # Vector DB settings
    chroma_persist_directory: str = "data/chroma_db"
    embeddings_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Legacy support for FAISS
    faiss_index_path: str = "data/faiss_index"
    
    # API keys for LLMs
    google_api_key: str
    openai_api_key: Optional[str] = None
    
    # JWT Authentication
    secret_key: str = "YOUR_SECRET_KEY_HERE"  # Change in production
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day
    
    # File upload settings
    max_upload_size: int = 5 * 1024 * 1024  # 5 MB
    
    # Applied per tenant
    tenant_defaults: Dict[str, Any] = {
        "allowed_file_types": ["pdf", "docx", "txt"],
        "max_files_per_tenant": 50,
        "max_embedding_tokens": 500000,  # Limit on tokens to embed per tenant
    }

    class Config:
        env_file = ".env"

settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.chroma_persist_directory, exist_ok=True)
os.makedirs(settings.faiss_index_path, exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)
