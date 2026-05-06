from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.embedding_index_metadata import EmbeddingIndexMetadata
from app.models.enums import EmbeddingIndexStatus, RetrievalMode
from app.models.legal_source import LegalSource
from app.services.corpus.normalization import detect_language
from app.services.knowledge.embeddings import embed_texts
from app.services.ml.registry import read_json, retrieval_root, write_json


INDEX_NAME = "legal_source_chunks"


@dataclass(slots=True)
class SemanticIndexRecord:
    source_id: str
    chunk_id: str | None
    title: str
    short_title: str
    citation_label: str
    source_type: str
    category: str
    act_name: str
    section_label: str
    language: str
    source_origin: str
    source_url: str
    text: str
    excerpt: str


def _index_dir(index_name: str = INDEX_NAME) -> Path:
    path = retrieval_root() / index_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _records_path(index_name: str = INDEX_NAME) -> Path:
    return _index_dir(index_name) / "records.json"


def _vectors_path(index_name: str = INDEX_NAME) -> Path:
    return _index_dir(index_name) / "vectors.npy"


def _report_path(index_name: str = INDEX_NAME) -> Path:
    return _index_dir(index_name) / "report.json"


def _metadata_path(index_name: str = INDEX_NAME) -> Path:
    return _index_dir(index_name) / "metadata.json"


def _base_query():
    return select(LegalSource).options(selectinload(LegalSource.chunks))


def _build_records(db: Session) -> list[SemanticIndexRecord]:
    records: list[SemanticIndexRecord] = []
    for source in db.scalars(_base_query()).all():
        candidate_chunks = source.chunks or [None]
        for chunk in candidate_chunks:
            text = (chunk.text if chunk else source.content).strip()
            if not text:
                continue
            excerpt = " ".join(text.split())[:360]
            records.append(
                SemanticIndexRecord(
                    source_id=source.id,
                    chunk_id=chunk.id if chunk else None,
                    title=source.title,
                    short_title=source.short_title,
                    citation_label=source.citation_label,
                    source_type=source.source_type.value,
                    category=source.category,
                    act_name=source.act_name,
                    section_label=source.section_label,
                    language=source.language,
                    source_origin=str(source.metadata_json.get("originKind") or "Seeded Legal Source"),
                    source_url=str(source.metadata_json.get("sourceUrl") or ""),
                    text=text,
                    excerpt=excerpt,
                )
            )
    return records


def _corpus_version(records: list[SemanticIndexRecord]) -> str:
    return f"sources-{len(records)}"


def _corpus_signature(records: list[SemanticIndexRecord]) -> str:
    digest = sha256()
    for record in records:
        digest.update(record.source_id.encode("utf-8"))
        digest.update(b"|")
        digest.update((record.chunk_id or "").encode("utf-8"))
        digest.update(b"|")
        digest.update(record.text[:256].encode("utf-8", errors="ignore"))
        digest.update(b"\n")
    return digest.hexdigest()


def _stored_records_signature(index_name: str = INDEX_NAME) -> str:
    records_path = _records_path(index_name)
    if not records_path.exists():
        return ""
    raw_records = read_json(records_path)
    if not isinstance(raw_records, list):
        return ""
    digest = sha256()
    for item in raw_records:
        if not isinstance(item, dict):
            continue
        digest.update(str(item.get("source_id") or item.get("sourceId") or "").encode("utf-8"))
        digest.update(b"|")
        digest.update(str(item.get("chunk_id") or item.get("chunkId") or "").encode("utf-8"))
        digest.update(b"|")
        digest.update(str(item.get("text") or "")[:256].encode("utf-8", errors="ignore"))
        digest.update(b"\n")
    return digest.hexdigest()


def get_index_metadata(db: Session, *, index_name: str = INDEX_NAME) -> EmbeddingIndexMetadata | None:
    return db.scalar(select(EmbeddingIndexMetadata).where(EmbeddingIndexMetadata.name == index_name))


def _upsert_index_metadata(
    db: Session,
    *,
    index_name: str,
    status: EmbeddingIndexStatus,
    model_name: str,
    index_path: Path,
    corpus_version: str,
    vector_dimension: int,
    source_count: int,
    metadata_json: dict[str, Any],
) -> EmbeddingIndexMetadata:
    record = get_index_metadata(db, index_name=index_name)
    if record is None:
        record = EmbeddingIndexMetadata(
            name=index_name,
            retrieval_mode=RetrievalMode.SEMANTIC,
        )
        db.add(record)
        db.flush()
    record.model_name = model_name
    record.status = status
    record.corpus_version = corpus_version
    record.index_path = str(index_path)
    record.vector_dimension = vector_dimension
    record.source_count = source_count
    record.metadata_json = metadata_json
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def build_semantic_index(
    db: Session,
    *,
    model_name: str | None = None,
    index_name: str = INDEX_NAME,
) -> EmbeddingIndexMetadata:
    checkpoint = model_name or settings.ml_embedding_model_name
    records = _build_records(db)
    corpus_version = _corpus_version(records)
    corpus_signature = _corpus_signature(records)
    index_path = _index_dir(index_name)
    existing = get_index_metadata(db, index_name=index_name)

    if (
        existing is not None
        and existing.status == EmbeddingIndexStatus.READY
        and existing.model_name == checkpoint
        and existing.corpus_version == corpus_version
        and (
            str((existing.metadata_json or {}).get("sourceSignature") or "") == corpus_signature
            or _stored_records_signature(index_name) == corpus_signature
        )
        and _records_path(index_name).exists()
        and _vectors_path(index_name).exists()
    ):
        return existing

    _upsert_index_metadata(
        db,
        index_name=index_name,
        status=EmbeddingIndexStatus.BUILDING,
        model_name=checkpoint,
        index_path=index_path,
        corpus_version=corpus_version,
        vector_dimension=0,
        source_count=len(records),
        metadata_json={
            "stage": "encoding",
            "sourceSignature": corpus_signature,
        },
    )

    vectors = embed_texts([record.text for record in records], model_name=checkpoint)
    np.save(_vectors_path(index_name), vectors)
    write_json(_records_path(index_name), [asdict(record) for record in records])
    report = {
        "indexName": index_name,
        "modelName": checkpoint,
        "vectorDimension": int(vectors.shape[1]) if len(vectors.shape) == 2 and vectors.size else 0,
        "sourceCount": len(records),
        "sourceSignature": corpus_signature,
        "languageMix": {
            "English": sum(1 for record in records if record.language == "English"),
            "Urdu": sum(1 for record in records if record.language == "Urdu"),
            "Mixed": sum(1 for record in records if record.language == "Mixed"),
        },
    }
    write_json(_report_path(index_name), report)
    write_json(
        _metadata_path(index_name),
        {
            "indexName": index_name,
            "modelName": checkpoint,
            "corpusVersion": corpus_version,
            "sourceCount": len(records),
            "vectorDimension": report["vectorDimension"],
        },
    )
    return _upsert_index_metadata(
        db,
        index_name=index_name,
        status=EmbeddingIndexStatus.READY,
        model_name=checkpoint,
        index_path=index_path,
        corpus_version=corpus_version,
        vector_dimension=report["vectorDimension"],
        source_count=len(records),
        metadata_json=report,
    )


def load_semantic_index(
    db: Session,
    *,
    index_name: str = INDEX_NAME,
) -> tuple[EmbeddingIndexMetadata | None, list[SemanticIndexRecord], np.ndarray | None]:
    metadata = get_index_metadata(db, index_name=index_name)
    if metadata is None or metadata.status != EmbeddingIndexStatus.READY:
        return metadata, [], None

    records_path = _records_path(index_name)
    vectors_path = _vectors_path(index_name)
    if not records_path.exists() or not vectors_path.exists():
        return metadata, [], None

    raw_records = read_json(records_path)
    records = [SemanticIndexRecord(**item) for item in raw_records]
    vectors = np.load(vectors_path)
    return metadata, records, vectors


def embed_query(query: str, *, model_name: str | None = None) -> np.ndarray:
    return embed_texts([query], model_name=model_name)[0]


def describe_semantic_query(query: str) -> dict[str, Any]:
    return {
        "language": detect_language(query),
        "tokenLength": len(query.split()),
        "queryPreview": query[:180],
    }
