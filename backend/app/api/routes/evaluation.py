from __future__ import annotations

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evaluation import DatasetReadinessRead, EvaluationReportRead
from app.services.evaluation.dataset_readiness import evaluate_all_datasets, evaluate_dataset_readiness
from app.services.evaluation.report_generator import (
    build_evaluation_report,
    get_evaluation_report,
    list_evaluation_reports,
)
from app.services.ml.training.trainer import get_dataset_or_none, list_ml_datasets
from app.utils.http import not_found

router = APIRouter()


@router.get("/evaluation/datasets/readiness", response_model=list[DatasetReadinessRead])
def get_dataset_readiness(db: Session = Depends(get_db)) -> list[DatasetReadinessRead]:
    return [DatasetReadinessRead(**item) for item in evaluate_all_datasets(list_ml_datasets(db))]


@router.get("/evaluation/datasets/{dataset_id}/readiness", response_model=DatasetReadinessRead)
def get_single_dataset_readiness(dataset_id: str, db: Session = Depends(get_db)) -> DatasetReadinessRead:
    dataset = get_dataset_or_none(db, dataset_id)
    if not dataset:
        raise not_found("Dataset not found.")
    return DatasetReadinessRead(**evaluate_dataset_readiness(dataset))


@router.post("/evaluation/reports/build", response_model=EvaluationReportRead, status_code=status.HTTP_201_CREATED)
def build_report(
    payload: dict[str, str] = Body(default={}),
    db: Session = Depends(get_db),
) -> EvaluationReportRead:
    title = payload.get("title") if isinstance(payload, dict) else None
    return EvaluationReportRead(**build_evaluation_report(db, title=title))


@router.get("/evaluation/reports", response_model=list[EvaluationReportRead])
def get_reports() -> list[EvaluationReportRead]:
    return [EvaluationReportRead(**item) for item in list_evaluation_reports()]


@router.get("/evaluation/reports/{report_id}", response_model=EvaluationReportRead)
def get_report(report_id: str) -> EvaluationReportRead:
    report = get_evaluation_report(report_id)
    if report is None:
        raise not_found("Evaluation report not found.")
    return EvaluationReportRead(**report)
