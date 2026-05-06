from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.corpus.normalization import clean_unicode_text, detect_language, normalize_text
from app.services.ocr.pipeline import OcrPipelineError, process_file


TEXT_KEYS = (
    "text",
    "raw_text",
    "normalized_text",
    "judgment",
    "judgement",
    "content",
    "body",
    "full_text",
    "case_text",
    "description",
)
TITLE_KEYS = ("title", "case_title", "name", "caption", "parties")
WATERMARK_PATTERNS = (
    re.compile(r"downloaded\s+from\s+.*", re.IGNORECASE),
    re.compile(r"page\s+\d+\s+of\s+\d+", re.IGNORECASE),
    re.compile(r"www\.[^\s]+", re.IGNORECASE),
)


@dataclass(slots=True)
class NormalizedTier1Record:
    source_type: str
    source_name: str
    external_id: str
    file_path: str
    title: str
    raw_text: str
    normalized_text: str
    language: str
    document_type: str = "Judgment"
    court: str = ""
    date: str = ""
    citation: str = ""
    case_number: str = ""
    parties: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def clean_tier1_text(value: str) -> str:
    cleaned_lines: list[str] = []
    for line in (value or "").splitlines():
        stripped = clean_unicode_text(line)
        if not stripped:
            continue
        if any(pattern.fullmatch(stripped) for pattern in WATERMARK_PATTERNS):
            continue
        cleaned_lines.append(stripped)
    return clean_unicode_text("\n".join(cleaned_lines))


def _first_text(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def _record_from_row(
    row: dict[str, Any],
    *,
    source_type: str,
    source_name: str,
    file_path: Path,
    row_index: int,
) -> NormalizedTier1Record | None:
    raw_text = clean_tier1_text(_first_text(row, TEXT_KEYS))
    if not raw_text:
        return None
    title = clean_unicode_text(_first_text(row, TITLE_KEYS)) or file_path.stem
    external_id = str(row.get("id") or row.get("external_id") or row.get("case_id") or f"{file_path.name}:{row_index}")
    normalized = normalize_text(raw_text)
    return NormalizedTier1Record(
        source_type=source_type,
        source_name=source_name,
        external_id=external_id,
        file_path=str(file_path),
        title=title[:500],
        raw_text=raw_text,
        normalized_text=normalized,
        language=str(row.get("language") or detect_language(raw_text)),
        document_type=str(row.get("document_type") or row.get("type") or "Judgment"),
        court=str(row.get("court") or row.get("forum") or ""),
        date=str(row.get("date") or row.get("judgment_date") or row.get("decision_date") or ""),
        citation=str(row.get("citation") or row.get("citation_label") or ""),
        case_number=str(row.get("case_number") or row.get("case_no") or ""),
        parties=str(row.get("parties") or row.get("party_names") or ""),
        metadata={key: value for key, value in row.items() if key not in set(TEXT_KEYS)},
    )


def _read_json_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "data", "documents", "judgments"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def _read_jsonl_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
    return records


def _read_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        return list(csv.DictReader(handle))


def records_from_file(
    path: str | Path,
    *,
    source_type: str,
    source_name: str,
) -> tuple[list[NormalizedTier1Record], list[str]]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    warnings: list[str] = []
    records: list[NormalizedTier1Record] = []

    try:
        if suffix == ".json":
            raw_rows = _read_json_records(file_path)
        elif suffix == ".jsonl":
            raw_rows = _read_jsonl_records(file_path)
        elif suffix == ".csv":
            raw_rows = _read_csv_records(file_path)
        elif suffix == ".txt":
            raw_rows = [{"title": file_path.stem, "text": file_path.read_text(encoding="utf-8", errors="ignore")}]
        elif suffix == ".pdf":
            extracted = process_file(file_path)
            raw_rows = [
                {
                    "title": file_path.stem,
                    "text": extracted.text,
                    "language": extracted.language,
                    "ocr_confidence": extracted.confidence_summary,
                    "page_count": extracted.page_count,
                }
            ]
        else:
            return [], [f"Unsupported file type: {file_path.name}"]
    except (OcrPipelineError, OSError, json.JSONDecodeError) as exc:
        return [], [f"{file_path.name}: {exc}"]

    for index, row in enumerate(raw_rows, start=1):
        record = _record_from_row(
            row,
            source_type=source_type,
            source_name=source_name,
            file_path=file_path,
            row_index=index,
        )
        if record is None:
            warnings.append(f"{file_path.name} row {index}: no usable text")
            continue
        records.append(record)
    return records, warnings
