from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

log = logging.getLogger("sentiment")

# canonical label order used across the app
LABELS = ("positive", "neutral", "negative")


@dataclass(frozen=True)
class SentimentOutput:
    """Model output for a single input text."""

    label: str
    scores: dict[str, float]


class SentimentService(Protocol):
    def warmup(self) -> None:  # optional no-op for mocks
        ...

    def predict(
        self, texts: list[str], batch_size: int = 16
    ) -> list[SentimentOutput]: ...


class MockSentimentService:
    """Deterministic lightweight mock for tests and local dev without model.

    Produces a fixed distribution with small variations based on text hash to
    prove batching works.
    """

    def warmup(self) -> None:
        log.info("MockSentimentService warmup completed")

    def predict(self, texts: list[str], batch_size: int = 16) -> list[SentimentOutput]:
        out: list[SentimentOutput] = []
        for t in texts:
            h = (hash(t) % 1000) / 1000.0
            # pseudo variation across inputs but stable per text
            pos = 0.33 + (h - 0.5) * 0.02
            neg = 0.33 - (h - 0.5) * 0.01
            neu = max(0.0, 1.0 - pos - neg)
            scores = {
                "positive": float(pos),
                "negative": float(neg),
                "neutral": float(neu),
            }
            label = max(scores, key=lambda k: scores[k])
            out.append(SentimentOutput(label=label, scores=scores))
        return out


class FinBertService:
    """FinBERT-backed inference using Hugging Face transformers pipeline.

    Lazy-imports transformers so importing this module doesn't force heavy
    dependencies in test environments that use the Mock service.
    """

    def __init__(
        self,
        model_name: str = "yiyanghkust/finbert-tone",
        device: int | str | None = None,
    ) -> None:
        """
        device: -1 or 'cpu' for CPU, 0..N or 'cuda:0' for GPU, 'auto' to detect.
        Internally converted to the pipeline 'device' int: -1 => CPU, >=0 => GPU index.
        """
        self.model_name = model_name
        self._device_arg = device
        self._device_index = self._normalize_device(device)
        # Lazy import to avoid hard dependency for tests that use MockSentimentService
        try:
            import transformers  # type: ignore  # noqa: F401
        except Exception as exc:  # pragma: no cover - exercised in integration
            log.error("transformers import failed: %s", exc)
            raise

        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            pipeline,
        )

        log.info(
            "Loading FinBERT model '%s' on device=%s...", model_name, self._device_index
        )
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
        # Build id2label mapping from model config if available
        raw_id2label = getattr(self._model.config, "id2label", None)
        if raw_id2label:
            try:
                self._id2label: dict[int, str] = {
                    int(k): str(v).strip().lower() for k, v in raw_id2label.items()
                }
            except Exception:
                self._id2label = {}
        else:
            self._id2label = {}

        # Create pipeline; set return_all_scores so we get full distributions
        # device: -1 -> CPU; >=0 -> GPU index
        self._pipeline = pipeline(
            task="text-classification",
            model=self._model,
            tokenizer=self._tokenizer,
            return_all_scores=True,
            truncation=True,
            top_k=None,
            device=self._device_index,
        )
        log.info("FinBERT pipeline ready (model=%s)", model_name)

    def _normalize_device(self, device: int | str | None) -> int:
        """Return pipeline device int (-1 CPU, >=0 GPU)."""
        if isinstance(device, int):
            return device
        d = (device or "").strip().lower()
        if d in ("", "auto"):
            try:
                import torch  # type: ignore

                return (
                    0
                    if getattr(torch, "cuda", None) and torch.cuda.is_available()
                    else -1
                )
            except Exception:
                return -1
        if d in ("cpu", "-1"):
            return -1
        if d.startswith("cuda"):
            parts = d.split(":")
            try:
                return int(parts[1]) if len(parts) > 1 else 0
            except Exception:
                return 0
        try:
            return int(d)
        except Exception:
            return -1

    def warmup(self) -> None:
        try:
            _ = self.predict(["warmup text for finbert"], batch_size=1)
            log.info("FinBertService warmup completed")
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("FinBertService warmup failed: %s", exc)

    def _map_label(self, raw_label: str) -> str:
        """Normalize raw label from pipeline/model into canonical LABELS."""
        label = (raw_label or "").strip().lower()
        if not label:
            return "neutral"
        # common shapes: "LABEL_0", "LABEL_1", "positive", "pos", "+", "NEGATIVE"
        if label.startswith("label_"):
            try:
                idx = int(label.split("_", 1)[1])
                if self._id2label and idx in self._id2label:
                    mapped = self._id2label[idx]
                    if mapped in LABELS:
                        return mapped
                    return mapped  # will be normalized below
                # fallback mapping by index if id2label unavailable: try best-effort
                # Many finetuned FinBERTs use order [positive, negative, neutral] or
                # [positive, neutral, negative].
                # We'll fall back to a conservative mapping:
                # label_0->positive, label_1->negative, label_2->neutral
                fallback = {0: "positive", 1: "negative", 2: "neutral"}
                return fallback.get(idx, "neutral")
            except Exception:
                return "neutral"
        if label in {"pos", "+"}:
            return "positive"
        if label in {"neg", "-"}:
            return "negative"
        # if label already matches canonical
        if label in LABELS:
            return label
        # if model returned something else (e.g., "positive_score"),
        # try to find canonical token
        for canonical in LABELS:
            if canonical in label:
                return canonical
        return "neutral"

    def predict(self, texts: list[str], batch_size: int = 16) -> list[SentimentOutput]:
        if not texts:
            return []
        raw: list[list[dict[str, Any]]] = self._pipeline(texts, batch_size=batch_size)  # type: ignore
        outputs: list[SentimentOutput] = []
        for scores_list in raw:
            # scores_list is a list of dicts: {"label": "...", "score": 0.123}
            scores_map: dict[str, float] = {}
            for item in scores_list:
                raw_label = str(item.get("label", "")).strip()
                score = float(item.get("score", 0.0))
                label = self._map_label(raw_label)
                # accumulate in case pipeline returns duplicate normalized labels
                scores_map[label] = scores_map.get(label, 0.0) + score
            # ensure all canonical labels present
            for lab in LABELS:
                scores_map.setdefault(lab, 0.0)
            # Normalize to sum to 1.0 (defensive)
            total = sum(scores_map.values()) or 1.0
            for k in list(scores_map.keys()):
                scores_map[k] = float(scores_map[k] / total)
            pred_label = max(scores_map, key=lambda k: scores_map[k])
            outputs.append(SentimentOutput(label=pred_label, scores=scores_map))
        return outputs
