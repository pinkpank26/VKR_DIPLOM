from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_SECRET_KEY: str
    APP_JWT_ISSUER: str = "mailer_app"
    APP_JWT_EXPIRE_MIN: int = 120

    DB_URL: str
    DB_SCHEMA: str = "mailing"

    REDIS_URL: str | None = None

    SMTP_HOST: str
    SMTP_PORT: int = 465
    SMTP_USE_SSL: bool = True
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_NAME: str = "Mailer"
    SMTP_FROM_EMAIL: str

    RATE_LIMIT_PER_MINUTE: int = 30
    MAX_RETRY: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()