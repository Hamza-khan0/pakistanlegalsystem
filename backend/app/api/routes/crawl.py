from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.crawl import (
    CrawlJobRead,
    CrawlRunRequest,
    CrawledDocumentRead,
    CrawlSourceCreate,
    CrawlSourceRead,
)
from app.services import crawled_documents as crawled_document_service
from app.services.crawling.registry import (
    create_or_update_crawl_source,
    get_crawl_source_or_none,
    list_crawl_sources,
)
from app.services.crawling.runner import get_crawl_job_or_none, list_crawl_jobs, run_crawl_job
from app.services.serializers import (
    serialize_crawl_job,
    serialize_crawl_source,
    serialize_crawled_document,
)
from app.utils.http import not_found

router = APIRouter()


@router.get("/crawl/sources", response_model=list[CrawlSourceRead])
def get_crawl_sources(db: Session = Depends(get_db)) -> list[CrawlSourceRead]:
    return [serialize_crawl_source(source) for source in list_crawl_sources(db)]


@router.post("/crawl/sources", response_model=CrawlSourceRead, status_code=status.HTTP_201_CREATED)
def create_crawl_source(
    payload: CrawlSourceCreate,
    db: Session = Depends(get_db),
) -> CrawlSourceRead:
    source = create_or_update_crawl_source(db, payload.model_dump())
    return serialize_crawl_source(source)


@router.post("/crawl/run", response_model=CrawlJobRead, status_code=status.HTTP_201_CREATED)
def create_crawl_run(
    payload: CrawlRunRequest = Body(...),
    db: Session = Depends(get_db),
) -> CrawlJobRead:
    source = get_crawl_source_or_none(db, payload.source_id)
    if not source:
        raise not_found("Crawl source not found.")
    job = run_crawl_job(db, source=source)
    return serialize_crawl_job(job)


@router.get("/crawl/jobs", response_model=list[CrawlJobRead])
def get_jobs(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CrawlJobRead]:
    return [serialize_crawl_job(job) for job in list_crawl_jobs(db, limit=limit)]


@router.get("/crawl/jobs/{job_id}", response_model=CrawlJobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> CrawlJobRead:
    job = get_crawl_job_or_none(db, job_id)
    if not job:
        raise not_found("Crawl job not found.")
    return serialize_crawl_job(job)


@router.get("/crawled-documents", response_model=list[CrawledDocumentRead])
def get_crawled_documents(
    q: str | None = Query(default=None),
    source_id: str | None = Query(default=None, alias="sourceId"),
    processing_status: str | None = Query(default=None, alias="processingStatus"),
    db: Session = Depends(get_db),
) -> list[CrawledDocumentRead]:
    documents = crawled_document_service.list_crawled_documents(
        db,
        q=q,
        source_id=source_id,
        processing_status=processing_status,
    )
    return [serialize_crawled_document(document) for document in documents]


@router.get("/crawled-documents/{document_id}", response_model=CrawledDocumentRead)
def get_crawled_document(document_id: str, db: Session = Depends(get_db)) -> CrawledDocumentRead:
    document = crawled_document_service.get_crawled_document_or_none(db, document_id)
    if not document:
        raise not_found("Crawled document not found.")
    return serialize_crawled_document(document)


@router.post("/crawled-documents/{document_id}/process", response_model=CrawledDocumentRead)
def process_crawled_document(document_id: str, db: Session = Depends(get_db)) -> CrawledDocumentRead:
    document = crawled_document_service.get_crawled_document_or_none(db, document_id)
    if not document:
        raise not_found("Crawled document not found.")
    processed = crawled_document_service.process_crawled_document(db, document, force_ocr=False)
    return serialize_crawled_document(processed)


@router.post("/crawled-documents/{document_id}/ocr", response_model=CrawledDocumentRead)
def force_ocr_crawled_document(document_id: str, db: Session = Depends(get_db)) -> CrawledDocumentRead:
    document = crawled_document_service.get_crawled_document_or_none(db, document_id)
    if not document:
        raise not_found("Crawled document not found.")
    processed = crawled_document_service.process_crawled_document(db, document, force_ocr=True)
    return serialize_crawled_document(processed)


@router.get("/crawled-documents/{document_id}/extraction", response_model=CrawledDocumentRead)
def get_crawled_document_extraction(document_id: str, db: Session = Depends(get_db)) -> CrawledDocumentRead:
    document = crawled_document_service.get_crawled_document_or_none(db, document_id)
    if not document:
        raise not_found("Crawled document not found.")
    return serialize_crawled_document(document)
