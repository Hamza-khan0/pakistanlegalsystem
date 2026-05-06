from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.legal_source import LegalSource
from app.services.knowledge.ingestion import IngestionStats, ingest_seed_legal_sources


def get_legal_source_or_none(db: Session, source_id: str) -> LegalSource | None:
    return db.scalar(
        select(LegalSource)
        .options(selectinload(LegalSource.chunks))
        .where(LegalSource.id == source_id)
    )


def list_legal_sources(db: Session, *, limit: int = 100) -> list[LegalSource]:
    return list(
        db.scalars(
            select(LegalSource)
            .options(selectinload(LegalSource.chunks))
            .order_by(LegalSource.title)
            .limit(limit)
        ).all()
    )


def ingest_seed_corpus(db: Session, *, reset_existing: bool = False) -> IngestionStats:
    return ingest_seed_legal_sources(db, reset_existing=reset_existing)
