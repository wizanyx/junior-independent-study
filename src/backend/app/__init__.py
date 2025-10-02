from flask import Flask
from flask_cors import CORS

from .config import Settings, get_settings


def create_app(settings: Settings | None = None) -> Flask:
    if settings is None:
        settings = get_settings()

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    CORS(app, resources={r"/*": {"origins": settings.cors_allowed_origins}})

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "env": settings.flask_env,
            "enabled_sources": settings.enabled_sources,
            "default_window_hours": settings.default_window_hours,
        }

    return app
