from __future__ import annotations

from app.models.case import Case
from app.models.enums import ChamberTaskType
from app.services.agents.base import (
    build_agent_input_summary,
    latest_output_by_agent,
)
from app.services.llm.base import CaseContext, GroundedSourceContext, GroundingContext
from app.services.llm.provider import get_generation_provider
from app.services.orchestration.schemas import AgentStepResult, CaseMemoryBundle, LegalGroundingBundle, WorkflowPlan


def _provider_grounding_context(grounding: LegalGroundingBundle) -> GroundingContext:
    return GroundingContext(
        query=grounding.query,
        status=grounding.status,
        summary=grounding.summary,
        sources=[
            GroundedSourceContext(
                source_id=source.source_id,
                chunk_id=source.chunk_id,
                title=source.title,
                short_title=source.short_title,
                citation_label=source.citation_label,
                source_type=source.source_type,
                category=source.category,
                act_name=source.act_name,
                section_label=source.section_label,
                excerpt=source.excerpt,
                relevance_score=source.relevance_score,
                usage_type=source.usage_type,
            )
            for source in grounding.sources
        ],
    )


def _instruction_packet(
    *,
    plan: WorkflowPlan,
    case_context: CaseContext,
    research_output: AgentStepResult | None,
    procedural_output: AgentStepResult | None,
    grounding: LegalGroundingBundle,
) -> str:
    packets = [plan.objective]

    if plan.focus_issue:
        packets.append(f"Primary issue for this pass: {plan.focus_issue}.")
    if research_output:
        packets.append(
            f"Use the live research direction already surfaced: {research_output.output_summary}"
        )
    if procedural_output:
        packets.append(
            "Respect the stored procedural cautions and filing posture already identified by the chamber."
        )
    if grounding.sources:
        packets.append(
            "Incorporate the retrieved legal basis into the draft and keep source-backed propositions distinct from chamber inference."
        )
    elif plan.requires_legal_retrieval:
        packets.append(
            "No sufficiently relevant legal source was retrieved, so mark legal propositions as provisional and note the research gap."
        )
    if plan.task_type == ChamberTaskType.DRAFT_REVIEW:
        packets.append(
            "Frame the output as a review-oriented chamber note on the current draft posture, not as a final filing-ready pleading."
        )
    if not case_context.documents:
        packets.append(
            "Source material remains thin because no processed document set is currently available; keep the drafting support clearly provisional."
        )

    return " ".join(packet.strip() for packet in packets if packet.strip())


def run_drafting_agent(
    case: Case,
    case_context: CaseContext,
    plan: WorkflowPlan,
    memory: CaseMemoryBundle,
    grounding: LegalGroundingBundle,
    step_results: list[AgentStepResult],
) -> AgentStepResult:
    provider = get_generation_provider()
    research_output = latest_output_by_agent(step_results, "Research Agent")
    procedural_output = latest_output_by_agent(step_results, "Procedural Agent")
    draft_type = plan.draft_type or "Draft outline"

    draft_output = provider.generate_draft_assistance(
        case_context,
        draft_type=draft_type,
        instructions=_instruction_packet(
            plan=plan,
            case_context=case_context,
            research_output=research_output,
            procedural_output=procedural_output,
            grounding=grounding,
        ),
        grounding=_provider_grounding_context(grounding),
    )

    return AgentStepResult(
        agent_name="Drafting Agent",
        task_label=f"{draft_type} drafting pass",
        input_summary=build_agent_input_summary(
            case=case,
            plan=plan,
            memory=memory,
            grounding=grounding,
        ),
        output_summary=draft_output.summary,
        full_output=draft_output.content,
        structured_output={
            "title": draft_output.title,
            "draftType": draft_type,
            "artifactType": draft_output.artifact_type.value,
            "summary": draft_output.summary,
            "citations": draft_output.citations,
            "nextAction": draft_output.next_action,
        },
        confidence_score=draft_output.confidence_score,
        citations=draft_output.citations,
        source_artifact_ids=memory.source_artifact_ids,
        grounding_source_ids=[source.source_id for source in grounding.sources],
        metadata_json={
            "nextAction": draft_output.next_action,
            "legalGroundingStatus": grounding.status,
        },
    )
