from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="env.local", env_file_encoding="utf-8", extra="ignore")

    # App
    backend_port: int = 8000
    web_url: str = "http://localhost:5173"
    base_url: str = "https://y2m.badkiko.ru"

    # DB
    database_url: str = "postgres://y2m:y2m@localhost:5432/y2m"

    # MQTT
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883

    # OAuth Yandex (для авторизации через Яндекс)
    ya_client_id: str | None = None
    ya_client_secret: str | None = None
    ya_redirect_uri: str = "https://y2m.badkiko.ru/api/auth/yandex/callback"
    
    # Яндекс.Умный дом навык (Client Identifier и Password для навыка)
    yandex_skill_client_id: str | None = None
    yandex_skill_client_secret: str | None = None

    # Crypto
    y2m_enc_key: str | None = None


settings = Settings()


