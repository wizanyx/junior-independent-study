from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app import create_app

if TYPE_CHECKING:
    import pytest
from app.config import Settings


def test_health_returns_expected_json() -> None:
    s = Settings()
    s.flask_env = "test"
    s.enabled_sources = ["news"]
    s.default_window_hours = 12
    s.cors_allowed_origins = ["http://example.com"]

    app = create_app(s)
    client = app.test_client()

    rv = client.get("/health")
    assert rv.status_code == 200
    data: dict[str, Any] = rv.get_json()  # type: ignore[assignment]
    assert data["status"] == "ok"
    assert data["env"] == "test"
    assert data["enabled_sources"] == ["news"]
    assert data["default_window_hours"] == 12


def test_cors_allows_configured_origin() -> None:
    s = Settings()
    s.cors_allowed_origins = ["http://allowed.com"]
    app = create_app(s)
    client = app.test_client()

    rv = client.get("/health", headers={"Origin": "http://allowed.com"})
    assert rv.status_code == 200
    # Flask-CORS should reflect the Origin when it matches
    assert rv.headers.get("Access-Control-Allow-Origin") == "http://allowed.com"

    # A disallowed origin should not be reflected
    rv2 = client.get("/health", headers={"Origin": "http://blocked.com"})
    assert rv2.headers.get("Access-Control-Allow-Origin") is None


def test_create_app_uses_get_settings_when_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Prepare a deterministic settings instance
    s = Settings()
    s.flask_env = "ci"
    s.enabled_sources = ["news"]
    s.default_window_hours = 6
    s.cors_allowed_origins = ["http://test"]

    # Ensure create_app(None) uses our settings by patching get_settings
    # get_settings is re-exported in app/__init__.py, so patch app.get_settings
    monkeypatch.setattr("app.get_settings", lambda: s)

    app = create_app()  # no arg path
    client = app.test_client()

    rv = client.get("/health")
    assert rv.status_code == 200
    data: dict[str, Any] = rv.get_json()  # type: ignore[assignment]
    assert data["env"] == "ci"
    assert data["enabled_sources"] == ["news"]
    assert data["default_window_hours"] == 6
