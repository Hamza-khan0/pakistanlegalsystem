from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import fitz
from pypdf import PdfReader

from app.services.ocr.image import ocr_image_bytes
from app.services.ocr.postprocess import clean_extracted_text


@dataclass(slots=True)
class PdfPageExtraction:
    page_number: int
    text: str
    method: str
    confidence: float | None = None


@dataclass(slots=True)
class PdfExtractionResult:
    text: str
    page_count: int
    method: str
    ocr_used: bool
    confidence_summary: float | None
    warnings: list[str] = field(default_factory=list)
    pages: list[PdfPageExtraction] = field(default_factory=list)


def extract_text_pdf(path: str | Path) -> PdfExtractionResult:
    reader = PdfReader(str(path))
    pages: list[PdfPageExtraction] = []
    page_texts: list[str] = []
    for index, page in enumerate(reader.pages):
        text = clean_extracted_text(page.extract_text() or "")
        pages.append(PdfPageExtraction(page_number=index + 1, text=text, method="text"))
        if text:
            page_texts.append(text)
    extracted = clean_extracted_text("\n\n".join(page_texts))
    return PdfExtractionResult(
        text=extracted,
        page_count=len(reader.pages),
        method="text",
        ocr_used=False,
        confidence_summary=None,
        pages=pages,
    )


def ocr_pdf(path: str | Path, *, language_hint: str | None = None) -> PdfExtractionResult:
    document = fitz.open(str(path))
    pages: list[PdfPageExtraction] = []
    page_texts: list[str] = []
    confidences: list[float] = []
    warnings: list[str] = []
    try:
        for index in range(document.page_count):
            page = document.load_page(index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image_bytes = pixmap.tobytes("png")
            ocr_result = ocr_image_bytes(image_bytes, language_hint=language_hint)
            warnings.extend(ocr_result.warnings)
            text = clean_extracted_text(ocr_result.text)
            pages.append(
                PdfPageExtraction(
                    page_number=index + 1,
                    text=text,
                    method="ocr",
                    confidence=ocr_result.confidence,
                )
            )
            if text:
                page_texts.append(text)
            if ocr_result.confidence is not None:
                confidences.append(ocr_result.confidence)
    finally:
        document.close()

    confidence_summary = round(sum(confidences) / len(confidences), 3) if confidences else None
    return PdfExtractionResult(
        text=clean_extracted_text("\n\n".join(page_texts)),
        page_count=len(pages),
        method="ocr",
        ocr_used=True,
        confidence_summary=confidence_summary,
        warnings=warnings,
        pages=pages,
    )
