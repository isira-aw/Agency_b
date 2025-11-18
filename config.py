from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DATABASE_URL: str
    SECRET_KEY: str
    USER_DATA_PATH: str = "./user_data"
    
    class Config:
        env_file = ".env"

settings = Settings()
