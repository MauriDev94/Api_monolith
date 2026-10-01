import pytest

from app.main import AppSettings


def test_app_settings_accepts_default_origins_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dev mode keeps the localhost default and does not require CORS_ALLOWED_ORIGINS."""
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    settings = AppSettings()

    assert settings.cors_allowed_origins == ["http://localhost:3000"]
    assert settings.cors_allow_credentials is True


def test_app_settings_accepts_empty_origins_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dev defaults still pass when the caller explicitly disables CORS."""
    monkeypatch.delenv("APP_ENV", raising=False)

    settings = AppSettings(cors_allowed_origins=[])

    assert settings.cors_allowed_origins == []


def test_app_settings_fails_fast_in_production_when_origins_are_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production MUST fail-fast when CORS_ALLOWED_ORIGINS is empty — silent breakage otherwise."""
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS must be set in production"):
        AppSettings(cors_allowed_origins=[])


def test_app_settings_accepts_configured_origins_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production passes when the operator set the Vercel origin."""
    monkeypatch.setenv("APP_ENV", "production")

    settings = AppSettings(cors_allowed_origins=["https://monolith-frontend.vercel.app"])

    assert settings.cors_allowed_origins == ["https://monolith-frontend.vercel.app"]


def test_app_settings_accepts_multiple_origins_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production can whitelist multiple origins (e.g. Vercel preview + production)."""
    monkeypatch.setenv("APP_ENV", "production")

    settings = AppSettings(
        cors_allowed_origins=[
            "https://monolith-frontend.vercel.app",
            "https://monolith-frontend-git-main.vercel.app",
        ]
    )

    assert settings.cors_allowed_origins == [
        "https://monolith-frontend.vercel.app",
        "https://monolith-frontend-git-main.vercel.app",
    ]
