from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvConfig(BaseSettings):
    """Application settings loaded from environment variables."""

    # Opcionales: en producción (Render) la conexión se arma desde DATABASE_URL; los
    # db_* solo se usan como fallback para desarrollo local. Hacerlos obligatorios
    # rompía un deploy que solo inyecta DATABASE_URL (EnvConfig fallaba antes de que
    # Database pudiera leer DATABASE_URL).
    db_user: str | None = None
    db_password: str | None = None
    db_name: str | None = None
    db_port: int | None = None
    db_host: str | None = None
    jwt_secret_key: str
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender_email: str | None = None
    smtp_use_tls: bool = True
    resend_api_key: str | None = None
    resend_sender_email: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
