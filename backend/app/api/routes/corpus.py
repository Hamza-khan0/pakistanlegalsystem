from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corpus_entry import CorpusEntry
from app.services.corpus import build_corpus_entries, export_corpus_datasets
from app.schemas.corpus import CorpusBuildRead, CorpusEntryRead, CorpusExportRead
from app.services.serializers import serialize_corpus_entry

router = APIRouter()


@router.get("/corpus/entries", response_model=list[CorpusEntryRead])
def get_corpus_entries(
    language: str | None = Query(default=None),
    source_kind: str | None = Query(default=None, alias="sourceKind"),
    ready_for_training: bool | None = Query(default=None, alias="readyForTraining"),
    db: Session = Depends(get_db),
) -> list[CorpusEntryRead]:
    query = select(CorpusEntry).order_by(CorpusEntry.updated_at.desc())
    if language:
        query = query.where(CorpusEntry.language == language)
    if source_kind:
        query = query.where(CorpusEntry.source_kind == source_kind)
    if ready_for_training is not None:
        query = query.where(CorpusEntry.ready_for_training == ready_for_training)
    entries = list(db.scalars(query).all())
    return [serialize_corpus_entry(entry) for entry in entries]


@router.post("/corpus/build", response_model=CorpusBuildRead, status_code=status.HTTP_201_CREATED)
def build_corpus(db: Session = Depends(get_db)) -> CorpusBuildRead:
    stats = build_corpus_entries(db)
    return CorpusBuildRead(
        legal_sources_upserted=stats.legal_sources_upserted,
        corpus_entries_upserted=stats.corpus_entries_upserted,
        crawled_documents_promoted=stats.crawled_documents_promoted,
    )


@router.post("/corpus/export", response_model=CorpusExportRead, status_code=status.HTTP_201_CREATED)
def export_corpus(db: Session = Depends(get_db)) -> CorpusExportRead:
    stats = export_corpus_datasets(db)
    return CorpusExportRead(
        output_dir=stats.output_dir,
        retrieval_records=stats.retrieval_records,
        classification_records=stats.classification_records,
        bilingual_records=stats.bilingual_records,
        files=stats.files,
    )
