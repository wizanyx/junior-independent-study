from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Mapping, Sequence

import pytest

if TYPE_CHECKING:
    from pytest import LogCaptureFixture, MonkeyPatch

from app.sentiment_service import (
    LABELS,
    FinBertService,
    MockSentimentService,
    SentimentOutput,
)


def test_finbert_init_and_predict_with_fake_transformers(
    monkeypatch: MonkeyPatch,
) -> None:
    # Create a fake transformers module to allow FinBertService.__init__ to run
    class FakeConfig:
        id2label = {"0": "positive", "1": "negative", "2": "neutral"}

    class FakeModel:
        def __init__(self) -> None:
            self.config = FakeConfig()

    class AutoModelForSequenceClassification:
        @staticmethod
        def from_pretrained(name: str) -> FakeModel:
            return FakeModel()

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(name: str) -> object:
            return object()

    def fake_pipeline(*args: Any, **kwargs: Any) -> object:
        # return a callable that when invoked with texts returns per-text score lists
        def _call(
            texts: list[str],
            batch_size: int | None = None,
        ) -> list[list[dict[str, str | float]]]:
            return [
                [
                    {"label": "LABEL_0", "score": 0.6},
                    {"label": "LABEL_1", "score": 0.4},
                ]
                for _ in texts
            ]

        return _call

    fake_transformers = type("mod", (), {})()
    setattr(
        fake_transformers,
        "AutoModelForSequenceClassification",
        AutoModelForSequenceClassification,
    )
    setattr(fake_transformers, "AutoTokenizer", AutoTokenizer)
    setattr(fake_transformers, "pipeline", fake_pipeline)

    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    svc = FinBertService(model_name="fake-model", device="cpu")
    outs = svc.predict(["a", "b"], batch_size=1)
    assert len(outs) == 2
    for out in outs:
        assert out.label in LABELS
        assert pytest.approx(1.0, rel=1e-6) == _scores_sum(out.scores)


def test_finbert_predict_accumulates_duplicate_labels() -> None:
    svc = FinBertService.__new__(FinBertService)

    # pipeline returns duplicate labels (different raw forms mapping to same canonical)
    def dup_pipeline(
        texts: list[str],
        batch_size: int | None = None,
    ) -> list[list[dict[str, str | float]]]:
        return [
            [
                {"label": "positive", "score": 0.5},
                {"label": "pos", "score": 0.5},
            ]
            for _ in texts
        ]

    svc._pipeline = dup_pipeline  # type: ignore
    svc._id2label = {}
    outs = svc.predict(["x"])
    assert len(outs) == 1
    out = outs[0]
    assert out.label == "positive"
    assert pytest.approx(1.0, rel=1e-9) == _scores_sum(out.scores)


def test_finbert_predict_empty_texts_returns_empty_list() -> None:
    svc = FinBertService.__new__(FinBertService)
    # should return early without accessing _pipeline
    assert svc.predict([]) == []


def _scores_sum(scores: dict[str, float]) -> float:
    return sum(float(v) for v in scores.values())


def test_mock_sentiment_predict_basic() -> None:
    svc = MockSentimentService()
    texts = ["Stocks rally on upbeat earnings", "Company misses revenue estimates"]
    outs = svc.predict(texts, batch_size=2)
    assert isinstance(outs, list)
    assert len(outs) == len(texts)
    for out in outs:
        assert isinstance(out, SentimentOutput)
        assert out.label in LABELS
        assert set(out.scores.keys()) == set(LABELS)
        # distribution should be normalized to ~1.0
        assert pytest.approx(1.0, rel=1e-3) == _scores_sum(out.scores)


def test_mock_sentiment_is_deterministic_for_same_texts() -> None:
    svc = MockSentimentService()
    texts = ["same text", "same text"]
    a = svc.predict(texts)
    b = svc.predict(texts)
    # same inputs should give same outputs (deterministic mock)
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert x.label == y.label
        # compare scores keys and values
        assert set(x.scores.keys()) == set(y.scores.keys())
        for k in x.scores:
            assert pytest.approx(x.scores[k], rel=1e-9) == y.scores[k]


def test_finbert_map_label_various_forms() -> None:
    # create instance without running __init__ (avoid heavy imports)
    svc = FinBertService.__new__(FinBertService)
    # set id2label mapping to a known mapping
    svc._id2label = {0: "positive", 1: "negative", 2: "neutral"}

    assert svc._map_label("LABEL_0") == "positive"
    assert svc._map_label("label_1") == "negative"
    assert svc._map_label("pos") == "positive"
    assert svc._map_label("+") == "positive"
    assert svc._map_label("NEGATIVE") == "negative"
    assert svc._map_label("") == "neutral"
    # contains canonical token
    assert svc._map_label("some_positive_score") == "positive"

    # when id2label is empty, fallback mapping by index should work
    svc._id2label = {}
    assert svc._map_label("LABEL_2") == "neutral"


def test_normalize_device_variants() -> None:
    svc = FinBertService.__new__(FinBertService)

    # integer device passes through
    assert svc._normalize_device(2) == 2

    # cpu and -1 map to -1
    assert svc._normalize_device("cpu") == -1
    assert svc._normalize_device("-1") == -1

    # cuda shorthand and explicit index
    assert svc._normalize_device("cuda") == 0
    assert svc._normalize_device("cuda:1") == 1

    # numeric string
    assert svc._normalize_device("0") == 0

    # auto behavior: simulate torch with cuda unavailable
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    sys.modules["torch"] = fake_torch  # type: ignore
    try:
        assert svc._normalize_device("auto") == -1
    finally:
        del sys.modules["torch"]


def test_normalize_device_auto_when_cuda_available() -> None:
    svc = FinBertService.__new__(FinBertService)
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True))
    sys.modules["torch"] = fake_torch  # type: ignore
    try:
        assert svc._normalize_device("auto") == 0
    finally:
        del sys.modules["torch"]


def test_map_label_with_id2label_noncanonical() -> None:
    svc = FinBertService.__new__(FinBertService)
    svc._id2label = {0: "some_label"}
    # when id2label contains a mapping the method should return it (lowercased)
    assert svc._map_label("LABEL_0") == "some_label"


def test_map_label_bad_index_returns_neutral() -> None:
    svc = FinBertService.__new__(FinBertService)
    # malformed LABEL_ value
    assert svc._map_label("LABEL_x") == "neutral"


def test_finbert_init_handles_nonint_id2label(monkeypatch: MonkeyPatch) -> None:
    # fake transformers where id2label keys are non-numeric to trigger the except branch
    class FakeModel:
        def __init__(self) -> None:
            self.config = type("c", (), {"id2label": {"a": "POS"}})()

    class AutoModelForSequenceClassification:
        @staticmethod
        def from_pretrained(name: str) -> FakeModel:
            return FakeModel()

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(name: str) -> object:
            return object()

    def fake_pipeline(*args: Any, **kwargs: Any) -> object:
        def _call(
            texts: list[str],
            batch_size: int | None = None,
        ) -> list[list[dict[str, str | float]]]:
            return [[{"label": "LABEL_0", "score": 1.0}] for _ in texts]

        return _call

    fake_transformers = type("mod", (), {})()
    setattr(
        fake_transformers,
        "AutoModelForSequenceClassification",
        AutoModelForSequenceClassification,
    )
    setattr(fake_transformers, "AutoTokenizer", AutoTokenizer)
    setattr(fake_transformers, "pipeline", fake_pipeline)

    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    svc = FinBertService(model_name="fm", device="cpu")
    # when id2label conversion fails we expect an empty mapping
    assert getattr(svc, "_id2label", {}) == {}


def test_finbert_init_when_no_id2label_sets_empty(monkeypatch: MonkeyPatch) -> None:
    # fake transformers where model.config has no id2label attribute
    class FakeModel:
        def __init__(self) -> None:
            self.config = type("c", (), {})()

    class AutoModelForSequenceClassification:
        @staticmethod
        def from_pretrained(name: str) -> FakeModel:
            return FakeModel()

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(name: str) -> object:
            return object()

    def fake_pipeline(*args: Any, **kwargs: Any) -> object:
        def _call(
            texts: list[str], batch_size: int | None = None
        ) -> list[list[dict[str, str | float]]]:
            return [[{"label": "LABEL_0", "score": 1.0}] for _ in texts]

        return _call

    fake_transformers = type("mod", (), {})()
    setattr(
        fake_transformers,
        "AutoModelForSequenceClassification",
        AutoModelForSequenceClassification,
    )
    setattr(fake_transformers, "AutoTokenizer", AutoTokenizer)
    setattr(fake_transformers, "pipeline", fake_pipeline)

    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    svc = FinBertService(model_name="fm2", device="cpu")
    assert getattr(svc, "_id2label", {}) == {}

    def test_warmup_calls_predict_and_logs(
        monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
    ) -> None:
        svc = FinBertService.__new__(FinBertService)

        called = {}

        def fake_predict(texts: list[str], batch_size: int = 1) -> list[str]:
            called["ok"] = True
            return ["ok"]

        svc.predict = fake_predict  # type: ignore

        with caplog.at_level("INFO"):
            svc.warmup()

        assert called.get("ok") is True
        # ensure warmup success logs the info message
        assert any(
            "FinBertService warmup completed" in r.getMessage() for r in caplog.records
        )


def test_normalize_device_cuda_bad_and_non_numeric() -> None:
    svc = FinBertService.__new__(FinBertService)
    assert svc._normalize_device("cuda:bad") == 0
    assert svc._normalize_device("notanumber") == -1


def test_map_label_neg_and_unknown() -> None:
    svc = FinBertService.__new__(FinBertService)
    assert svc._map_label("-") == "negative"
    assert svc._map_label("mystery_label") == "neutral"


def test_normalize_device_auto_import_error() -> None:
    import builtins

    svc = FinBertService.__new__(FinBertService)
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> Any:
        if name == "torch":
            raise ImportError("no torch")
        return real_import(name, globals, locals, fromlist, level)

    builtins.__import__ = fake_import
    try:
        assert svc._normalize_device("auto") == -1
    finally:
        builtins.__import__ = real_import
