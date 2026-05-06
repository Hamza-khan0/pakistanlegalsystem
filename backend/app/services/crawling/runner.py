from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.crawl_job import CrawlJob
from app.models.crawled_document import CrawledDocument
from app.models.crawl_source import CrawlSource
from app.models.enums import (
    CrawlMode,
    CrawlDocumentStatus,
    CrawlJobStatus,
    CrawlProcessingStatus,
)
from app.services.crawling.base import CrawlRunStats, DiscoveredDocument
from app.services.crawling.dedupe import build_duplicate_hash, find_existing_document
from app.services.crawling.fetcher import fetch_resource
from app.services.crawling.parsers.html import parse_detail_page, parse_listing_page
from app.services.corpus.normalization import detect_language


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _write_file(root: Path, filename: str, payload: bytes) -> str:
    root.mkdir(parents=True, exist_ok=True)
    destination = root / filename
    destination.write_bytes(payload)
    return str(destination)


def _safe_filename(url: str, fallback_suffix: str = ".html") -> str:
    digest = sha256(url.encode("utf-8")).hexdigest()
    suffix = Path(urlparse(url).path).suffix or fallback_suffix
    return f"{digest}{suffix}"


def _persist_document(
    db: Session,
    *,
    source: CrawlSource,
    discovered: DiscoveredDocument,
    raw_html_path: str = "",
    downloaded_file_path: str = "",
    mime_type: str = "text/html",
) -> bool:
    existing_metadata = dict(getattr(discovered, "metadata", {}) or {})
    duplicate_hash = build_duplicate_hash(
        discovered.source_url,
        discovered.title,
        discovered.body_text[:1200],
        discovered.document_url,
    )
    existing = find_existing_document(
        db,
        source_id=source.id,
        source_url=discovered.source_url,
        duplicate_hash=duplicate_hash,
    )
    if existing is None:
        document = CrawledDocument(source_id=source.id)
        db.add(document)
        created = True
    else:
        document = existing
        created = False

    document.legal_source_id = existing.legal_source_id if existing else None
    document.source_url = discovered.source_url
    document.title = discovered.title
    document.document_type = discovered.document_type
    document.language = discovered.language or detect_language(discovered.body_text or discovered.title)
    document.jurisdiction = str(discovered.metadata.get("jurisdiction") or "Pakistan")
    document.raw_html_path = raw_html_path
    document.downloaded_file_path = downloaded_file_path
    document.mime_type = mime_type
    document.crawl_status = (
        CrawlDocumentStatus.DOWNLOADED if downloaded_file_path else CrawlDocumentStatus.FETCHED
    )
    document.processing_status = (
        CrawlProcessingStatus.TEXT_EXTRACTED if discovered.body_text else CrawlProcessingStatus.PENDING
    )
    document.duplicate_hash = duplicate_hash
    document.extracted_text = discovered.body_text
    document.extracted_text_preview = discovered.body_text[:1500]
    document.normalized_text = ""
    document.metadata_json = {
        **(document.metadata_json or {}),
        **existing_metadata,
        "documentUrl": discovered.document_url,
        "crawlSourceName": source.name,
        "crawlSourceCategory": source.category,
    }
    db.commit()
    db.refresh(document)
    return created


def _run_index_crawl(db: Session, *, source: CrawlSource, stats: CrawlRunStats) -> None:
    config = source.config_json
    entry_urls = list(config.get("entryUrls") or [])
    detail_selector = str(config.get("listing", {}).get("detailLinkSelector") or "a")
    next_selector = config.get("pagination", {}).get("nextLinkSelector")
    max_pages = int(config.get("maxPages") or 6)
    rate_limit_seconds = float(config.get("rateLimitSeconds") or 0.0)
    content_config = dict(config.get("content") or {})

    pending_pages = entry_urls[:]
    visited_pages: set[str] = set()
    detail_urls: set[str] = set()
    raw_root = Path(settings.crawl_storage_dir) / "raw" / source.id
    download_root = Path(settings.crawl_storage_dir) / "downloads" / source.id

    while pending_pages and len(visited_pages) < max_pages:
        page_url = pending_pages.pop(0)
        if page_url in visited_pages:
            continue
        visited_pages.add(page_url)

        listing = fetch_resource(page_url, rate_limit_seconds=rate_limit_seconds)
        stats.pages_fetched += 1
        raw_name = _safe_filename(page_url, ".html")
        _write_file(raw_root, raw_name, listing.content)

        next_detail_urls, next_page = parse_listing_page(
            listing.text,
            base_url=listing.url,
            detail_link_selector=detail_selector,
            next_link_selector=next_selector,
        )
        detail_urls.update(next_detail_urls)
        if next_page and next_page not in visited_pages and next_page not in pending_pages:
            pending_pages.append(next_page)

    for detail_url in sorted(detail_urls):
        detail = fetch_resource(detail_url, rate_limit_seconds=rate_limit_seconds)
        stats.pages_fetched += 1
        raw_name = _safe_filename(detail_url, ".html")
        raw_html_path = _write_file(raw_root, raw_name, detail.content)
        discovered = parse_detail_page(
            detail.text,
            base_url=detail.url,
            title_selector=str(content_config.get("titleSelector") or "title"),
            body_selector=str(content_config.get("bodySelector") or "body"),
            download_link_selector=content_config.get("downloadLinkSelector"),
            metadata_selectors=dict(content_config.get("metadataSelectors") or {}),
            default_document_type=str(config.get("documentTypeHint") or source.category or "Legal Material"),
            default_language=str(source.language_hint or "Unknown"),
        )

        downloaded_file_path = ""
        mime_type = detail.content_type or "text/html"
        if discovered.document_url:
            fetched_file = fetch_resource(
                discovered.document_url,
                rate_limit_seconds=rate_limit_seconds,
            )
            stats.pages_fetched += 1
            file_name = _safe_filename(discovered.document_url, ".bin")
            downloaded_file_path = _write_file(download_root, file_name, fetched_file.content)
            mime_type = fetched_file.content_type or mime_type

        stats.documents_discovered += 1
        created = _persist_document(
            db,
            source=source,
            discovered=discovered,
            raw_html_path=raw_html_path,
            downloaded_file_path=downloaded_file_path,
            mime_type=mime_type,
        )
        if created:
            stats.documents_saved += 1


def _run_direct_document_crawl(db: Session, *, source: CrawlSource, stats: CrawlRunStats) -> None:
    config = source.config_json
    entry_urls = list(config.get("entryUrls") or [])
    rate_limit_seconds = float(config.get("rateLimitSeconds") or 0.0)
    download_root = Path(settings.crawl_storage_dir) / "downloads" / source.id

    for entry_url in entry_urls:
        fetched = fetch_resource(entry_url, rate_limit_seconds=rate_limit_seconds)
        stats.pages_fetched += 1
        filename = _safe_filename(entry_url, ".bin")
        downloaded_file_path = _write_file(download_root, filename, fetched.content)
        title = (
            str(config.get("titlePrefix") or "").strip() + " " + Path(urlparse(entry_url).path).stem.replace("-", " ")
        ).strip()
        discovered = DiscoveredDocument(
            source_url=entry_url,
            title=title or "Direct legal document",
            document_type=str(config.get("documentTypeHint") or source.category or "Legal Material"),
            language=str(source.language_hint or "Unknown"),
            body_text="",
            document_url=entry_url,
            mime_type=fetched.content_type or "application/octet-stream",
            metadata={
                "category": source.category,
                "documentType": str(config.get("documentTypeHint") or source.category),
            },
        )
        stats.documents_discovered += 1
        created = _persist_document(
            db,
            source=source,
            discovered=discovered,
            downloaded_file_path=downloaded_file_path,
            mime_type=fetched.content_type or "application/octet-stream",
        )
        if created:
            stats.documents_saved += 1


def run_crawl_job(db: Session, *, source: CrawlSource) -> CrawlJob:
    job = CrawlJob(source_id=source.id, status=CrawlJobStatus.RUNNING, started_at=_now())
    db.add(job)
    db.commit()
    db.refresh(job)

    stats = CrawlRunStats()
    try:
        if source.crawl_mode in {CrawlMode.INDEX, CrawlMode.PAGINATED_INDEX}:
            _run_index_crawl(db, source=source, stats=stats)
        else:
            _run_direct_document_crawl(db, source=source, stats=stats)
        job.status = CrawlJobStatus.COMPLETED
    except Exception as exc:
        stats.errors_count += 1
        stats.warnings.append(str(exc))
        job.status = CrawlJobStatus.FAILED
    finally:
        job.completed_at = _now()
        job.pages_fetched = stats.pages_fetched
        job.documents_discovered = stats.documents_discovered
        job.documents_saved = stats.documents_saved
        job.errors_count = stats.errors_count
        job.metadata_json = {
            "warnings": stats.warnings,
            "sourceName": source.name,
        }
        db.add(job)
        db.commit()
        db.refresh(job)

    return job


def list_crawl_jobs(db: Session, *, limit: int = 25) -> list[CrawlJob]:
    return list(
        db.scalars(
            select(CrawlJob)
            .options(joinedload(CrawlJob.source))
            .order_by(CrawlJob.started_at.desc())
            .limit(limit)
        ).all()
    )


def get_crawl_job_or_none(db: Session, job_id: str) -> CrawlJob | None:
    return db.scalar(
        select(CrawlJob)
        .options(joinedload(CrawlJob.source))
        .where(CrawlJob.id == job_id)
    )
