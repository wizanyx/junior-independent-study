from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from app.schema import Document

if TYPE_CHECKING:
    import pytest  # noqa: F401


def _is_iso_with_z(s: str) -> bool:
    # Example: 2025-01-01T12:00:00.000000Z
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", s))


def test_document_generates_uuid_and_utc_created_at() -> None:
    d = Document(source="news", text="hello")
    # id should be a valid UUID string
    uuid_obj = uuid.UUID(d.id)
    assert str(uuid_obj) == d.id

    # created_at should be timezone-aware UTC
    assert isinstance(d.created_at, datetime)
    assert d.created_at.tzinfo is not None
    # UTC offset 0
    assert d.created_at.utcoffset() == timedelta(0)


def test_document_uses_provided_id_and_normalizes_ticker() -> None:
    d = Document(id="my-id", source="reddit", text="hi", ticker=" aapl ")
    assert d.id == "my-id"
    assert d.ticker == "AAPL"

    # Empty ticker becomes None after normalization
    d2 = Document(source="reddit", text="hi", ticker="  ")
    assert d2.ticker is None


def test_document_rejects_missing_required_fields() -> None:
    # Missing/empty source
    try:
        Document(text="x")  # type: ignore[call-arg]
        assert False, "expected ValueError for missing source"
    except ValueError as e:  # noqa: PT011 - explicit exception assertion
        assert "source" in str(e)

    # Missing/empty text
    try:
        Document(source="news")  # type: ignore[call-arg]
        assert False, "expected ValueError for missing text"
    except ValueError as e:  # noqa: PT011
        assert "text" in str(e)

    # Empty id gets replaced
    d = Document(id="", source="news", text="x")
    assert d.id != ""
    # should be a valid UUID
    uuid.UUID(d.id)


def test_to_dict_serializes_created_at_iso_z() -> None:
    d = Document(source="news", text="hello")
    data = d.to_dict()
    assert isinstance(data["id"], str)
    assert data["source"] == "news"
    assert _is_iso_with_z(data["created_at"]) is True

    # Round-trip parsing of the ISO string
    iso = data["created_at"].replace("Z", "+00:00")
    parsed = datetime.fromisoformat(iso)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)


def test_from_dict_accepts_iso_and_datetime() -> None:
    iso_z = "2025-01-01T12:00:00.000000Z"
    d1 = Document.from_dict(
        {
            "source": "news",
            "text": "t",
            "created_at": iso_z,
        }
    )
    assert d1.created_at.tzinfo is not None
    assert d1.created_at.utcoffset() == timedelta(0)

    iso_offset = "2025-01-01T12:00:00.000000+00:00"
    d2 = Document.from_dict(
        {
            "source": "news",
            "text": "t",
            "created_at": iso_offset,
        }
    )
    assert d2.created_at.tzinfo is not None
    assert d2.created_at.utcoffset() == timedelta(0)

    naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # naive
    d3 = Document.from_dict(
        {
            "source": "news",
            "text": "t",
            "created_at": naive_dt,
        }
    )
    assert d3.created_at.tzinfo is not None
    assert d3.created_at.utcoffset() == timedelta(0)


def test_direct_init_with_naive_created_at_normalizes_to_utc() -> None:
    naive = datetime(2025, 1, 1, 12, 0, 0)
    d = Document(source="news", text="x", created_at=naive)
    assert d.created_at.tzinfo is not None
    assert d.created_at.utcoffset() == timedelta(0)


def test_from_dict_invalid_iso_falls_back_to_now() -> None:
    d = Document.from_dict({"source": "news", "text": "x", "created_at": "not-a-date"})
    assert d.created_at.tzinfo is not None
    assert d.created_at.utcoffset() == timedelta(0)


def test_from_dict_missing_created_at_uses_now() -> None:
    d = Document.from_dict({"source": "news", "text": "x"})
    assert d.created_at.tzinfo is not None
    assert d.created_at.utcoffset() == timedelta(0)


def test_from_adapter_upload_mapping() -> None:
    payload: dict[str, Any] = {
        "id": "abc",
        "ticker": "msft",
        "created_at": "2025-01-01T00:00:00.000000Z",
        "text": "body",
        "permalink": "https://example.com/x",
    }
    d = Document.from_adapter("upload", payload)
    assert d.id == "abc"
    assert d.source == "upload"
    assert d.ticker == "MSFT"
    assert d.text == "body"
    assert d.permalink == "https://example.com/x"


def test_from_adapter_fallback_passes_through() -> None:
    d = Document.from_adapter("news", {"source": "news", "text": "t", "ticker": "amzn"})
    assert d.source == "news"
    assert d.ticker == "AMZN"


def test_round_trip_to_from_dict() -> None:
    original = Document(source="news", text="hello world", ticker="tsla")
    as_dict = original.to_dict()

    # Construct again from dict
    rebuilt = Document.from_dict(as_dict)

    assert rebuilt.source == original.source
    assert rebuilt.ticker == "TSLA"
    assert rebuilt.text == original.text
    # created_at should be close and UTC-aware
    assert rebuilt.created_at.tzinfo is not None
    assert rebuilt.created_at.utcoffset() == timedelta(0)

    # id can be different only if original had empty id; here it should be present
    uuid.UUID(rebuilt.id)
