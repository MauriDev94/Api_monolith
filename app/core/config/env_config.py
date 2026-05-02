from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvConfig(BaseSettings):
    """Application settings loaded from environment variables."""

    db_user: str
    db_password: str
    db_name: str
    db_port: int
    db_host: str
    jwt_secret_key: str
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender_email: str | None = None
    smtp_use_tls: bool = True
    resend_api_key: str | None = None
    resend_sender_email: str | None = None
    internal_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
