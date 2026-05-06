from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.enums import LegalSourceType
from app.models.grounding_link import GroundingLink
from app.models.legal_source import LegalSource
from app.models.legal_source_chunk import LegalSourceChunk
from app.services.knowledge.chunking import chunk_legal_source
from app.services.knowledge.normalization import normalize_text, unique_tokens


LEGAL_SOURCE_DIR = Path(__file__).resolve().parents[2] / "seed" / "legal_sources"


@dataclass(slots=True)
class IngestionStats:
    sources_created: int = 0
    chunks_created: int = 0


def _source_records_from_path(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def load_seed_legal_source_records(directory: Path | None = None) -> list[dict[str, Any]]:
    search_dir = directory or LEGAL_SOURCE_DIR
    records: list[dict[str, Any]] = []
    for path in sorted(search_dir.glob("*.json")):
        records.extend(_source_records_from_path(path))
    return records


def _build_normalized_source_text(record: dict[str, Any]) -> str:
    metadata = record.get("metadata_json")
    keywords = metadata.get("keywords", []) if isinstance(metadata, dict) else []
    pieces = [
        str(record.get("title") or ""),
        str(record.get("short_title") or ""),
        str(record.get("citation_label") or ""),
        str(record.get("act_name") or ""),
        str(record.get("section_label") or ""),
        str(record.get("content") or ""),
        " ".join(str(keyword) for keyword in keywords),
    ]
    return normalize_text(" ".join(piece for piece in pieces if piece))


def ingest_legal_source_records(
    db: Session,
    records: list[dict[str, Any]],
    *,
    reset_existing: bool = False,
) -> IngestionStats:
    if reset_existing:
        db.execute(delete(GroundingLink))
        db.execute(delete(LegalSourceChunk))
        db.execute(delete(LegalSource))
        db.commit()

    stats = IngestionStats()
    for record in records:
        source_id = str(record.get("id") or "")
        existing = db.scalar(select(LegalSource).where(LegalSource.id == source_id)) if source_id else None
        if existing:
            db.execute(delete(LegalSourceChunk).where(LegalSourceChunk.source_id == existing.id))
            source = existing
        else:
            source = LegalSource()
            if source_id:
                source.id = source_id
            db.add(source)
            stats.sources_created += 1

        metadata_json = dict(record.get("metadata_json") or {})
        metadata_json.setdefault("keywords", unique_tokens(" ".join(metadata_json.get("keywords", []))))

        source.source_type = LegalSourceType(str(record["source_type"]))
        source.title = str(record.get("title") or "")
        source.short_title = str(record.get("short_title") or "")
        source.jurisdiction = str(record.get("jurisdiction") or "Pakistan")
        source.category = str(record.get("category") or "")
        source.act_name = str(record.get("act_name") or "")
        source.section_label = str(record.get("section_label") or "")
        source.section_number = str(record.get("section_number") or "")
        source.order_rule_label = str(record.get("order_rule_label") or "")
        source.year = record.get("year")
        source.language = str(record.get("language") or "English")
        source.citation_label = str(record.get("citation_label") or source.title)
        source.content = str(record.get("content") or "")
        source.normalized_text = _build_normalized_source_text(record)
        source.metadata_json = metadata_json
        db.flush()

        chunks = chunk_legal_source(
            content=source.content,
            heading=source.section_label or source.short_title or source.title,
        )
        for chunk in chunks:
            db.add(
                LegalSourceChunk(
                    source_id=source.id,
                    chunk_index=chunk.chunk_index,
                    heading=chunk.heading,
                    text=chunk.text,
                    normalized_text=chunk.normalized_text,
                    token_count=chunk.token_count,
                    metadata_json={"sourceTitle": source.title},
                )
            )
            stats.chunks_created += 1

    db.commit()
    return stats


def ingest_seed_legal_sources(
    db: Session,
    *,
    reset_existing: bool = False,
    directory: Path | None = None,
) -> IngestionStats:
    records = load_seed_legal_source_records(directory)
    return ingest_legal_source_records(db, records, reset_existing=reset_existing)
