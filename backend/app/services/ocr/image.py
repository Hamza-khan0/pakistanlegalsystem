from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image
import pytesseract
from pytesseract import Output

from app.core.config import settings
from app.services.ocr.language import resolve_ocr_language
from app.services.ocr.postprocess import clean_extracted_text


pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


@dataclass(slots=True)
class ImageOcrResult:
    text: str
    confidence: float | None
    language: str
    engine: str
    warnings: list[str]


def _mean_confidence(data: dict) -> float | None:
    raw_values = data.get("conf", [])
    scores: list[float] = []
    for value in raw_values:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if parsed >= 0:
            scores.append(parsed)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 3)


def ocr_image(image: Image.Image, *, language_hint: str | None = None) -> ImageOcrResult:
    language, warnings = resolve_ocr_language(language_hint)
    data = pytesseract.image_to_data(image, lang=language, output_type=Output.DICT)
    text = clean_extracted_text(pytesseract.image_to_string(image, lang=language))
    return ImageOcrResult(
        text=text,
        confidence=_mean_confidence(data),
        language=language,
        engine="tesseract",
        warnings=warnings,
    )


def ocr_image_path(path: str | Path, *, language_hint: str | None = None) -> ImageOcrResult:
    with Image.open(path) as image:
        return ocr_image(image, language_hint=language_hint)


def ocr_image_bytes(payload: bytes, *, language_hint: str | None = None) -> ImageOcrResult:
    with Image.open(BytesIO(payload)) as image:
        return ocr_image(image, language_hint=language_hint)
