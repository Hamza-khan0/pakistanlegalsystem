from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.research import (
    LEGAL_RESEARCH_WARNING,
    ResearchEntryCreate,
    ResearchEntryRead,
    ResearchHealthRead,
    ResearchRunSummary,
    WebSearchTestRequest,
    ResearchWorkflowRequest,
    ResearchWorkflowResponse,
)
from app.services import cases as case_service
from app.services import research as research_service
from app.services.llm.provider import PRIVACY_NOTICE, get_llm_health
from app.services.ml.training.imported_legal_issue import get_legal_issue_model_health
from app.services.research_workflow.research_artifacts import ARTIFACT_ROOT
from app.services.research_workflow.research_draft_pipeline import (
    get_research_run,
    list_case_research_runs,
    research_run_summary,
    research_run_to_response,
    run_research_draft_pipeline,
)
from app.services.research_workflow.live_web_search import (
    get_live_web_search_health,
    run_live_legal_web_search,
)
from app.services.serializers import serialize_research_entry
from app.utils.http import not_found

router = APIRouter()


@router.get("/cases/{case_id}/research", response_model=list[ResearchEntryRead])
def get_case_research(case_id: str, db: Session = Depends(get_db)) -> list[ResearchEntryRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [
        serialize_research_entry(entry)
        for entry in research_service.list_research_entries(db, case_id)
    ]


@router.post(
    "/cases/{case_id}/research",
    response_model=ResearchEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_research_entry(
    case_id: str,
    payload: ResearchEntryCreate,
    db: Session = Depends(get_db),
) -> ResearchEntryRead:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    entry = research_service.create_research_entry(db, case_id, payload)
    return serialize_research_entry(entry)


@router.get("/research/health", response_model=ResearchHealthRead)
def get_research_health() -> ResearchHealthRead:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    probe = ARTIFACT_ROOT / ".write_probe"
    artifact_writable = False
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        artifact_writable = True
    except OSError:
        artifact_writable = False

    web_health = get_live_web_search_health()
    llm_health = get_llm_health()
    return ResearchHealthRead(
        workflow_available=True,
        legal_issue_classifier=get_legal_issue_model_health(),
        local_retrieval_available=True,
        retrieval_adapter_available=True,
        live_web_search_enabled=bool(web_health.get("enabled")),
        live_web_search_available=bool(web_health.get("available")),
        search_provider=str(web_health.get("provider") or "none"),
        llm_enabled=bool(llm_health.get("enabled")),
        llm_available=bool(llm_health.get("available")),
        llm_model=str(llm_health.get("model") or ""),
        llm_configured=bool(llm_health.get("api_key_configured")),
        pdf_available=True,
        artifact_directory_writable=artifact_writable,
        privacy_notice=PRIVACY_NOTICE,
        legal_authority_warning=LEGAL_RESEARCH_WARNING,
    )


@router.post("/research/web-search/test")
def test_research_web_search(payload: WebSearchTestRequest) -> dict:
    health = get_live_web_search_health()
    if not health.get("available"):
        return {
            "status": "warning",
            "message": health.get("reason") or "Live web search is unavailable.",
            "health": health,
            "results": [],
        }
    return {
        "status": "ok",
        "health": health,
        "results": run_live_legal_web_search(payload.query, max_results=payload.max_results),
    }


@router.post(
    "/research/runs",
    response_model=ResearchWorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_research_run(
    payload: ResearchWorkflowRequest,
    db: Session = Depends(get_db),
) -> ResearchWorkflowResponse:
    try:
        return run_research_draft_pipeline(db, payload)
    except ValueError as exc:
        raise not_found(str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research workflow failed: {exc}",
        ) from exc


@router.get("/research/runs/{run_id}", response_model=ResearchWorkflowResponse)
def read_research_run(run_id: str, db: Session = Depends(get_db)) -> ResearchWorkflowResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    return research_run_to_response(run)


@router.get("/research/cases/{case_id}/runs", response_model=list[ResearchRunSummary])
def read_case_research_runs(case_id: str, db: Session = Depends(get_db)) -> list[ResearchRunSummary]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [ResearchRunSummary(**research_run_summary(run)) for run in list_case_research_runs(db, case_id)]


@router.get("/research/runs/{run_id}/markdown", response_class=PlainTextResponse)
def read_research_markdown(run_id: str, db: Session = Depends(get_db)) -> PlainTextResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    if not run.markdown_path:
        raise not_found("Markdown artifact was not generated for this run.")
    markdown_path = Path(run.markdown_path)
    if not markdown_path.exists():
        raise not_found("Markdown artifact file is missing from disk.")
    return PlainTextResponse(markdown_path.read_text(encoding="utf-8"))


@router.get("/research/runs/{run_id}/pdf")
def read_research_pdf(run_id: str, db: Session = Depends(get_db)) -> FileResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    if not run.pdf_path:
        raise not_found("PDF artifact was not generated for this run.")
    pdf_path = Path(run.pdf_path)
    if not pdf_path.exists():
        raise not_found("PDF artifact file is missing from disk.")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"research_memo_{run.id}.pdf",
    )
