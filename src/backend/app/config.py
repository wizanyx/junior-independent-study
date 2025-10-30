from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load .env once at process start (no-op in prod if you use real env vars)
load_dotenv()

log = logging.getLogger("config")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def _split_csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip().lower() for x in s.split(",") if x.strip()]


@dataclass
class Settings:
    # Flask
    flask_env: str = os.getenv("FLASK_ENV", "development")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_allowed_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
        )
    )

    # Feature toggles
    requested_sources: list[str] = field(
        default_factory=lambda: _split_csv(os.getenv("ENABLE_SOURCES", "news,reddit"))
    )

    # Limits
    default_window_hours: int = int(os.getenv("DEFAULT_WINDOW_HOURS", "24"))
    max_upload_rows: int = int(os.getenv("MAX_UPLOAD_ROWS", "10000"))
    max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", "5000"))

    # External keys
    news_api_key: str | None = os.getenv("NEWS_API_KEY") or None
    reddit_client_id: str | None = os.getenv("REDDIT_CLIENT_ID") or None
    reddit_client_secret: str | None = os.getenv("REDDIT_CLIENT_SECRET") or None
    reddit_user_agent: str | None = os.getenv("REDDIT_USER_AGENT") or None

    # Derived
    enabled_sources: list[str] = field(default_factory=list)

    def compute_enabled_sources(self) -> None:
        enabled = []

        if "news" in self.requested_sources:
            if self.news_api_key:
                enabled.append("news")
            else:
                log.warning(
                    "NEWS source requested but NEWS_API_KEY is missing. "
                    "Disabling 'news'."
                )

        if "reddit" in self.requested_sources:
            if (
                self.reddit_client_id
                and self.reddit_client_secret
                and self.reddit_user_agent
            ):
                enabled.append("reddit")
            else:
                log.warning(
                    "REDDIT source requested but credentials are missing. "
                    "Disabling 'reddit'."
                )

        # You can add more (stocktwits, twitter, etc.) with the same pattern.
        self.enabled_sources = enabled


def get_settings() -> Settings:
    s = Settings()
    s.compute_enabled_sources()
    # Summary log
    log.info(
        "Config loaded | env=%s | port=%s | sources=%s | window=%sh",
        s.flask_env,
        s.api_port,
        ",".join(s.enabled_sources) or "(none)",
        s.default_window_hours,
    )
    return s
