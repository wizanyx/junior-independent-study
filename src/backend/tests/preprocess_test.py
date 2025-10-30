from __future__ import annotations

from dataclasses import asdict

import pytest

from app.preprocess import (
    Pipeline,
    deduplicate_by_text,
    default_pipeline,
    drop_empty_text,
    normalize_whitespace,
    truncate_text,
    uppercase_ticker_if_present,
)
from app.schema import Document


def test_normalize_whitespace_returns_same_instance_when_no_change() -> None:
    d = Document(source="news", text="hello world")
    out = normalize_whitespace(d)
    assert out is d


def test_normalize_whitespace_collapses_spaces_and_trims() -> None:
    d = Document(source="news", text="  hello\n\tworld   ")
    out = normalize_whitespace(d)
    assert out.text == "hello world"
    assert out is not d


def test_truncate_text_behavior() -> None:
    step = truncate_text(5)
    d1 = Document(source="news", text="short")
    d2 = Document(source="news", text="a little longer")
    out1 = step(d1)
    out2 = step(d2)
    assert out1 is not None and out1 is d1 and out1.text == "short"
    assert out2 is not None and out2.text == "a lit"


def test_drop_empty_text() -> None:
    step = drop_empty_text(min_len=2)
    d1 = Document(source="news", text=" ")
    d2 = Document(source="news", text="a")
    d3 = Document(source="news", text="ok")
    assert step(d1) is None
    assert step(d2) is None
    assert step(d3) is d3


def test_uppercase_ticker_step_and_model_normalization() -> None:
    d = Document(source="news", text="t", ticker="aapl")
    # Model already uppercases in __post_init__
    assert d.ticker == "AAPL"
    # The step keeps it uppercase as well
    out = uppercase_ticker_if_present(d)
    assert out.ticker == "AAPL"


def test_deduplicate_by_text() -> None:
    step = deduplicate_by_text()
    d1 = Document(source="news", text="same")
    d2 = Document(source="news", text="same")
    d3 = Document(source="news", text="different")
    assert step(d1) is d1
    assert step(d2) is None  # duplicate dropped
    assert step(d3) is d3


def test_deduplicate_by_text_ignores_whitespace_only() -> None:
    step = deduplicate_by_text()
    d = Document(source="news", text="   ")  # whitespace-only => empty key
    out = step(d)
    # Should pass through (not dropped) when key is empty
    assert out is d


def test_normalize_whitespace_noop_for_whitespace_only_text() -> None:
    # Should return the original doc to avoid creating an empty-text Document
    d = Document(source="news", text="   \n\t   ")
    out = normalize_whitespace(d)
    assert out is d


def test_pipeline_process_one_and_many() -> None:
    pl = Pipeline([normalize_whitespace, drop_empty_text(), truncate_text(10)])

    obj = {"source": "news", "text": "  hello   world   "}
    out = pl.process_one(obj)
    assert out is not None
    # normalized then truncated to 10 chars
    assert out.text == "hello worl"

    many = pl.process_many(
        [
            {"source": "news", "text": "  a  "},
            {"source": "news", "text": " "},  # dropped (whitespace-only)
            {
                "source": "news",
                "text": "  b   c  d  e  f  g  h  i  j  k  ",
            },  # will be truncated
        ]
    )
    assert len(many) == 2
    assert many[0].text == "a"
    assert len(many[1].text) <= 10


def test_pipeline_process_one_drops_when_step_returns_none() -> None:
    pl = Pipeline([drop_empty_text(min_len=1)])
    d = Document(source="news", text="   ")
    out = pl.process_one(d)
    assert out is None


def test_uppercase_ticker_noop_when_missing() -> None:
    d = Document(source="news", text="t", ticker=None)
    out = uppercase_ticker_if_present(d)
    assert out is d


def test_process_one_rejects_unsupported_payload_type() -> None:
    pl = Pipeline([normalize_whitespace])
    with pytest.raises(TypeError):
        pl.process_one(123)  # type: ignore[arg-type]


def test_default_pipeline_end_to_end_and_dedup() -> None:
    pl = default_pipeline(max_text_length=20)

    items = [
        {
            "source": "news",
            "text": "  Apple  beats\n\t earnings   ",
            "ticker": "aapl",
        },
        {
            "source": "news",
            "text": "Apple beats earnings",
            "ticker": "AAPL",
        },  # duplicate after normalize
        {"source": "news", "text": "   "},  # dropped
    ]

    results = pl.process_many(items)
    assert len(results) == 1

    doc = results[0]
    assert doc.text == "Apple beats earnings"
    assert doc.ticker == "AAPL"  # normalized by model
    # to_dict should serialize fields in JSON-friendly way
    data = asdict(doc)
    assert isinstance(data["id"], str)
