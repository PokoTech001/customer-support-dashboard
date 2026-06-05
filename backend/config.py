from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    tts_email: str
    tts_password: str
    tts_base_url: str = "https://api-smartflo.tatateleservices.com"
    gemini_api_key: str
    frontend_origins: str = "http://localhost:3000,http://localhost:5173"
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
