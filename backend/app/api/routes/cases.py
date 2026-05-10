from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.case_detail import CaseDetailRead
from app.schemas.research import (
    CaseResearchDraftRequest,
    ResearchRunSummary,
    ResearchWorkflowRequest,
    ResearchWorkflowResponse,
)
from app.services import cases as case_service
from app.services.grounding.provenance import collect_case_legal_basis
from app.services.research_workflow.research_draft_pipeline import (
    list_case_research_runs,
    research_run_summary,
    run_research_draft_pipeline,
)
from app.services.serializers import serialize_case, serialize_case_detail
from app.utils.http import not_found

router = APIRouter(prefix="/cases")


@router.get("", response_model=list[CaseRead])
def list_cases(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    forum: str | None = Query(default=None),
    sort: str = Query(default="hearing"),
    order: str = Query(default="asc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CaseRead]:
    records = case_service.list_cases(
        db,
        q=q,
        status=status_filter,
        priority=priority,
        forum=forum,
        sort=sort,
        order=order,
        limit=limit,
    )
    return [serialize_case(record) for record in records]


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseRead:
    try:
        case = case_service.create_case(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A case with this case number already exists.",
        ) from exc

    return serialize_case(case)


@router.get("/{case_id}", response_model=CaseDetailRead)
def get_case(case_id: str, db: Session = Depends(get_db)) -> CaseDetailRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    return serialize_case_detail(case, legal_basis=collect_case_legal_basis(db, case_id))


@router.get("/{case_id}/research-runs", response_model=list[ResearchRunSummary])
def get_case_research_runs(case_id: str, db: Session = Depends(get_db)) -> list[ResearchRunSummary]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [ResearchRunSummary(**research_run_summary(run)) for run in list_case_research_runs(db, case_id)]


@router.post(
    "/{case_id}/research-draft",
    response_model=ResearchWorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_case_research_draft(
    case_id: str,
    payload: CaseResearchDraftRequest,
    db: Session = Depends(get_db),
) -> ResearchWorkflowResponse:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")

    request = ResearchWorkflowRequest(
        case_id=case_id,
        draft_type=payload.draft_type,
        focus_issues=payload.focus_issues,
        include_documents=payload.include_documents,
        include_prior_notes=payload.include_prior_notes,
        include_timeline=payload.include_timeline,
        max_sources=payload.max_sources,
        max_live_sources=payload.max_live_sources,
        generate_pdf=payload.generate_pdf,
        pdf_mode=payload.pdf_mode,
        use_live_web=payload.use_live_web,
        use_llm=payload.use_llm,
        generate_full_draft=payload.generate_full_draft,
    )
    try:
        return run_research_draft_pipeline(db, request)
    except ValueError as exc:
        raise not_found(str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research workflow failed: {exc}",
        ) from exc


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: str,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
) -> CaseRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")

    try:
        updated = case_service.update_case(db, case, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A case with this case number already exists.",
        ) from exc

    return serialize_case(updated)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: str, db: Session = Depends(get_db)) -> Response:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    case_service.archive_case(db, case)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
