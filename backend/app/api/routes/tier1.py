from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.enums import MlTaskName
from app.models.tier1_document import Tier1Document
from app.models.tier1_label import Tier1Label
from app.schemas.tier1 import (
    Tier1DatasetBuildResult,
    Tier1DocumentRead,
    Tier1ExportResult,
    Tier1ImportResult,
    Tier1LabelRead,
    Tier1LabelUpdate,
    Tier1ReadinessRead,
    Tier1ReportRead,
)
from app.services.tier1_data.dataset_builder import build_tier1_datasets, tier1_readiness
from app.services.tier1_data.export_bundle import export_training_bundle
from app.services.tier1_data.importer import import_huggingface, import_kaggle, import_local
from app.services.tier1_data.reports import tier1_report
from app.utils.http import not_found

router = APIRouter()


def _document_read(document: Tier1Document) -> Tier1DocumentRead:
    return Tier1DocumentRead.model_validate(document)


def _label_read(label: Tier1Label) -> Tier1LabelRead:
    return Tier1LabelRead(
        id=label.id,
        document_id=label.document_id,
        document_title=label.document.title if label.document else "",
        task_name=label.task_name,
        label=label.label,
        label_source=label.label_source,
        confidence_score=label.confidence_score,
        evidence_text=label.evidence_text,
        rule_name=label.rule_name,
        needs_review=label.needs_review,
        reviewed=label.reviewed,
        reviewer_note=label.reviewer_note,
        created_at=label.created_at,
        updated_at=label.updated_at,
    )


@router.post("/tier1/import/local", response_model=Tier1ImportResult, status_code=status.HTTP_201_CREATED)
def import_local_tier1(db: Session = Depends(get_db)) -> Tier1ImportResult:
    return Tier1ImportResult(**import_local(db))


@router.post("/tier1/import/kaggle", response_model=Tier1ImportResult)
def import_kaggle_tier1(db: Session = Depends(get_db)) -> Tier1ImportResult:
    return Tier1ImportResult(**import_kaggle(db))


@router.post("/tier1/import/huggingface", response_model=Tier1ImportResult)
def import_huggingface_tier1(db: Session = Depends(get_db)) -> Tier1ImportResult:
    return Tier1ImportResult(**import_huggingface(db))


@router.get("/tier1/documents", response_model=list[Tier1DocumentRead])
def list_tier1_documents(
    source_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Tier1DocumentRead]:
    statement = select(Tier1Document).order_by(Tier1Document.created_at.desc()).limit(limit)
    if source_type:
        statement = select(Tier1Document).where(Tier1Document.source_type == source_type).order_by(Tier1Document.created_at.desc()).limit(limit)
    return [_document_read(document) for document in db.scalars(statement).all()]


@router.get("/tier1/documents/{document_id}", response_model=Tier1DocumentRead)
def get_tier1_document(document_id: str, db: Session = Depends(get_db)) -> Tier1DocumentRead:
    document = db.get(Tier1Document, document_id)
    if document is None:
        raise not_found("Tier 1 document not found.")
    return _document_read(document)


@router.get("/tier1/labels", response_model=list[Tier1LabelRead])
def list_tier1_labels(
    task_name: MlTaskName | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Tier1LabelRead]:
    statement = select(Tier1Label).options(selectinload(Tier1Label.document)).order_by(Tier1Label.created_at.desc()).limit(limit)
    if task_name:
        statement = (
            select(Tier1Label)
            .where(Tier1Label.task_name == task_name)
            .options(selectinload(Tier1Label.document))
            .order_by(Tier1Label.created_at.desc())
            .limit(limit)
        )
    return [_label_read(label) for label in db.scalars(statement).all()]


@router.get("/tier1/labels/audit", response_model=list[Tier1LabelRead])
def list_tier1_audit_labels(
    task_name: MlTaskName | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Tier1LabelRead]:
    statement = (
        select(Tier1Label)
        .where(Tier1Label.needs_review.is_(True))
        .options(selectinload(Tier1Label.document))
        .order_by(Tier1Label.confidence_score.asc(), Tier1Label.created_at.desc())
        .limit(limit)
    )
    if task_name:
        statement = (
            select(Tier1Label)
            .where(Tier1Label.needs_review.is_(True), Tier1Label.task_name == task_name)
            .options(selectinload(Tier1Label.document))
            .order_by(Tier1Label.confidence_score.asc(), Tier1Label.created_at.desc())
            .limit(limit)
        )
    return [_label_read(label) for label in db.scalars(statement).all()]


@router.patch("/tier1/labels/{label_id}", response_model=Tier1LabelRead)
def update_tier1_label(
    label_id: str,
    payload: Tier1LabelUpdate,
    db: Session = Depends(get_db),
) -> Tier1LabelRead:
    label = db.scalar(
        select(Tier1Label)
        .where(Tier1Label.id == label_id)
        .options(selectinload(Tier1Label.document))
    )
    if label is None:
        raise not_found("Tier 1 label not found.")
    if payload.label is not None:
        label.label = payload.label
        label.label_source = "manual_review"
        label.confidence_score = max(label.confidence_score, 0.95)
    if payload.reviewed is not None:
        label.reviewed = payload.reviewed
    if payload.needs_review is not None:
        label.needs_review = payload.needs_review
    if payload.reviewer_note is not None:
        label.reviewer_note = payload.reviewer_note
    db.add(label)
    db.commit()
    db.refresh(label)
    return _label_read(label)


@router.post("/tier1/datasets/build", response_model=Tier1DatasetBuildResult, status_code=status.HTTP_201_CREATED)
def build_tier1_dataset_route(db: Session = Depends(get_db)) -> Tier1DatasetBuildResult:
    return Tier1DatasetBuildResult(**build_tier1_datasets(db))


@router.get("/tier1/datasets/readiness", response_model=list[Tier1ReadinessRead])
def get_tier1_readiness(db: Session = Depends(get_db)) -> list[Tier1ReadinessRead]:
    return [Tier1ReadinessRead(**item) for item in tier1_readiness(db)]


@router.post("/tier1/export/training-bundle", response_model=Tier1ExportResult, status_code=status.HTTP_201_CREATED)
def export_tier1_training_bundle(db: Session = Depends(get_db)) -> Tier1ExportResult:
    return Tier1ExportResult(**export_training_bundle(db))


@router.get("/tier1/reports", response_model=Tier1ReportRead)
def get_tier1_report(db: Session = Depends(get_db)) -> Tier1ReportRead:
    return Tier1ReportRead(**tier1_report(db))
