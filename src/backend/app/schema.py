from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_utc() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class Document:
    """
    Canonical normalized document schema used across ingestion adapters and APIs.

    Fields:
    - id: unique identifier for the document (string).
          If not provided, a UUID4 will be generated.
    - source: the upstream source, e.g. 'news', 'reddit', 'upload'
    - ticker: associated ticker as uppercase string or None
    - created_at: timezone-aware UTC datetime internally; serialized to ISO8601
                  with 'Z' suffix (e.g. '2025-01-01T12:00:00.000000Z') in to_dict
    - text: the raw/full text body to be analyzed
    - permalink: optional URL linking back to the original source
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = field(default="")
    ticker: str | None = field(default=None)
    created_at: datetime = field(default_factory=_now_utc)
    text: str = field(default="")
    permalink: str | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.source:
            raise ValueError("Document.source is required")
        if not self.text:
            raise ValueError("Document.text is required")
        # Normalize ticker to upper-case if present
        if isinstance(self.ticker, str):
            self.ticker = self.ticker.strip().upper() or None
        # Ensure created_at is timezone-aware UTC
        if isinstance(self.created_at, datetime):
            if self.created_at.tzinfo is None:
                # Assume naive datetimes are UTC
                self.created_at = self.created_at.replace(tzinfo=timezone.utc)
            else:
                self.created_at = self.created_at.astimezone(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON-serializable dict representation.
        created_at is serialized to an ISO8601 string with 'Z'.
        """
        d = asdict(self)
        # Serialize created_at to ISO with microseconds and 'Z'
        ca: datetime = self.created_at
        d["created_at"] = (
            ca.astimezone(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        return d

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Document:
        """
        Create Document from a dict. Accepts created_at as datetime or ISO string.
        """
        d = payload.copy()

        created_at_val = d.get("created_at")
        if isinstance(created_at_val, str) and created_at_val:
            # Support 'Z' suffix and various ISO shapes
            iso = created_at_val.strip()
            if iso.endswith("Z"):
                iso = iso[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(iso)
            except ValueError:
                parsed = _now_utc()
            created_at_dt = (
                parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            )
        elif isinstance(created_at_val, datetime):
            created_at_dt = (
                created_at_val
                if created_at_val.tzinfo
                else created_at_val.replace(tzinfo=timezone.utc)
            )
        else:
            created_at_dt = _now_utc()

        return cls(
            id=d.get("id", ""),
            source=d.get("source", ""),
            ticker=d.get("ticker"),
            created_at=created_at_dt,
            text=d.get("text", ""),
            permalink=d.get("permalink"),
        )

    @classmethod
    def from_adapter(cls, adapter_name: str, payload: dict[str, Any]) -> Document:
        """
        Convert adapter-specific payload into Document.

        adapter_name: one of 'news', 'reddit', 'upload', etc.
        payload: raw payload returned by adapter.

        Mappings:
        - 'upload' -> expects 'text', 'created_at' (optional), 'ticker' (optional)
        """
        # TODO: Add more adapter mappings as needed
        if adapter_name == "upload":
            return cls.from_dict(
                {
                    "id": payload.get("id"),
                    "source": "upload",
                    "ticker": payload.get("ticker"),
                    "created_at": payload.get("created_at"),
                    "text": payload.get("text"),
                    "permalink": payload.get("permalink"),
                }
            )
        # Fallback: assume user provides canonical fields
        return cls.from_dict(payload)
