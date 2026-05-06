from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import ChamberTaskType, GroundingUsageType
from app.schemas.legal_sources import (
    CaseLegalBasisRead,
    GroundingSourceRead,
    LegalIngestionRead,
    LegalRetrievalRead,
    LegalRetrievalRequest,
    LegalSourceRead,
)
from app.services import cases as case_service
from app.services import legal_sources as legal_source_service
from app.services import runs as run_service
from app.services.corpus import build_corpus_entries
from app.services.grounding.provenance import (
    collect_case_legal_basis,
    list_artifact_grounding_links,
    list_run_grounding_links,
)
from app.services.intelligence_artifacts import get_artifact_or_none
from app.services.knowledge.retrieval import search_legal_sources, retrieve_case_legal_grounding
from app.services.serializers import serialize_grounding_link, serialize_legal_source
from app.utils.http import not_found

router = APIRouter()


@router.post("/legal-sources/ingest", response_model=LegalIngestionRead)
def ingest_legal_sources(
    reset_existing: bool = Query(default=False, alias="resetExisting"),
    db: Session = Depends(get_db),
) -> LegalIngestionRead:
    stats = legal_source_service.ingest_seed_corpus(db, reset_existing=reset_existing)
    build_corpus_entries(db, include_seeded=True, include_crawled=False)
    return LegalIngestionRead(
        sources_created=stats.sources_created,
        chunks_created=stats.chunks_created,
    )


@router.get("/legal-sources/search", response_model=LegalRetrievalRead)
def search_sources(
    q: str = Query(..., min_length=2),
    task_type: ChamberTaskType | None = Query(default=None, alias="taskType"),
    language: str | None = Query(default=None),
    limit: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
) -> LegalRetrievalRead:
    resolved_task_type = task_type or ChamberTaskType.RESEARCH_MEMO
    bundle = search_legal_sources(
        db,
        query=q,
        task_type=resolved_task_type,
        limit=limit,
        language=language,
    )
    return LegalRetrievalRead(
        query=bundle.query,
        status=bundle.status,
        summary=bundle.summary,
        sources=[
            GroundingSourceRead(
                source_id=source.source_id,
                chunk_id=source.chunk_id,
                title=source.title,
                short_title=source.short_title,
                citation_label=source.citation_label,
                source_type=source.source_type,
                category=source.category,
                act_name=source.act_name,
                section_label=source.section_label,
                language=source.language,
                source_origin=source.source_origin,
                source_url=source.source_url,
                excerpt=source.excerpt,
                relevance_score=source.relevance_score,
                usage_type=GroundingUsageType.RETRIEVED,
            )
            for source in bundle.sources
        ],
    )


@router.post("/legal-retrieval", response_model=LegalRetrievalRead)
def retrieve_legal_basis(
    payload: LegalRetrievalRequest = Body(...),
    db: Session = Depends(get_db),
) -> LegalRetrievalRead:
    if payload.case_id:
        case = case_service.get_case_or_none(db, payload.case_id)
        if not case:
            raise not_found("Case not found.")
        bundle = retrieve_case_legal_grounding(
            db,
            case=case,
            instruction=payload.query,
            task_type=payload.task_type or ChamberTaskType.RESEARCH_MEMO,
            focus_issue=None,
            limit=8,
            required=True,
            language=payload.language,
        )
    else:
        bundle = search_legal_sources(
            db,
            query=payload.query,
            task_type=payload.task_type or ChamberTaskType.RESEARCH_MEMO,
            limit=8,
            language=payload.language,
        )

    return LegalRetrievalRead(
        query=bundle.query,
        status=bundle.status,
        summary=bundle.summary,
        sources=[
            GroundingSourceRead(
                source_id=source.source_id,
                chunk_id=source.chunk_id,
                title=source.title,
                short_title=source.short_title,
                citation_label=source.citation_label,
                source_type=source.source_type,
                category=source.category,
                act_name=source.act_name,
                section_label=source.section_label,
                language=source.language,
                source_origin=source.source_origin,
                source_url=source.source_url,
                excerpt=source.excerpt,
                relevance_score=source.relevance_score,
                usage_type=GroundingUsageType.RETRIEVED,
            )
            for source in bundle.sources
        ],
    )


@router.get("/legal-sources/{source_id}", response_model=LegalSourceRead)
def get_legal_source(source_id: str, db: Session = Depends(get_db)) -> LegalSourceRead:
    source = legal_source_service.get_legal_source_or_none(db, source_id)
    if not source:
        raise not_found("Legal source not found.")
    return serialize_legal_source(source)


@router.get("/runs/{run_id}/sources", response_model=list[GroundingSourceRead])
def get_run_sources(run_id: str, db: Session = Depends(get_db)) -> list[GroundingSourceRead]:
    run = run_service.get_run_or_none(db, run_id)
    if not run:
        raise not_found("Run not found.")
    return [serialize_grounding_link(link) for link in list_run_grounding_links(db, run_id)]


@router.get("/intelligence/{artifact_id}/sources", response_model=list[GroundingSourceRead])
def get_artifact_sources(
    artifact_id: str,
    db: Session = Depends(get_db),
) -> list[GroundingSourceRead]:
    artifact = get_artifact_or_none(db, artifact_id)
    if not artifact:
        raise not_found("Intelligence artifact not found.")
    return [
        serialize_grounding_link(link)
        for link in list_artifact_grounding_links(db, artifact_id)
    ]


@router.get("/cases/{case_id}/legal-basis", response_model=CaseLegalBasisRead)
def get_case_legal_basis(case_id: str, db: Session = Depends(get_db)) -> CaseLegalBasisRead:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    links = collect_case_legal_basis(db, case_id)
    return CaseLegalBasisRead(
        case_id=case_id,
        sources=[serialize_grounding_link(link) for link in links],
    )
