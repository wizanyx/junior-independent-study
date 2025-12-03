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


def _to_bool(val: str | None, default: bool = False) -> bool:
    """Parse common truthy/falsey strings from env vars.

    Accepts: 1/0, true/false, yes/no, on/off (case-insensitive). Falls back to default.
    """
    if val is None:
        return default
    v = val.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


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

    # Model / Inference
    # Default to using a lightweight mock for local development/tests.
    # Set USE_MOCK_MODEL=0/false to enable real model loading.
    use_mock_model: bool = _to_bool(os.getenv("USE_MOCK_MODEL"), True)
    # Default FinBERT-like model — configurable via MODEL_NAME env var.
    model_name: str = os.getenv("MODEL_NAME", "yiyanghkust/finbert-tone")
    # Accept "cpu", "auto", "cuda:0", numeric index "0", or "-1" for CPU.
    # "auto" will pick GPU if available (requires torch).
    model_device: str = os.getenv("MODEL_DEVICE", "cpu")
    model_batch_size: int = int(os.getenv("MODEL_BATCH_SIZE", "16"))

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

    def pipeline_device_index(self) -> int:
        """Return an int device index suitable for transformers.pipeline:
        -1 => CPU, 0..N => CUDA device index.

        Accepts model_device values:
          - 'cpu' or '-1' => -1
          - 'auto' => 0 if torch.cuda.is_available() else -1
          - 'cuda' or 'cuda:0' or 'cuda:1' => numeric index
          - '0' or '1' => numeric index (interpreted as GPU index)
        """
        val = (self.model_device or "").strip().lower()
        if val in ("", "auto"):
            # 'auto' behavior: try to use GPU if available
            try:
                import torch  # type: ignore
            except Exception:
                return -1
            return (
                0 if getattr(torch, "cuda", None) and torch.cuda.is_available() else -1
            )
        if val in ("cpu", "-1"):
            return -1
        if val.startswith("cuda"):
            parts = val.split(":")
            try:
                return int(parts[1]) if len(parts) > 1 else 0
            except Exception:
                return 0
        # numeric string
        try:
            return int(val)
        except Exception:
            return -1


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
    log.info(
        "Model config | use_mock=%s | name=%s | device=%s "
        "(pipeline_index=%s) | batch=%s",
        s.use_mock_model,
        s.model_name,
        s.model_device,
        s.pipeline_device_index(),
        s.model_batch_size,
    )
    return s
