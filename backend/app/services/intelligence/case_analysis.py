from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.enums import ChamberTaskType, GroundingUsageType, IntelligenceArtifactType, IntelligenceStatus
from app.models.intelligence_artifact import IntelligenceArtifact
from app.services.intelligence.generation import (
    attach_grounding_to_artifact,
    build_case_context,
    build_grounding_context,
    create_artifact,
    create_generation_log,
    dedupe,
)
from app.services.llm.provider import get_generation_provider


def generate_case_summary(
    db: Session,
    case: Case,
    *,
    document_ids: list[str] | None = None,
    instructions: str = "",
) -> tuple[list[IntelligenceArtifact], object]:
    provider = get_generation_provider()
    context = build_case_context(db, case, document_ids=document_ids)
    grounding, retrieved = build_grounding_context(
        db,
        case,
        task_type=ChamberTaskType.SUMMARY,
        instruction=instructions or f"Summarize {case.case_number} with chamber legal grounding.",
    )
    output = provider.generate_case_summary(
        context,
        instructions=instructions,
        grounding=grounding,
    )

    factual_artifact = create_artifact(
        db,
        case_id=case.id,
        artifact_type=IntelligenceArtifactType.FACTUAL_SUMMARY,
        title=f"Factual summary - {case.case_number}",
        content=(
            "Factual Summary\n"
            f"{output.factual_summary}\n\n"
            "Key Parties\n- " + "\n- ".join(output.key_parties)
        ),
        structured_json={
            "factualSummary": output.factual_summary,
            "keyParties": output.key_parties,
            "importantDates": output.important_dates,
            "reliefSought": output.relief_sought,
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
        },
        source=provider.provider_name,
        status=IntelligenceStatus.GENERATED,
    )
    procedural_artifact = create_artifact(
        db,
        case_id=case.id,
        artifact_type=IntelligenceArtifactType.PROCEDURAL_SUMMARY,
        title=f"Procedural summary - {case.case_number}",
        content=(
            "Procedural Summary\n"
            f"{output.procedural_summary}\n\n"
            "Important Dates\n- " + "\n- ".join(output.important_dates) + "\n\n"
            "Next-Step Recommendations\n- " + "\n- ".join(output.next_steps)
        ),
        structured_json={
            "proceduralSummary": output.procedural_summary,
            "importantDates": output.important_dates,
            "reliefSought": output.relief_sought,
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
        },
        source=provider.provider_name,
        status=IntelligenceStatus.GENERATED,
    )
    attach_grounding_to_artifact(
        db,
        factual_artifact,
        retrieved=retrieved,
        usage_type=GroundingUsageType.RELIED_ON,
    )
    attach_grounding_to_artifact(
        db,
        procedural_artifact,
        retrieved=retrieved,
        usage_type=GroundingUsageType.RELIED_ON,
    )

    log = create_generation_log(
        db,
        case_id=case.id,
        agent_name="Manager Agent",
        title=f"Case summary generated for {case.case_number}",
        task_type="Case intelligence summary",
        input_summary=f"Summarize the matter using {len(context.documents)} linked documents and the live case record.",
        output_summary=output.factual_summary,
        next_action=output.next_steps[0] if output.next_steps else "Review the summary against the live record.",
        citations=output.citations,
        confidence_score=output.confidence_score,
        metadata_json={
            "artifactIds": [factual_artifact.id, procedural_artifact.id],
            "documentIds": [document.id for document in context.documents],
            "provider": provider.provider_name,
            "legalGroundingStatus": grounding.status,
            "legalRetrievalQuery": grounding.query,
        },
    )

    db.commit()
    db.refresh(factual_artifact)
    db.refresh(procedural_artifact)
    db.refresh(log)
    return [factual_artifact, procedural_artifact], log


def generate_issue_spotting(
    db: Session,
    case: Case,
    *,
    document_ids: list[str] | None = None,
    instructions: str = "",
) -> tuple[list[IntelligenceArtifact], object]:
    provider = get_generation_provider()
    context = build_case_context(db, case, document_ids=document_ids)
    grounding, retrieved = build_grounding_context(
        db,
        case,
        task_type=ChamberTaskType.ISSUE_SPOTTING,
        instruction=instructions or f"Identify legal issues and maintainability concerns in {case.case_number}.",
    )
    output = provider.generate_issue_spotting(
        context,
        instructions=instructions,
        grounding=grounding,
    )

    case.legal_issues = dedupe([*case.legal_issues, *output.legal_issues])
    case.risk_flags = dedupe([*case.risk_flags, *output.risk_flags])
    case.procedural_alerts = dedupe([*case.procedural_alerts, *output.recommendations[:2]])
    db.add(case)

    issue_artifact = create_artifact(
        db,
        case_id=case.id,
        artifact_type=IntelligenceArtifactType.ISSUE_SPOTTING,
        title=f"Issue spotting - {case.case_number}",
        content=(
            "Likely Legal Issues\n- " + "\n- ".join(output.legal_issues) + "\n\n"
            "Maintainability Concerns\n- " + "\n- ".join(output.maintainability_concerns)
        ),
        structured_json={
            "legalIssues": output.legal_issues,
            "maintainabilityConcerns": output.maintainability_concerns,
            "missingInformation": output.missing_information,
            "recommendations": output.recommendations,
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
        },
        source=provider.provider_name,
        status=IntelligenceStatus.GENERATED,
    )
    risk_artifact = create_artifact(
        db,
        case_id=case.id,
        artifact_type=IntelligenceArtifactType.RISK_ASSESSMENT,
        title=f"Risk assessment - {case.case_number}",
        content=(
            "Missing Information or Missing Documents\n- " + "\n- ".join(output.missing_information) + "\n\n"
            "Risk Flags\n- " + "\n- ".join(output.risk_flags) + "\n\n"
            "Next-Step Recommendations\n- " + "\n- ".join(output.recommendations)
        ),
        structured_json={
            "missingInformation": output.missing_information,
            "riskFlags": output.risk_flags,
            "recommendations": output.recommendations,
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
        },
        source=provider.provider_name,
        status=IntelligenceStatus.NEEDS_REVIEW,
    )
    attach_grounding_to_artifact(
        db,
        issue_artifact,
        retrieved=retrieved,
        usage_type=GroundingUsageType.RELIED_ON,
    )
    attach_grounding_to_artifact(
        db,
        risk_artifact,
        retrieved=retrieved,
        usage_type=GroundingUsageType.RELIED_ON,
    )

    log = create_generation_log(
        db,
        case_id=case.id,
        agent_name="Critic Agent",
        title=f"Issue spotting completed for {case.case_number}",
        task_type="Issue spotting and risk review",
        input_summary=f"Review the matter record for legal issues, maintainability concerns, and missing material using {len(context.documents)} documents.",
        output_summary="; ".join(output.legal_issues[:3]) or "Issue spotting completed.",
        next_action=output.recommendations[0] if output.recommendations else "Verify the generated risks against the underlying documents.",
        citations=output.citations,
        confidence_score=output.confidence_score,
        metadata_json={
            "artifactIds": [issue_artifact.id, risk_artifact.id],
            "documentIds": [document.id for document in context.documents],
            "provider": provider.provider_name,
            "legalGroundingStatus": grounding.status,
            "legalRetrievalQuery": grounding.query,
        },
    )

    db.commit()
    db.refresh(case)
    db.refresh(issue_artifact)
    db.refresh(risk_artifact)
    db.refresh(log)
    return [issue_artifact, risk_artifact], log
