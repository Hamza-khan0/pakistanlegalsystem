from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.enums import ChamberTaskType, GroundingUsageType, IntelligenceArtifactType, IntelligenceStatus, ResearchStatus
from app.models.research import ResearchEntry
from app.services.intelligence.generation import (
    attach_grounding_to_artifact,
    build_case_context,
    build_grounding_context,
    create_artifact,
    create_generation_log,
)
from app.services.llm.provider import get_generation_provider


def generate_research_note(
    db: Session,
    case: Case,
    *,
    issue: str = "",
    document_ids: list[str] | None = None,
    instructions: str = "",
) -> tuple[ResearchEntry, object, object]:
    provider = get_generation_provider()
    context = build_case_context(db, case, document_ids=document_ids)
    grounding, retrieved = build_grounding_context(
        db,
        case,
        task_type=ChamberTaskType.RESEARCH_MEMO,
        instruction=instructions or f"Generate a grounded research note for {case.case_number}.",
        focus_issue=issue,
    )
    output = provider.generate_research_note(
        context,
        issue=issue,
        instructions=instructions,
        grounding=grounding,
    )

    research_entry = ResearchEntry(
        case_id=case.id,
        title=output.title,
        query=output.query,
        summary=output.summary,
        citations=output.citations,
        source_type=output.source_type,
        status=ResearchStatus.NEEDS_REVIEW,
        author="Chamber AI Research",
        next_question=output.next_question,
    )
    db.add(research_entry)
    db.flush()

    artifact = create_artifact(
        db,
        case_id=case.id,
        artifact_type=IntelligenceArtifactType.RESEARCH_NOTE,
        title=output.title,
        content=output.content,
        structured_json={
            "query": output.query,
            "summary": output.summary,
            "analysisDirection": output.analysis_direction,
            "statutoryHooks": output.statutory_hooks,
            "factualDependencies": output.factual_dependencies,
            "nextSteps": output.next_steps,
            "citations": output.citations,
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
            "researchEntryId": research_entry.id,
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
        agent_name="Research Agent",
        title=f"Research note generated for {case.case_number}",
        task_type="Issue-based chamber research",
        input_summary=f"Generate a structured research note for the selected issue using {len(context.documents)} documents and the live matter record.",
        output_summary=output.summary,
        next_action=output.next_steps[0] if output.next_steps else "Verify placeholder authorities before external use.",
        citations=output.citations,
        confidence_score=output.confidence_score,
        metadata_json={
            "artifactId": artifact.id,
            "researchEntryId": research_entry.id,
            "documentIds": [document.id for document in context.documents],
            "provider": provider.provider_name,
            "legalGroundingStatus": grounding.status,
            "legalRetrievalQuery": grounding.query,
        },
    )

    db.commit()
    db.refresh(research_entry)
    db.refresh(artifact)
    db.refresh(log)
    return research_entry, artifact, log
