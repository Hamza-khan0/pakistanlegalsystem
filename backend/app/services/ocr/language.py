from __future__ import annotations

from functools import lru_cache
import subprocess

from app.core.config import settings
from app.services.corpus.normalization import detect_language


@lru_cache(maxsize=1)
def installed_tesseract_languages() -> set[str]:
    try:
        command = [settings.tesseract_cmd, "--list-langs"]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except Exception:
        return set()

    languages: set[str] = set()
    for line in result.stdout.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("List of available languages"):
            continue
        languages.add(cleaned)
    return languages


def resolve_ocr_language(language_hint: str | None, text: str = "") -> tuple[str, list[str]]:
    installed = installed_tesseract_languages()
    warnings: list[str] = []
    detected = detect_language(text) if text else "Unknown"
    resolved_hint = (language_hint or detected or "English").strip().casefold()

    if resolved_hint == "urdu" and "urd" in installed:
        return "urd", warnings
    if resolved_hint == "mixed" and {"eng", "urd"}.issubset(installed):
        return "eng+urd", warnings
    if resolved_hint in {"mixed", "urdu"} and "urd" not in installed:
        warnings.append("Urdu OCR language pack is not installed; falling back to English OCR.")
    if "eng" in installed:
        return "eng", warnings
    if installed:
        return sorted(installed)[0], warnings
    warnings.append("Tesseract language data was not available for OCR.")
    return "eng", warnings
