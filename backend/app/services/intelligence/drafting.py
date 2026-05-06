from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.draft import Draft
from app.models.enums import ChamberTaskType, DraftStatus, GroundingUsageType, IntelligenceStatus
from app.services.intelligence.generation import (
    attach_grounding_to_artifact,
    build_case_context,
    build_grounding_context,
    create_artifact,
    create_generation_log,
)
from app.services.llm.provider import get_generation_provider


def next_draft_version(db: Session, *, case_id: str, title: str) -> int:
    existing = db.scalars(
        select(Draft)
        .where(Draft.case_id == case_id, Draft.title == title)
        .order_by(Draft.version.desc())
    ).first()
    return (existing.version + 1) if existing else 1


def generate_draft_assistance(
    db: Session,
    case: Case,
    *,
    draft_type: str,
    document_ids: list[str] | None = None,
    instructions: str = "",
) -> tuple[Draft, object, object]:
    provider = get_generation_provider()
    context = build_case_context(db, case, document_ids=document_ids)
    resolved_task_type = (
        ChamberTaskType.PRELIMINARY_OBJECTIONS
        if "objection" in draft_type.casefold()
        else (
            ChamberTaskType.HEARING_NOTES
            if "hearing" in draft_type.casefold()
            else ChamberTaskType.DRAFT_OUTLINE
        )
    )
    grounding, retrieved = build_grounding_context(
        db,
        case,
        task_type=resolved_task_type,
        instruction=instructions or f"Generate grounded {draft_type} assistance for {case.case_number}.",
    )
    output = provider.generate_draft_assistance(
        context,
        draft_type=draft_type,
        instructions=instructions,
        grounding=grounding,
    )

    draft = Draft(
        case_id=case.id,
        title=output.title,
        draft_type=draft_type,
        status=DraftStatus.DRAFTING,
        content=output.content,
        version=next_draft_version(db, case_id=case.id, title=output.title),
        owner="Chamber AI Drafting",
        summary=output.summary,
    )
    db.add(draft)
    db.flush()

    artifact = create_artifact(
        db,
        case_id=case.id,
        artifact_type=output.artifact_type,
        title=output.title,
        content=output.content,
        structured_json={
            "draftType": draft_type,
            "summary": output.summary,
            "citations": output.citations,
            "nextAction": output.next_action,
            "groundingStatus": grounding.status,
            "legalBasis": [
                {
                    "sourceId": source.source_id,
                    "citationLabel": source.citation_label,
                    "excerpt": source.excerpt,
                }
                for source in grounding.sources
            ],
            "confidenceScore": output.confidence_score,
            "draftId": draft.id,
        },
        source=provider.provider_name,
        status=IntelligenceStatus.NEEDS_REVIEW,
    )
    attach_grounding_to_artifact(
        db,
        artifact,
        retrieved=retrieved,
        usage_type=GroundingUsageType.RELIED_ON,
    )
    log = create_generation_log(
        db,
        case_id=case.id,
        agent_name="Drafting Agent",
        title=f"Draft assistance generated for {case.case_number}",
        task_type=draft_type,
        input_summary=f"Prepare first-pass draft assistance using {len(context.documents)} documents and the current chamber record.",
        output_summary=output.summary,
        next_action=output.next_action,
        citations=output.citations,
        confidence_score=output.confidence_score,
        metadata_json={
            "artifactId": artifact.id,
            "draftId": draft.id,
            "documentIds": [document.id for document in context.documents],
            "provider": provider.provider_name,
            "legalGroundingStatus": grounding.status,
            "legalRetrievalQuery": grounding.query,
        },
    )

    db.commit()
    db.refresh(draft)
    db.refresh(artifact)
    db.refresh(log)
    return draft, artifact, log
