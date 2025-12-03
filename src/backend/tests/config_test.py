from __future__ import annotations

from typing import TYPE_CHECKING, Mapping, Sequence

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
            # attributes accessed by get_settings logging
            self.use_mock_model = True
            self.model_name = "dummy-model"
            self.model_device = "cpu"
            self.model_batch_size = 16

        def pipeline_device_index(self) -> int:
            return -1

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


def test_to_bool_variants() -> None:
    from app.config import _to_bool

    # truthy
    for v in ("1", "true", "yes", "y", "on", "TRUE"):
        assert _to_bool(v, default=False) is True

    # falsey
    for v in ("0", "false", "no", "n", "off", "FALSE"):
        assert _to_bool(v, default=True) is False


def test_pipeline_device_index_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Settings()

    # cpu and -1
    s.model_device = "cpu"
    assert s.pipeline_device_index() == -1
    s.model_device = "-1"
    assert s.pipeline_device_index() == -1

    # cuda variants
    s.model_device = "cuda"
    assert s.pipeline_device_index() == 0
    s.model_device = "cuda:1"
    assert s.pipeline_device_index() == 1

    # numeric string
    s.model_device = "0"
    assert s.pipeline_device_index() == 0

    # auto when torch unavailable -> -1
    s.model_device = "auto"
    monkeypatch.setitem(__import__("sys").modules, "torch", None)
    # remove torch to simulate ImportError path
    try:
        if "torch" in __import__("sys").modules:
            del __import__("sys").modules["torch"]
        assert s.pipeline_device_index() == -1
    finally:
        __import__("sys").modules.pop("torch", None)


def test_to_bool_none_and_unknown() -> None:
    from app.config import _to_bool

    assert _to_bool(None, default=True) is True
    assert _to_bool("unknown", default=True) is True
    assert _to_bool("unknown", default=False) is False


def test_pipeline_device_index_error_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Settings()
    s.model_device = "cuda:bad"
    assert s.pipeline_device_index() == 0

    s.model_device = "not_a_number"
    assert s.pipeline_device_index() == -1

    # auto when torch available and cuda available
    fake_torch = type(
        "t", (), {"cuda": type("c", (), {"is_available": staticmethod(lambda: True)})}
    )()
    monkeypatch.setitem(__import__("sys").modules, "torch", fake_torch)
    try:
        s.model_device = "auto"
        assert s.pipeline_device_index() == 0
    finally:
        __import__("sys").modules.pop("torch", None)


def test_pipeline_device_index_import_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate import raising for 'torch' to hit except: branch returning -1
    import builtins

    orig_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == "torch":
            raise ImportError("no torch")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        s = Settings()
        s.model_device = "auto"
        assert s.pipeline_device_index() == -1
    finally:
        monkeypatch.setattr(builtins, "__import__", orig_import)
