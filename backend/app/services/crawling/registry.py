from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.crawl_source import CrawlSource
from app.models.enums import CrawlMode, CrawlSourceType


REGISTRY_PATH = Path(settings.crawl_seed_dir) / "registry.json"


def _resolve_entry_url(path_value: str, *, base_dir: Path) -> str:
    parsed = urlparse(path_value)
    if parsed.scheme in {"http", "https", "file"}:
        return path_value
    absolute = (base_dir / path_value).resolve()
    return absolute.as_uri()


def load_seed_crawl_source_records() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else []


def register_crawl_sources(db: Session, records: list[dict]) -> list[CrawlSource]:
    base_dir = Path(settings.crawl_seed_dir)
    registered: list[CrawlSource] = []
    for record in records:
        name = str(record.get("name") or "").strip()
        if not name:
            continue
        source = db.scalar(select(CrawlSource).where(CrawlSource.name == name))
        if source is None:
            source = CrawlSource(name=name)
            db.add(source)

        config_json = dict(record.get("config") or {})
        entry_urls = [
            _resolve_entry_url(str(value), base_dir=base_dir)
            for value in config_json.get("entryUrls", [])
        ]
        config_json["entryUrls"] = entry_urls

        source.source_type = CrawlSourceType(str(record.get("sourceType") or "HTML"))
        source.base_url = str(record.get("baseUrl") or (entry_urls[0] if entry_urls else ""))
        source.allowed_domains = list(record.get("allowedDomains") or [])
        source.crawl_mode = CrawlMode(str(record.get("crawlMode") or "Index"))
        source.language_hint = str(record.get("languageHint") or "English")
        source.category = str(record.get("category") or "")
        source.is_active = bool(record.get("isActive", True))
        source.config_json = config_json
        registered.append(source)

    db.commit()
    return list(
        db.scalars(select(CrawlSource).order_by(CrawlSource.name)).all()
    )


def create_or_update_crawl_source(db: Session, payload: dict) -> CrawlSource:
    name = str(payload.get("name") or "").strip()
    source = db.scalar(select(CrawlSource).where(CrawlSource.name == name)) if name else None
    if source is None:
        source = CrawlSource(name=name)
        db.add(source)

    source.source_type = CrawlSourceType(str(payload.get("source_type") or payload.get("sourceType") or "HTML"))
    source.base_url = str(payload.get("base_url") or payload.get("baseUrl") or "")
    source.allowed_domains = list(payload.get("allowed_domains") or payload.get("allowedDomains") or [])
    source.crawl_mode = CrawlMode(str(payload.get("crawl_mode") or payload.get("crawlMode") or "Index"))
    source.language_hint = str(payload.get("language_hint") or payload.get("languageHint") or "English")
    source.category = str(payload.get("category") or "")
    source.is_active = bool(payload.get("is_active") if "is_active" in payload else payload.get("isActive", True))
    source.config_json = dict(payload.get("config_json") or payload.get("configJson") or {})

    db.commit()
    db.refresh(source)
    return source


def register_seed_crawl_sources(db: Session) -> list[CrawlSource]:
    return register_crawl_sources(db, load_seed_crawl_source_records())


def list_crawl_sources(db: Session) -> list[CrawlSource]:
    return list(db.scalars(select(CrawlSource).order_by(CrawlSource.name)).all())


def get_crawl_source_or_none(db: Session, source_id: str) -> CrawlSource | None:
    return db.scalar(select(CrawlSource).where(CrawlSource.id == source_id))
