from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Mongo
    mongo_uri: str
    mongo_db: str = "dental_chatbot"

    # ChromaDB
    chroma_db_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

    # LLM keys
    google_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
