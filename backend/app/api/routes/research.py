from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.research import (
    LEGAL_RESEARCH_WARNING,
    PDF_MODE_DRAFT_WITH_RESEARCH,
    PdfRegenerateRequest,
    PdfRegenerateResponse,
    ResearchDraftRegenerateRequest,
    ResearchDraftResponse,
    ResearchDraftUpdateRequest,
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
from app.services.research_workflow.draft_storage import (
    mark_pdf_generated,
    research_draft_response_payload,
    set_edited_draft_markdown,
)
from app.services.research_workflow.research_draft_pipeline import (
    get_research_run,
    list_case_research_runs,
    regenerate_research_draft,
    regenerate_research_artifacts,
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


def _ensure_markdown_artifact(db: Session, run) -> Path:
    markdown_path = Path(run.markdown_path) if run.markdown_path else None
    if markdown_path is not None and markdown_path.exists():
        return markdown_path

    regenerate_research_artifacts(
        db,
        run,
        generate_pdf=False,
        pdf_mode=PDF_MODE_DRAFT_WITH_RESEARCH,
    )
    db.refresh(run)
    markdown_path = Path(run.markdown_path) if run.markdown_path else None
    if markdown_path is None or not markdown_path.exists():
        raise not_found("Markdown artifact could not be generated for this run.")
    return markdown_path


def _ensure_pdf_artifact(db: Session, run) -> Path:
    pdf_path = Path(run.pdf_path) if run.pdf_path else None
    if pdf_path is not None and pdf_path.exists():
        return pdf_path

    regenerate_research_artifacts(
        db,
        run,
        generate_pdf=True,
        pdf_mode=PDF_MODE_DRAFT_WITH_RESEARCH,
    )
    mark_pdf_generated(run)
    db.commit()
    db.refresh(run)
    pdf_path = Path(run.pdf_path) if run.pdf_path else None
    if pdf_path is None or not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF artifact could not be generated for this run.",
        )
    return pdf_path


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


@router.get("/research/runs/{run_id}/draft", response_model=ResearchDraftResponse)
def read_research_draft(run_id: str, db: Session = Depends(get_db)) -> ResearchDraftResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    try:
        return ResearchDraftResponse(**research_draft_response_payload(run))
    except ValueError as exc:
        raise not_found(str(exc)) from exc


@router.patch("/research/runs/{run_id}/draft", response_model=ResearchDraftResponse)
def update_research_draft(
    run_id: str,
    payload: ResearchDraftUpdateRequest,
    db: Session = Depends(get_db),
) -> ResearchDraftResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    try:
        set_edited_draft_markdown(
            run,
            payload.edited_draft_markdown,
            edit_note=payload.edit_note,
        )
        regenerate_research_artifacts(db, run, generate_pdf=False)
        db.refresh(run)
        return ResearchDraftResponse(**research_draft_response_payload(run))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/research/runs/{run_id}/draft/regenerate", response_model=ResearchDraftResponse)
def regenerate_research_draft_endpoint(
    run_id: str,
    payload: ResearchDraftRegenerateRequest,
    db: Session = Depends(get_db),
) -> ResearchDraftResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    try:
        regenerate_research_draft(
            db,
            run,
            draft_type=payload.draft_type,
            use_llm=payload.use_llm,
        )
        regenerate_research_artifacts(db, run, generate_pdf=False)
        db.refresh(run)
        return ResearchDraftResponse(**research_draft_response_payload(run))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/research/runs/{run_id}/markdown/regenerate", response_model=ResearchWorkflowResponse)
def regenerate_research_markdown(
    run_id: str,
    db: Session = Depends(get_db),
) -> ResearchWorkflowResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    regenerate_research_artifacts(db, run, generate_pdf=False)
    return research_run_to_response(run)


@router.post("/research/runs/{run_id}/pdf/regenerate", response_model=PdfRegenerateResponse)
def regenerate_research_pdf(
    run_id: str,
    payload: PdfRegenerateRequest,
    db: Session = Depends(get_db),
) -> PdfRegenerateResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    try:
        regenerate_research_artifacts(
            db,
            run,
            generate_pdf=True,
            use_edited_draft=payload.use_edited_draft,
            pdf_mode=payload.pdf_mode,
        )
        mark_pdf_generated(run)
        db.commit()
        db.refresh(run)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        ) from exc

    if not run.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation did not produce a file path.",
        )
    pdf_path = Path(run.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation did not produce a file on disk.",
        )
    return PdfRegenerateResponse(
        run_id=run.id,
        pdf_generated=True,
        pdf_path=str(pdf_path),
        pdf_url=f"/api/research/runs/{run.id}/pdf",
        file_size_bytes=pdf_path.stat().st_size,
        pdf_mode=payload.pdf_mode,
    )


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
    markdown_path = _ensure_markdown_artifact(db, run)
    return PlainTextResponse(markdown_path.read_text(encoding="utf-8"))


@router.get("/research/runs/{run_id}/pdf")
def read_research_pdf(
    run_id: str,
    download: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> FileResponse:
    run = get_research_run(db, run_id)
    if run is None:
        raise not_found("Research run not found.")
    pdf_path = _ensure_pdf_artifact(db, run)
    disposition = "attachment" if download else "inline"
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"research_output_{run.id}.pdf",
        content_disposition_type=disposition,
    )
