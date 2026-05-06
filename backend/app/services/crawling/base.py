from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FetchedResource:
    url: str
    content: bytes
    content_type: str
    text: str


@dataclass(slots=True)
class DiscoveredDocument:
    source_url: str
    title: str
    document_type: str
    language: str
    body_text: str = ""
    document_url: str = ""
    mime_type: str = "text/html"
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CrawlRunStats:
    pages_fetched: int = 0
    documents_discovered: int = 0
    documents_saved: int = 0
    errors_count: int = 0
    warnings: list[str] = field(default_factory=list)
