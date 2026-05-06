from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evaluation import CaseQualitySummaryRead, ChamberRunQualityRead
from app.schemas.runs import AgentActivityRead, ChamberRunCreate, ChamberRunRead, ChamberRunStepRead, ChamberRunSummaryRead
from app.services import cases as case_service
from app.services import runs as run_service
from app.services.evaluation.chamber_quality import evaluate_case_quality, evaluate_run_quality
from app.services.orchestration.runner import create_case_run
from app.services.serializers import (
    serialize_agent_activity,
    serialize_chamber_run,
    serialize_chamber_run_step,
    serialize_chamber_run_summary,
)
from app.utils.http import not_found

router = APIRouter()


@router.post("/cases/{case_id}/runs", response_model=ChamberRunRead, status_code=status.HTTP_201_CREATED)
def create_case_chamber_run(
    case_id: str,
    payload: ChamberRunCreate,
    db: Session = Depends(get_db),
) -> ChamberRunRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    run = create_case_run(
        db,
        case=case,
        instruction=payload.instruction,
        task_type=payload.task_type,
        selected_workflow=payload.selected_workflow,
    )
    return serialize_chamber_run(run)


@router.get("/cases/{case_id}/runs", response_model=list[ChamberRunSummaryRead])
def get_case_runs(case_id: str, db: Session = Depends(get_db)) -> list[ChamberRunSummaryRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [serialize_chamber_run_summary(run) for run in run_service.list_case_runs(db, case_id)]


@router.get("/runs/{run_id}", response_model=ChamberRunRead)
def get_run_detail(run_id: str, db: Session = Depends(get_db)) -> ChamberRunRead:
    run = run_service.get_run_or_none(db, run_id)
    if not run:
        raise not_found("Run not found.")
    return serialize_chamber_run(run)


@router.get("/runs/{run_id}/steps", response_model=list[ChamberRunStepRead])
def get_run_steps(run_id: str, db: Session = Depends(get_db)) -> list[ChamberRunStepRead]:
    run = run_service.get_run_or_none(db, run_id)
    if not run:
        raise not_found("Run not found.")
    return [serialize_chamber_run_step(step) for step in run.steps]


@router.get("/runs/{run_id}/quality", response_model=ChamberRunQualityRead)
def get_run_quality(run_id: str, db: Session = Depends(get_db)) -> ChamberRunQualityRead:
    run = run_service.get_run_or_none(db, run_id)
    if not run:
        raise not_found("Run not found.")
    return ChamberRunQualityRead(**evaluate_run_quality(run))


@router.get("/cases/{case_id}/quality-summary", response_model=CaseQualitySummaryRead)
def get_case_quality_summary(case_id: str, db: Session = Depends(get_db)) -> CaseQualitySummaryRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    return CaseQualitySummaryRead(**evaluate_case_quality(case))


@router.get("/agents/activity", response_model=list[AgentActivityRead])
def get_agent_activity(
    case_id: str | None = Query(default=None, alias="caseId"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[AgentActivityRead]:
    activity = run_service.list_agent_activity(db, case_id=case_id, limit=limit)
    return [serialize_agent_activity(step) for step in activity]
