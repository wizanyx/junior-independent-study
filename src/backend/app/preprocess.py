from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import replace

from .schema import Document

# A Step is a callable that accepts a Document and returns Document | None (None = drop)
Step = Callable[[Document], Document | None]


def _ensure_document(obj: object) -> Document:
    """Coerce a dict or Document-like payload into a Document instance.

    Raises TypeError for unsupported inputs.
    """
    if isinstance(obj, Document):
        return obj
    if isinstance(obj, dict):
        return Document.from_dict(obj)
    raise TypeError("Input must be Document or dict")


def normalize_whitespace(doc: Document) -> Document:
    """Collapse all whitespace to single spaces and trim.

    Returns the original instance if no change is needed; otherwise returns a copy
    with normalized text.
    """
    text = doc.text or ""
    # collapse whitespace
    normalized = re.sub(r"\s+", " ", text).strip()
    # If normalization would yield empty text, let a later drop step handle it
    # to avoid re-validating a Document with empty text in __post_init__.
    if normalized == "" and text.strip() == "":
        return doc
    if normalized == doc.text:
        return doc
    return replace(doc, text=normalized)


def truncate_text(max_len: int) -> Step:
    """Return a step that truncates Document.text to at most max_len characters."""

    def _step(doc: Document) -> Document:
        if len(doc.text) <= max_len:
            return doc
        return replace(doc, text=doc.text[:max_len])

    return _step


def drop_empty_text(min_len: int = 1) -> Step:
    """Drop documents whose text is empty or shorter than min_len (after strip)."""

    def _step(doc: Document) -> Document | None:
        if not doc.text or len(doc.text.strip()) < min_len:
            return None
        return doc

    return _step


def uppercase_ticker_if_present(doc: Document) -> Document:
    """Normalize ticker to uppercase if provided.

    Note: This is redundant with Document.__post_init__ but kept as a reusable step
    for pipelines that operate on already-constructed Document instances.
    """
    if isinstance(doc.ticker, str) and doc.ticker:
        return replace(doc, ticker=doc.ticker.strip().upper() or None)
    return doc


def deduplicate_by_text() -> Step:
    seen: set[str] = set()

    def _step(doc: Document) -> Document | None:
        key = (doc.text or "").strip()
        if not key:
            return doc
        if key in seen:
            return None
        seen.add(key)
        return doc

    return _step


class Pipeline:
    """Composable preprocessing pipeline for Documents.

    Each step is a function that receives a Document and returns either a (possibly
    modified) Document or None to signal dropping the document.
    """

    def __init__(self, steps: Iterable[Step]):
        self.steps = list(steps)

    def process_one(self, payload: object) -> Document | None:
        doc: Document | None = _ensure_document(payload)
        for step in self.steps:
            if doc is None:
                return None
            doc = step(doc)
        return doc

    def process_many(self, payloads: Iterable[object]) -> list[Document]:
        out: list[Document] = []
        for p in payloads:
            processed = self.process_one(p)
            if processed is not None:
                out.append(processed)
        return out


# Factory for a sensible default pipeline
def default_pipeline(max_text_length: int = 5000) -> Pipeline:
    """Factory for a sensible default pipeline.

    Note: Ticker normalization is handled by the Document model. We omit the
    explicit uppercase_ticker_if_present step to avoid redundancy.
    """
    return Pipeline(
        [
            normalize_whitespace,
            drop_empty_text(min_len=1),
            truncate_text(max_text_length),
            deduplicate_by_text(),
        ]
    )
