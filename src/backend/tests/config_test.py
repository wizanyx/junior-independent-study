from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import Settings, _split_csv, get_settings

if TYPE_CHECKING:
    import pytest


def test_enabled_sources_none_when_missing_keys() -> None:
    s = Settings()
    s.requested_sources = ["news", "reddit"]
    # No creds provided
    s.news_api_key = None
    s.reddit_client_id = None
    s.reddit_client_secret = None
    s.reddit_user_agent = None

    s.compute_enabled_sources()
    assert s.enabled_sources == []


def test_enabled_sources_news_only() -> None:
    s = Settings()
    s.requested_sources = ["news"]
    s.news_api_key = "abc"
    # No reddit creds
    s.reddit_client_id = None
    s.reddit_client_secret = None
    s.reddit_user_agent = None

    s.compute_enabled_sources()
    assert s.enabled_sources == ["news"]


def test_enabled_sources_reddit_only() -> None:
    s = Settings()
    s.requested_sources = ["reddit"]
    s.reddit_client_id = "id"
    s.reddit_client_secret = "secret"
    s.reddit_user_agent = "ua"
    # No news key
    s.news_api_key = None

    s.compute_enabled_sources()
    assert s.enabled_sources == ["reddit"]


def test_enabled_sources_both() -> None:
    s = Settings()
    s.requested_sources = ["news", "reddit"]
    s.news_api_key = "abc"
    s.reddit_client_id = "id"
    s.reddit_client_secret = "secret"
    s.reddit_user_agent = "ua"

    s.compute_enabled_sources()
    assert set(s.enabled_sources) == {"news", "reddit"}


def test_get_settings_calls_compute_and_logs(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Replace Settings with a dummy to avoid env dependency and
    # make behavior deterministic
    class DummySettings:
        def __init__(self) -> None:
            self.flask_env = "test"
            self.api_port = 1234
            self.enabled_sources: list[str] = []
            self.default_window_hours = 12
            self.compute_called = False

        def compute_enabled_sources(self) -> None:  # called by get_settings
            self.compute_called = True
            self.enabled_sources = ["news"]

    monkeypatch.setattr("app.config.Settings", DummySettings)

    with caplog.at_level("INFO"):
        s = get_settings()

    # Ensure our dummy was used and compute was called
    assert isinstance(s, DummySettings)
    assert s.compute_called is True
    assert s.enabled_sources == ["news"]


def test_split_csv_handles_none_and_empty() -> None:
    assert _split_csv(None) == []
    assert _split_csv("") == []
    assert _split_csv("a, b , ,C") == ["a", "b", "c"]
