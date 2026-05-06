from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.corpus_entry import CorpusEntry
from app.models.crawled_document import CrawledDocument
from app.models.enums import CorpusSourceKind, DatasetSplit, LegalSourceType
from app.models.legal_source import LegalSource
from app.models.legal_source_chunk import LegalSourceChunk
from app.services.corpus.chunking import chunk_corpus_text
from app.services.corpus.normalization import detect_language, normalize_text, unique_tokens


@dataclass(slots=True)
class CorpusBuildStats:
    legal_sources_upserted: int = 0
    corpus_entries_upserted: int = 0
    crawled_documents_promoted: int = 0


def _stable_split(identifier: str) -> DatasetSplit:
    score = int(sha256(identifier.encode("utf-8")).hexdigest(), 16) % 100
    if score < 80:
        return DatasetSplit.TRAIN
    if score < 90:
        return DatasetSplit.VALIDATION
    return DatasetSplit.TEST


def _legal_source_type_from_document(document: CrawledDocument) -> LegalSourceType:
    lowered_type = document.document_type.casefold()
    metadata_json = document.metadata_json or {}
    category = str(metadata_json.get("category") or "").casefold()
    if "case" in lowered_type or "judgment" in lowered_type or "court" in category:
        return LegalSourceType.CASE_LAW
    if "rule" in lowered_type or "rules" in category:
        return LegalSourceType.RULES
    if "manual" in lowered_type:
        return LegalSourceType.MANUAL
    return LegalSourceType.STATUTE


def _upsert_chunks(db: Session, source: LegalSource) -> int:
    db.query(LegalSourceChunk).filter(LegalSourceChunk.source_id == source.id).delete()
    chunks = chunk_corpus_text(
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
                metadata_json={"language": chunk.language, "sourceTitle": source.title},
            )
        )
    return len(chunks)


def upsert_legal_source_from_crawled_document(
    db: Session,
    document: CrawledDocument,
) -> tuple[LegalSource, int, bool]:
    identifier = document.legal_source_id or f"crawled-{document.id}"
    source = db.scalar(select(LegalSource).where(LegalSource.id == identifier))
    created = source is None
    if source is None:
        source = LegalSource(id=identifier)
        db.add(source)

    source_metadata = source.metadata_json or {}
    document_metadata = document.metadata_json or {}
    metadata_json = {
        **source_metadata,
        **document_metadata,
        "originKind": "Crawled Corpus",
        "crawlSourceId": document.source_id,
        "crawlSourceName": document.source.name if document.source else "",
        "sourceUrl": document.source_url,
        "documentType": document.document_type,
        "keywords": unique_tokens(" ".join([document.title, document.document_type, document.extracted_text[:2000]])),
    }
    source.source_type = _legal_source_type_from_document(document)
    source.title = document.title
    source.short_title = str(document_metadata.get("shortTitle") or document.title[:180])
    source.jurisdiction = document.jurisdiction
    source.category = str(document_metadata.get("category") or document.document_type)
    source.act_name = str(document_metadata.get("actName") or document_metadata.get("act_name") or "")
    source.section_label = str(document_metadata.get("sectionLabel") or document_metadata.get("section_label") or "")
    source.section_number = str(document_metadata.get("sectionNumber") or "")
    source.order_rule_label = str(document_metadata.get("orderRuleLabel") or "")
    source.year = None
    source.language = document.language_detected or document.language or detect_language(document.extracted_text)
    source.citation_label = str(document_metadata.get("citationLabel") or document.title)
    source.content = document.extracted_text
    source.normalized_text = normalize_text(document.extracted_text)
    source.metadata_json = metadata_json
    db.flush()

    chunk_count = _upsert_chunks(db, source)
    document.legal_source_id = source.id
    db.add(document)
    return source, chunk_count, created


def _upsert_corpus_entry(
    db: Session,
    *,
    source_kind: CorpusSourceKind,
    legal_source: LegalSource | None,
    crawled_document: CrawledDocument | None,
    title: str,
    language: str,
    normalized_text: str,
    chunk_count: int,
    metadata_json: dict,
) -> tuple[CorpusEntry, bool]:
    query = select(CorpusEntry).where(CorpusEntry.source_kind == source_kind)
    if legal_source is not None:
        query = query.where(CorpusEntry.legal_source_id == legal_source.id)
    if crawled_document is not None:
        query = query.where(CorpusEntry.crawled_document_id == crawled_document.id)
    entry = db.scalar(query)
    created = entry is None
    if entry is None:
        entry = CorpusEntry(source_kind=source_kind)
        db.add(entry)

    entry.crawled_document_id = crawled_document.id if crawled_document else None
    entry.legal_source_id = legal_source.id if legal_source else None
    entry.title = title
    entry.language = language
    entry.normalized_text = normalized_text
    entry.chunk_count = chunk_count
    entry.ready_for_retrieval = bool(normalized_text.strip())
    entry.ready_for_training = bool(normalized_text.strip())
    entry.dataset_split = _stable_split(entry.legal_source_id or entry.crawled_document_id or title)
    entry.metadata_json = metadata_json
    return entry, created


def upsert_corpus_entry_for_legal_source(db: Session, source: LegalSource) -> tuple[CorpusEntry, bool]:
    chunk_count = len(source.chunks)
    source_metadata = source.metadata_json or {}
    return _upsert_corpus_entry(
        db,
        source_kind=CorpusSourceKind.SEEDED_LEGAL_SOURCE,
        legal_source=source,
        crawled_document=None,
        title=source.title,
        language=source.language,
        normalized_text=source.normalized_text,
        chunk_count=chunk_count,
        metadata_json={
            "originKind": source_metadata.get("originKind", "Seeded Legal Source"),
            "sourceType": source.source_type.value,
            "citationLabel": source.citation_label,
            "category": source.category,
        },
    )


def upsert_corpus_entry_for_crawled_document(
    db: Session,
    document: CrawledDocument,
    *,
    legal_source: LegalSource,
    chunk_count: int,
) -> tuple[CorpusEntry, bool]:
    return _upsert_corpus_entry(
        db,
        source_kind=CorpusSourceKind.CRAWLED_DOCUMENT,
        legal_source=legal_source,
        crawled_document=document,
        title=document.title,
        language=document.language_detected or document.language,
        normalized_text=document.normalized_text,
        chunk_count=chunk_count,
        metadata_json={
            "originKind": "Crawled Corpus",
            "sourceType": legal_source.source_type.value,
            "citationLabel": legal_source.citation_label,
            "documentType": document.document_type,
            "sourceUrl": document.source_url,
            "crawlSourceName": document.source.name if document.source else "",
        },
    )


def build_corpus_entries(
    db: Session,
    *,
    include_seeded: bool = True,
    include_crawled: bool = True,
) -> CorpusBuildStats:
    stats = CorpusBuildStats()
    if include_seeded:
        for source in db.scalars(select(LegalSource)).all():
            if source.metadata_json.get("originKind") == "Crawled Corpus":
                continue
            _, created = upsert_corpus_entry_for_legal_source(db, source)
            if created:
                stats.corpus_entries_upserted += 1

    if include_crawled:
        documents = db.scalars(
            select(CrawledDocument).where(CrawledDocument.extracted_text != "")
        ).all()
        for document in documents:
            legal_source, chunk_count, created_source = upsert_legal_source_from_crawled_document(db, document)
            _, created_entry = upsert_corpus_entry_for_crawled_document(
                db,
                document,
                legal_source=legal_source,
                chunk_count=chunk_count,
            )
            stats.crawled_documents_promoted += 1
            if created_source:
                stats.legal_sources_upserted += 1
            if created_entry:
                stats.corpus_entries_upserted += 1

    db.commit()
    return stats
