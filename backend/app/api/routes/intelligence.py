from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.intelligence import (
    CaseGenerationRead,
    DraftGenerationRead,
    GenerateDraftRequest,
    GenerateIssuesRequest,
    GenerateResearchRequest,
    GenerateSummaryRequest,
    IntelligenceArtifactRead,
    ResearchGenerationRead,
)
from app.services import cases as case_service
from app.services import intelligence_artifacts as intelligence_artifact_service
from app.services.intelligence import (
    generate_case_summary,
    generate_draft_assistance,
    generate_issue_spotting,
    generate_research_note,
)
from app.services.serializers import (
    serialize_agent_log,
    serialize_draft,
    serialize_intelligence_artifact,
    serialize_research_entry,
)
from app.utils.http import not_found

router = APIRouter()


@router.get("/cases/{case_id}/intelligence", response_model=list[IntelligenceArtifactRead])
def get_case_intelligence(case_id: str, db: Session = Depends(get_db)) -> list[IntelligenceArtifactRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [
        serialize_intelligence_artifact(artifact)
        for artifact in intelligence_artifact_service.list_case_intelligence(db, case_id)
    ]


@router.get("/intelligence/{artifact_id}", response_model=IntelligenceArtifactRead)
def get_intelligence_artifact(artifact_id: str, db: Session = Depends(get_db)) -> IntelligenceArtifactRead:
    artifact = intelligence_artifact_service.get_artifact_or_none(db, artifact_id)
    if not artifact:
        raise not_found("Intelligence artifact not found.")
    return serialize_intelligence_artifact(artifact)


@router.post("/cases/{case_id}/generate-summary", response_model=CaseGenerationRead)
def create_case_summary(
    case_id: str,
    payload: GenerateSummaryRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> CaseGenerationRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    request = payload or GenerateSummaryRequest()
    artifacts, agent_output = generate_case_summary(
        db,
        case,
        document_ids=request.document_ids,
        instructions=request.instructions,
    )
    return CaseGenerationRead(
        artifacts=[serialize_intelligence_artifact(artifact) for artifact in artifacts],
        agent_output=serialize_agent_log(agent_output),
    )


@router.post("/cases/{case_id}/generate-issues", response_model=CaseGenerationRead)
def create_issue_spotting(
    case_id: str,
    payload: GenerateIssuesRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> CaseGenerationRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    request = payload or GenerateIssuesRequest()
    artifacts, agent_output = generate_issue_spotting(
        db,
        case,
        document_ids=request.document_ids,
        instructions=request.instructions,
    )
    return CaseGenerationRead(
        artifacts=[serialize_intelligence_artifact(artifact) for artifact in artifacts],
        agent_output=serialize_agent_log(agent_output),
    )


@router.post(
    "/cases/{case_id}/generate-draft",
    response_model=DraftGenerationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_generated_draft(
    case_id: str,
    payload: GenerateDraftRequest,
    db: Session = Depends(get_db),
) -> DraftGenerationRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    draft, artifact, agent_output = generate_draft_assistance(
        db,
        case,
        draft_type=payload.draft_type,
        document_ids=payload.document_ids,
        instructions=payload.instructions,
    )
    return DraftGenerationRead(
        draft=serialize_draft(draft),
        artifact=serialize_intelligence_artifact(artifact),
        agent_output=serialize_agent_log(agent_output),
    )


@router.post(
    "/cases/{case_id}/generate-research",
    response_model=ResearchGenerationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_generated_research(
    case_id: str,
    payload: GenerateResearchRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> ResearchGenerationRead:
    case = case_service.get_case_or_none(db, case_id)
    if not case:
        raise not_found("Case not found.")
    request = payload or GenerateResearchRequest()
    research_entry, artifact, agent_output = generate_research_note(
        db,
        case,
        issue=request.issue,
        document_ids=request.document_ids,
        instructions=request.instructions,
    )
    return ResearchGenerationRead(
        research_entry=serialize_research_entry(research_entry),
        artifact=serialize_intelligence_artifact(artifact),
        agent_output=serialize_agent_log(agent_output),
    )
