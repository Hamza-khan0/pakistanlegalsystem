from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.crawled_document import CrawledDocument
from app.models.enums import CrawlProcessingStatus
from app.services.ocr import OcrPipelineError, process_file


def list_crawled_documents(
    db: Session,
    *,
    q: str | None = None,
    source_id: str | None = None,
    processing_status: str | None = None,
) -> list[CrawledDocument]:
    query = (
        select(CrawledDocument)
        .options(
            joinedload(CrawledDocument.source),
            joinedload(CrawledDocument.legal_source),
        )
        .order_by(CrawledDocument.updated_at.desc())
    )
    if q:
        like_value = f"%{q.strip()}%"
        query = query.where(
            or_(
                CrawledDocument.title.ilike(like_value),
                CrawledDocument.source_url.ilike(like_value),
                CrawledDocument.document_type.ilike(like_value),
            )
        )
    if source_id:
        query = query.where(CrawledDocument.source_id == source_id)
    if processing_status:
        query = query.where(CrawledDocument.processing_status == processing_status)
    return list(db.scalars(query).all())


def get_crawled_document_or_none(db: Session, document_id: str) -> CrawledDocument | None:
    return db.scalar(
        select(CrawledDocument)
        .options(
            joinedload(CrawledDocument.source),
            joinedload(CrawledDocument.legal_source),
        )
        .where(CrawledDocument.id == document_id)
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def process_crawled_document(
    db: Session,
    document: CrawledDocument,
    *,
    force_ocr: bool = False,
) -> CrawledDocument:
    existing_errors = document.errors_json or {}
    existing_metadata = document.metadata_json or {}
    file_path = document.downloaded_file_path or document.raw_html_path
    if not file_path:
        document.processing_status = CrawlProcessingStatus.FAILED
        document.errors_json = {
            **existing_errors,
            "message": "No downloaded file or raw HTML was available for processing.",
        }
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    document.processing_status = CrawlProcessingStatus.PENDING
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        result = process_file(
            Path(file_path),
            mime_type=document.mime_type,
            language_hint=document.language,
            force_ocr=force_ocr,
        )
        status_map = {
            "Text Extracted": CrawlProcessingStatus.TEXT_EXTRACTED,
            "OCR Completed": CrawlProcessingStatus.OCR_COMPLETED,
            "Partially Extracted": CrawlProcessingStatus.PARTIALLY_EXTRACTED,
        }
        document.processing_status = status_map.get(
            result.status,
            CrawlProcessingStatus.OCR_REQUIRED if result.needs_ocr else CrawlProcessingStatus.TEXT_EXTRACTED,
        )
        document.extracted_text = result.text
        document.extracted_text_preview = result.preview_text
        document.normalized_text = result.normalized_text
        document.language_detected = result.language
        document.page_count = result.page_count
        document.ocr_engine = result.ocr_engine
        document.ocr_status = result.ocr_status
        document.ocr_confidence_summary = result.confidence_summary
        document.processed_at = _now()
        document.errors_json = {
            "warnings": result.warnings,
        }
        document.metadata_json = {
            **existing_metadata,
            "normalizedTextPreview": result.normalized_text[:1200],
            "pageExtractions": [
                {
                    "pageNumber": page.page_number,
                    "method": page.method,
                    "confidence": page.confidence,
                    "textPreview": page.text[:400],
                }
                for page in result.pages[:12]
            ],
        }
    except OcrPipelineError as exc:
        document.processing_status = CrawlProcessingStatus.FAILED
        document.processed_at = _now()
        document.errors_json = {
            **existing_errors,
            "message": str(exc),
        }

    db.add(document)
    db.commit()
    db.refresh(document)
    return document
