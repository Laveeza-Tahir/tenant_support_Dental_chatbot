from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Mongo
    mongo_uri: str
    mongo_db: str = "dental_chatbot"

    # FAISS
    faiss_index_path: str = "data/faiss_index"

    # LLM keys
    google_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
