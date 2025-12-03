from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytest import LogCaptureFixture, MonkeyPatch

from app import create_app
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
    monkeypatch: MonkeyPatch,
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


def test_sentiment_service_not_available_returns_503(
    monkeypatch: MonkeyPatch,
) -> None:
    s = Settings()
    s.use_mock_model = False

    # Force FinBertService construction to raise so create_app sets service=None
    def bad_init(*a: Any, **kw: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr("app.FinBertService", bad_init)

    app = create_app(s)
    client = app.test_client()

    rv = client.post("/sentiment", data="[]", content_type="application/json")
    assert rv.status_code == 503
    assert rv.get_json() == {"error": "sentiment service is not available"}


def test_sentiment_invalid_json_returns_400() -> None:
    s = Settings()
    s.use_mock_model = True
    app = create_app(s)
    client = app.test_client()

    rv = client.post("/sentiment", data="not json", content_type="application/json")
    assert rv.status_code == 400
    assert rv.get_json() == {"error": "Invalid JSON"}


def test_sentiment_payload_not_array_returns_400() -> None:
    s = Settings()
    s.use_mock_model = True
    app = create_app(s)
    client = app.test_client()

    rv = client.post(
        "/sentiment", data=json.dumps({"foo": "bar"}), content_type="application/json"
    )
    assert rv.status_code == 400
    assert rv.get_json() == {"error": "Expected a JSON array"}


def test_sentiment_preprocessing_error_returns_400(
    monkeypatch: MonkeyPatch,
) -> None:
    s = Settings()
    s.use_mock_model = True
    app = create_app(s)
    client = app.test_client()

    # Make the pipeline raise when processing
    def fail_process_many(_payloads: list[dict[str, Any]]) -> list[Any]:
        raise RuntimeError("preproc fail")

    monkeypatch.setattr(
        app.config["PREPROCESS_PIPELINE"], "process_many", fail_process_many
    )

    rv = client.post(
        "/sentiment",
        data=json.dumps([{"source": "news", "text": "hi"}]),
        content_type="application/json",
    )
    assert rv.status_code == 400
    data = rv.get_json()
    assert isinstance(data, dict) and data.get("error", "").startswith(
        "Preprocessing error"
    )


def test_sentiment_empty_docs_returns_empty_list(
    monkeypatch: MonkeyPatch,
) -> None:
    s = Settings()
    s.use_mock_model = True
    app = create_app(s)
    client = app.test_client()

    # Make pipeline return empty list
    monkeypatch.setattr(
        app.config["PREPROCESS_PIPELINE"], "process_many", lambda payloads: []
    )

    rv = client.post(
        "/sentiment",
        data=json.dumps([{"source": "news", "text": "will be dropped"}]),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json() == []


def test_sentiment_success_with_mock_service(monkeypatch: MonkeyPatch) -> None:
    s = Settings()
    s.use_mock_model = True
    app = create_app(s)
    client = app.test_client()

    payload = [{"source": "news", "text": "Good news for markets"}]
    rv = client.post(
        "/sentiment", data=json.dumps(payload), content_type="application/json"
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list) and len(data) == 1
    item = data[0]
    assert "id" in item and "label" in item and "scores" in item


def test_sentiment_inference_failure_returns_500(
    monkeypatch: MonkeyPatch,
) -> None:
    s = Settings()
    s.use_mock_model = True
    app = create_app(s)
    client = app.test_client()

    # Replace service.predict to raise
    svc = app.config.get("SENTIMENT_SERVICE")

    def bad_predict(
        _texts: list[dict[str, Any]] | list[Any],
        batch_size: int = 16,
    ) -> list[Any]:
        raise RuntimeError("inference boom")

    monkeypatch.setattr(svc, "predict", bad_predict)

    rv = client.post(
        "/sentiment",
        data=json.dumps([{"source": "news", "text": "x"}]),
        content_type="application/json",
    )
    assert rv.status_code == 500
    assert rv.get_json() == {"error": "Inference failed"}


def test_create_app_logs_finbert_initialized(
    monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
) -> None:
    s = Settings()
    s.use_mock_model = False

    class FakeFinBert:
        def __init__(self, model_name: str, device: int | str | None = None) -> None:
            self.model_name = model_name
            self.device = device

        def warmup(self) -> None:
            return None

    monkeypatch.setattr("app.FinBertService", FakeFinBert)

    with caplog.at_level("INFO"):
        _ = create_app(s)

    # check that the log.info line for initialization was executed
    assert any("FinBertService initialized" in r.getMessage() for r in caplog.records)
