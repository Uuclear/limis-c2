from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://limis:limis123@localhost:5434/limis"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "limis-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    APP_NAME: str = "LIMIS"
    DEBUG: bool = True
    UPLOAD_DIR: str = "./uploads"
    TEMPLATE_DIR: str = "./templates"

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
