from __future__ import annotations

from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crawled_document import CrawledDocument


def build_duplicate_hash(*parts: str) -> str:
    cleaned = "||".join(part.strip().casefold() for part in parts if part and part.strip())
    return sha256(cleaned.encode("utf-8")).hexdigest()


def find_existing_document(
    db: Session,
    *,
    source_id: str,
    source_url: str,
    duplicate_hash: str,
) -> CrawledDocument | None:
    return db.scalar(
        select(CrawledDocument).where(
            CrawledDocument.source_id == source_id,
            (CrawledDocument.source_url == source_url) | (CrawledDocument.duplicate_hash == duplicate_hash),
        )
    )
