from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.services.crawling.base import DiscoveredDocument
from app.services.corpus.normalization import detect_language


def parse_listing_page(
    html: str,
    *,
    base_url: str,
    detail_link_selector: str,
    next_link_selector: str | None = None,
) -> tuple[list[str], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    detail_urls: list[str] = []
    for anchor in soup.select(detail_link_selector):
        href = anchor.get("href")
        if not href:
            continue
        detail_urls.append(urljoin(base_url, href))

    next_url: str | None = None
    if next_link_selector:
        next_anchor = soup.select_one(next_link_selector)
        if next_anchor and next_anchor.get("href"):
            next_url = urljoin(base_url, next_anchor.get("href"))

    return detail_urls, next_url


def parse_detail_page(
    html: str,
    *,
    base_url: str,
    title_selector: str,
    body_selector: str,
    download_link_selector: str | None = None,
    metadata_selectors: dict[str, str] | None = None,
    default_document_type: str = "",
    default_language: str = "Unknown",
) -> DiscoveredDocument:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one(title_selector)
    body_node = soup.select_one(body_selector)
    metadata_selectors = metadata_selectors or {}

    title = title_node.get_text(" ", strip=True) if title_node else "Untitled legal document"
    body_text = body_node.get_text("\n", strip=True) if body_node else ""
    metadata: dict[str, object] = {}
    for key, selector in metadata_selectors.items():
        node = soup.select_one(selector)
        if node:
            metadata[key] = node.get_text(" ", strip=True)

    document_url = ""
    if download_link_selector:
        link = soup.select_one(download_link_selector)
        if link and link.get("href"):
            document_url = urljoin(base_url, link.get("href"))

    language = str(metadata.get("language") or default_language)
    if not language or language == "Unknown":
        language = detect_language(body_text or title)

    document_type = str(
        metadata.get("documentType")
        or metadata.get("document_type")
        or default_document_type
        or metadata.get("category")
        or "Legal Material"
    )

    return DiscoveredDocument(
        source_url=base_url,
        title=title,
        document_type=document_type,
        language=language,
        body_text=body_text,
        document_url=document_url,
        metadata=metadata,
    )
