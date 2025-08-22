from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "MQTT2Yandex Bridge"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str

    # MQTT
    MQTT_BROKER: str = "mosquitto"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""

    # Yandex
    YANDEX_CLIENT_ID: str = ""
    YANDEX_CLIENT_SECRET: str = ""
    YANDEX_REDIRECT_URI: str = ""

    # YAPI
    YAPI_URL: str = "http://yapi:8080"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "admin"

    # Encryption
    ENCRYPTION_KEY: str

    class Config:
        case_sensitive = True
        env_file = ".env"

# Lazy initialization to avoid import errors during testing
try:
    settings = Settings()
except Exception:
    # Fallback for testing
    import os
    os.environ.setdefault('SECRET_KEY', 'test-secret-key')
    os.environ.setdefault('ENCRYPTION_KEY', 'test-encryption-key')
    os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')
    settings = Settings()
