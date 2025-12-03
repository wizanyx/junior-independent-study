import logging
from typing import TYPE_CHECKING, cast

from flask import Flask, jsonify, request
from flask_cors import CORS

from .config import Settings, get_settings
from .preprocess import Pipeline, default_pipeline
from .sentiment_service import FinBertService, MockSentimentService, SentimentService

log = logging.getLogger("app")


if TYPE_CHECKING:
    from flask import Response


def create_app(settings: Settings | None = None) -> Flask:
    if settings is None:
        settings = get_settings()

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    CORS(app, resources={r"/*": {"origins": settings.cors_allowed_origins}})

    # Initialize preprocessing pipeline and sentiment service
    pl = default_pipeline(max_text_length=settings.max_text_length)
    app.config["PREPROCESS_PIPELINE"] = pl

    # Select and initialize sentiment service
    service: SentimentService | None = None
    if settings.use_mock_model:
        service = MockSentimentService()
        log.info(
            "Using MockSentimentService (USE_MOCK_MODEL=%s)", settings.use_mock_model
        )
    else:
        # Prefer a pipeline-friendly device index if the settings expose one.
        device_arg = settings.pipeline_device_index()

        try:
            service = FinBertService(
                model_name=settings.model_name,
                device=device_arg,
            )
            log.info(
                "FinBertService initialized (model=%s device=%s)",
                settings.model_name,
                device_arg,
            )
        except Exception as e:  # pragma: no cover - integration/runtime errors
            log.exception("Failed to initialize FinBertService: %s", e)
            service = None

    # Warm-up (best-effort)
    try:
        if service is not None:
            service.warmup()
    except Exception as e:  # pragma: no cover
        log.warning("Model warmup failed: %s", e)

    app.config["SENTIMENT_SERVICE"] = service

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "env": settings.flask_env,
            "enabled_sources": settings.enabled_sources,
            "default_window_hours": settings.default_window_hours,
            "model_name": settings.model_name,
            "use_mock_model": settings.use_mock_model,
            "model_loaded": service is not None,
        }

    @app.post("/sentiment")
    def sentiment() -> tuple["Response", int]:
        """Batch sentiment inference endpoint.

        Body: JSON array of objects compatible with Document.from_dict fields
        (minimally requires "source" and "text"). Returns an array of results
        with label and per-class probability scores.
        """
        svc: SentimentService | None = app.config.get("SENTIMENT_SERVICE")
        if svc is None:
            return jsonify({"error": "sentiment service is not available"}), 503

        pl: Pipeline = cast(Pipeline, app.config.get("PREPROCESS_PIPELINE"))
        try:
            payload = request.get_json(force=True, silent=False)
        except Exception:
            return jsonify({"error": "Invalid JSON"}), 400

        if not isinstance(payload, list):
            return jsonify({"error": "Expected a JSON array"}), 400

        try:
            docs = pl.process_many(payload)
        except Exception as e:
            log.exception("Preprocessing error: %s", e)
            return jsonify({"error": f"Preprocessing error: {e}"}), 400

        if not docs:
            return jsonify([]), 200

        texts = [d.text for d in docs]
        # prefer model_batch_size from settings if present
        default_batch = int(settings.model_batch_size)
        batch_size = (
            int(request.json.get("batch_size", default_batch))
            if isinstance(request.json, dict)
            else default_batch
        )

        try:
            outputs = svc.predict([str(t) for t in texts], batch_size=batch_size)
        except Exception as e:  # pragma: no cover - model-level errors
            log.exception("Inference failed: %s", e)
            return jsonify({"error": "Inference failed"}), 500

        # Shape the response alongside original ids when present
        results: list[dict] = []
        for d, out in zip(docs, outputs):
            results.append(
                {
                    "id": getattr(d, "id", None),
                    "label": out.label,
                    "scores": out.scores,
                }
            )

        return jsonify(results), 200

    return app
