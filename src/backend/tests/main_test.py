from __future__ import annotations

from typing import TYPE_CHECKING

from app.__main__ import main as main_entry
from app.config import Settings

if TYPE_CHECKING:
    import pytest


class _DummyApp:
    def __init__(self) -> None:
        self.called: dict[str, object] = {}

    def run(self, port: int, debug: bool) -> None:
        # pragma: no cover - behavior asserted via side effects
        self.called["port"] = port
        self.called["debug"] = debug


def test_main_invokes_run_with_expected_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy = _DummyApp()

    s = Settings()
    s.api_port = 1234
    s.flask_env = "development"  # ensures debug=True branch

    # Patch get_settings to return our controlled settings
    monkeypatch.setattr("app.__main__.get_settings", lambda: s)
    # Patch create_app to return our dummy app
    monkeypatch.setattr("app.__main__.create_app", lambda _s: dummy)

    # Call entrypoint
    main_entry()

    assert dummy.called.get("port") == 1234
    assert dummy.called.get("debug") is True
