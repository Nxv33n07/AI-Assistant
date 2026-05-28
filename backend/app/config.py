from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str
    allowed_origins: str = "*"
    bible_api_base: str = "https://bible-api.com"
    pollinations_base: str = "https://image.pollinations.ai"
    chroma_persist_dir: str = "./data/chroma_db"
    verses_file: str = "./data/key_verses.json"
    gemini_model: str = "gemma-4-31b-it"
    max_history_turns: int = 10

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
