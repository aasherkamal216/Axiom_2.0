import os
from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict

_ = load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )
    """
    Configuration settings for the Axiom 2.0 Agent.
    """
    GOOGLE_API_KEY: str
    DEFAULT_MODEL: str = "gemini-2.0-flash"
    BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    AVAILABLE_MODELS: list[str] = [
        "gemini-2.0-flash", 
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash-thinking-exp-1219",
        "gemini-2.5-pro-exp-03-25",
        "gemini-2.5-flash-preview-04-17",
    ]
    
    MAX_DOCS_TOKEN_LIMIT: int = 20000  # Maximum tokens to retrieve from the documentations

settings = Settings()
