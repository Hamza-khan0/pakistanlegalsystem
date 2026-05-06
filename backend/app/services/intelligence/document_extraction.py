from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import ExtractionStatus, IntelligenceStatus, OcrStatus, ParsingStatus
from app.services import documents as document_service
from app.services.corpus.normalization import detect_language
from app.services.ocr import OcrPipelineError, process_file


TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".text", ".csv", ".json", ".html", ".htm"}
TEXT_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "text/html",
}


class DocumentProcessingError(RuntimeError):
    pass


def can_extract_document(document: Document) -> bool:
    suffix = Path(document.file_name or document.file_path).suffix.lower()
    mime = (document.mime_type or "").lower()
    return (
        suffix in TEXT_EXTENSIONS
        or suffix in {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
        or mime in TEXT_MIME_TYPES
        or mime == "application/pdf"
        or mime.startswith("image/")
    )


def extract_text_from_document(document: Document) -> str:
    file_path = Path(document.file_path)
    if not file_path.exists():
        raise DocumentProcessingError("Stored file is missing from the uploads directory.")

    try:
        result = process_file(
            file_path,
            mime_type=document.mime_type,
            language_hint=str(document.metadata_json.get("language") or ""),
        )
    except OcrPipelineError as exc:
        raise DocumentProcessingError(str(exc)) from exc

    existing_metadata = document.metadata_json or {}
    document.metadata_json = {
        **existing_metadata,
        "detectedLanguage": result.language or detect_language(result.text),
        "normalizedTextPreview": result.normalized_text[:1200],
        "ocrOutcome": result.status,
        "ocrEngine": result.ocr_engine,
        "ocrConfidence": result.confidence_summary,
        "ocrWarnings": result.warnings,
        "pageExtractions": [
            {
                "pageNumber": page.page_number,
                "method": page.method,
                "confidence": page.confidence,
                "textPreview": page.text[:350],
            }
            for page in result.pages[:12]
        ],
    }
    document.pages = result.page_count
    document.ocr_status = OcrStatus.COMPLETED if result.ocr_used else OcrStatus.NOT_STARTED
    return result.text


def process_document(db: Session, document: Document) -> Document:
    document.intelligence_status = IntelligenceStatus.PROCESSING
    document.parsing_status = ParsingStatus.IN_PROGRESS
    document.extraction_error = ""
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        extracted_text = extract_text_from_document(document)
        if not extracted_text:
            raise DocumentProcessingError(
                "No extractable text was found. This document likely needs OCR or manual review."
            )

        document.extracted_text = extracted_text
        document.extracted_text_preview = extracted_text[:1200]
        document.extraction_error = ""
        document.processed_at = datetime.now(timezone.utc)
        document.intelligence_status = IntelligenceStatus.PROCESSED
        document.extraction_status = ExtractionStatus.PARSED
        document.parsing_status = ParsingStatus.COMPLETED
        document.ocr_status = OcrStatus.COMPLETED if Path(document.file_name).suffix.lower() == ".pdf" else OcrStatus.NOT_STARTED
        document.metadata_json = {
            **(document.metadata_json or {}),
            "extractedCharacters": len(extracted_text),
            "processor": "phase-6-ocr-pipeline",
            "processedAt": document.processed_at.isoformat(),
        }
    except DocumentProcessingError as exc:
        document.extraction_error = str(exc)
        document.processed_at = datetime.now(timezone.utc)
        document.intelligence_status = IntelligenceStatus.FAILED
        document.extraction_status = ExtractionStatus.MANUAL_REVIEW
        document.parsing_status = ParsingStatus.COMPLETED
    finally:
        db.add(document)
        db.commit()
        db.refresh(document)

    return document


def process_document_by_id(db: Session, document_id: str) -> Document | None:
    document = document_service.get_document_or_none(db, document_id)
    if not document:
        return None
    return process_document(db, document)
