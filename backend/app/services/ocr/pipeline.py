from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.services.corpus.normalization import detect_language, normalize_text
from app.services.ocr.image import ocr_image_path
from app.services.ocr.pdf import extract_text_pdf, ocr_pdf
from app.services.ocr.postprocess import clean_extracted_text


TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".text", ".csv", ".json", ".html", ".htm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


@dataclass(slots=True)
class PageText:
    page_number: int
    text: str
    method: str
    confidence: float | None = None


@dataclass(slots=True)
class OcrPipelineResult:
    text: str
    preview_text: str
    normalized_text: str
    language: str
    page_count: int
    needs_ocr: bool
    ocr_used: bool
    status: str
    ocr_status: str
    ocr_engine: str
    confidence_summary: float | None
    warnings: list[str] = field(default_factory=list)
    pages: list[PageText] = field(default_factory=list)


class OcrPipelineError(RuntimeError):
    pass


def _read_text_file(path: Path) -> str:
    if path.suffix.lower() in {".html", ".htm"}:
        from bs4 import BeautifulSoup

        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        return clean_extracted_text(soup.get_text("\n"))

    return clean_extracted_text(path.read_text(encoding="utf-8", errors="ignore"))


def _build_result(
    *,
    text: str,
    page_count: int,
    needs_ocr: bool,
    ocr_used: bool,
    status: str,
    ocr_status: str,
    ocr_engine: str,
    confidence_summary: float | None,
    warnings: list[str],
    pages: list[PageText],
) -> OcrPipelineResult:
    cleaned = clean_extracted_text(text)
    return OcrPipelineResult(
        text=cleaned,
        preview_text=cleaned[:1500],
        normalized_text=normalize_text(cleaned),
        language=detect_language(cleaned),
        page_count=page_count,
        needs_ocr=needs_ocr,
        ocr_used=ocr_used,
        status=status,
        ocr_status=ocr_status,
        ocr_engine=ocr_engine,
        confidence_summary=confidence_summary,
        warnings=warnings,
        pages=pages,
    )


def process_file(
    path: str | Path,
    *,
    mime_type: str = "",
    language_hint: str | None = None,
    force_ocr: bool = False,
) -> OcrPipelineResult:
    file_path = Path(path)
    if not file_path.exists():
        raise OcrPipelineError("Document file could not be found.")

    suffix = file_path.suffix.lower()
    resolved_mime = (mime_type or "").lower()

    if suffix in TEXT_EXTENSIONS or resolved_mime.startswith("text/") or resolved_mime == "application/json":
        text = _read_text_file(file_path)
        if not text:
            raise OcrPipelineError("No text could be extracted from the supplied file.")
        return _build_result(
            text=text,
            page_count=1,
            needs_ocr=False,
            ocr_used=False,
            status="Text Extracted",
            ocr_status="Not Required",
            ocr_engine="builtin-text",
            confidence_summary=None,
            warnings=[],
            pages=[PageText(page_number=1, text=text[:1500], method="text")],
        )

    if suffix == ".pdf" or resolved_mime == "application/pdf":
        text_pdf = extract_text_pdf(file_path)
        enough_text = len(text_pdf.text.strip()) >= 120
        if enough_text and not force_ocr:
            return _build_result(
                text=text_pdf.text,
                page_count=text_pdf.page_count,
                needs_ocr=False,
                ocr_used=False,
                status="Text Extracted",
                ocr_status="Not Required",
                ocr_engine="pdf-text",
                confidence_summary=text_pdf.confidence_summary,
                warnings=text_pdf.warnings,
                pages=[
                    PageText(
                        page_number=page.page_number,
                        text=page.text[:1200],
                        method=page.method,
                        confidence=page.confidence,
                    )
                    for page in text_pdf.pages
                ],
            )

        ocr_result = ocr_pdf(file_path, language_hint=language_hint)
        if not ocr_result.text:
            partial_text = text_pdf.text if text_pdf.text else ""
            if partial_text:
                return _build_result(
                    text=partial_text,
                    page_count=max(text_pdf.page_count, ocr_result.page_count),
                    needs_ocr=True,
                    ocr_used=True,
                    status="Partially Extracted",
                    ocr_status="Failed",
                    ocr_engine="tesseract",
                    confidence_summary=ocr_result.confidence_summary,
                    warnings=ocr_result.warnings,
                    pages=[
                        PageText(
                            page_number=page.page_number,
                            text=page.text[:1200],
                            method=page.method,
                            confidence=page.confidence,
                        )
                        for page in ocr_result.pages
                    ],
                )
            raise OcrPipelineError("OCR did not recover usable text from the scanned PDF.")

        return _build_result(
            text=ocr_result.text,
            page_count=ocr_result.page_count,
            needs_ocr=True,
            ocr_used=True,
            status="OCR Completed",
            ocr_status="Completed",
            ocr_engine="tesseract",
            confidence_summary=ocr_result.confidence_summary,
            warnings=ocr_result.warnings,
            pages=[
                PageText(
                    page_number=page.page_number,
                    text=page.text[:1200],
                    method=page.method,
                    confidence=page.confidence,
                )
                for page in ocr_result.pages
            ],
        )

    if suffix in IMAGE_EXTENSIONS or resolved_mime.startswith("image/"):
        ocr_result = ocr_image_path(file_path, language_hint=language_hint)
        if not ocr_result.text:
            raise OcrPipelineError("OCR did not recover usable text from the supplied image.")
        return _build_result(
            text=ocr_result.text,
            page_count=1,
            needs_ocr=True,
            ocr_used=True,
            status="OCR Completed",
            ocr_status="Completed",
            ocr_engine=ocr_result.engine,
            confidence_summary=ocr_result.confidence,
            warnings=ocr_result.warnings,
            pages=[
                PageText(
                    page_number=1,
                    text=ocr_result.text[:1200],
                    method="ocr",
                    confidence=ocr_result.confidence,
                )
            ],
        )

    raise OcrPipelineError("This file type is not yet supported by the Phase 6 OCR pipeline.")
