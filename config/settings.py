from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "dev-key"

    GIGACHAT_AUTH_KEY: str | None = None
    GIGACHAT_CLIENT_ID: str | None = None

    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    SMTP_SERVER: str | None = None
    EMAIL_ADDRESS: str | None = None
    EMAIL_PASSWORD: str | None = None

    model_config = {
        "env_file": ".env"
    }


settings = Settings()