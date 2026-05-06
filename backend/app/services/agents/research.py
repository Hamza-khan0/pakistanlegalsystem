from __future__ import annotations

from app.models.case import Case
from app.models.enums import ChamberTaskType
from app.services.agents.base import build_agent_input_summary
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


def run_research_agent(
    case: Case,
    case_context: CaseContext,
    plan: WorkflowPlan,
    memory: CaseMemoryBundle,
    grounding: LegalGroundingBundle,
) -> AgentStepResult:
    provider = get_generation_provider()
    provider_grounding = _provider_grounding_context(grounding)

    if plan.task_type == ChamberTaskType.SUMMARY:
        summary = provider.generate_case_summary(
            case_context,
            instructions=f"{plan.objective} Use prior matter memory where it helps, but stay explicit about missing material.",
            grounding=provider_grounding,
        )
        return AgentStepResult(
            agent_name="Research Agent",
            task_label="Matter analysis and summary framing",
            input_summary=build_agent_input_summary(
                case=case,
                plan=plan,
                memory=memory,
                grounding=grounding,
            ),
            output_summary=summary.factual_summary,
            full_output=(
                f"Factual Summary\n{summary.factual_summary}\n\n"
                f"Procedural Summary\n{summary.procedural_summary}\n\n"
                "Key Parties\n- "
                + "\n- ".join(summary.key_parties)
                + "\n\nImportant Dates\n- "
                + "\n- ".join(summary.important_dates)
                + "\n\nRelief Sought\n- "
                + "\n- ".join(summary.relief_sought)
            ),
            structured_output={
                "factualSummary": summary.factual_summary,
                "proceduralSummary": summary.procedural_summary,
                "keyParties": summary.key_parties,
                "importantDates": summary.important_dates,
                "reliefSought": summary.relief_sought,
                "nextSteps": summary.next_steps,
                "citations": summary.citations,
            },
            confidence_score=summary.confidence_score,
            citations=summary.citations,
            source_artifact_ids=memory.source_artifact_ids,
            grounding_source_ids=[source.source_id for source in grounding.sources],
            metadata_json={"legalGroundingStatus": grounding.status},
        )

    if plan.task_type == ChamberTaskType.RESEARCH_MEMO:
        focus_issue = plan.focus_issue or (
            case_context.legal_issues[0] if case_context.legal_issues else ""
        )
        research = provider.generate_research_note(
            case_context,
            issue=focus_issue,
            instructions=f"{plan.objective} Keep authority leads clearly labeled if not yet verified in the live record.",
            grounding=provider_grounding,
        )
        return AgentStepResult(
            agent_name="Research Agent",
            task_label="Research memorandum analysis",
            input_summary=build_agent_input_summary(
                case=case,
                plan=plan,
                memory=memory,
                grounding=grounding,
            ),
            output_summary=research.summary,
            full_output=research.content,
            structured_output={
                "title": research.title,
                "query": research.query,
                "summary": research.summary,
                "analysisDirection": research.analysis_direction,
                "statutoryHooks": research.statutory_hooks,
                "factualDependencies": research.factual_dependencies,
                "nextSteps": research.next_steps,
                "citations": research.citations,
            },
            confidence_score=research.confidence_score,
            citations=research.citations,
            source_artifact_ids=memory.source_artifact_ids,
            grounding_source_ids=[source.source_id for source in grounding.sources],
            metadata_json={"legalGroundingStatus": grounding.status},
        )

    issue_output = provider.generate_issue_spotting(
        case_context,
        instructions=f"{plan.objective} Surface maintainability, record gaps, and authority directions suitable for chamber review.",
        grounding=provider_grounding,
    )
    return AgentStepResult(
        agent_name="Research Agent",
        task_label="Issue analysis and authority direction",
        input_summary=build_agent_input_summary(
            case=case,
            plan=plan,
            memory=memory,
            grounding=grounding,
        ),
        output_summary="; ".join(issue_output.legal_issues[:3]) or "Issue review completed.",
        full_output=(
            "Likely Legal Issues\n- "
            + "\n- ".join(issue_output.legal_issues)
            + "\n\nMaintainability Concerns\n- "
            + "\n- ".join(issue_output.maintainability_concerns)
            + "\n\nMissing Information\n- "
            + "\n- ".join(issue_output.missing_information)
            + "\n\nRecommendations\n- "
            + "\n- ".join(issue_output.recommendations)
        ),
        structured_output={
            "legalIssues": issue_output.legal_issues,
            "maintainabilityConcerns": issue_output.maintainability_concerns,
            "missingInformation": issue_output.missing_information,
            "riskFlags": issue_output.risk_flags,
            "recommendations": issue_output.recommendations,
            "citations": issue_output.citations,
        },
        confidence_score=issue_output.confidence_score,
        citations=issue_output.citations,
        source_artifact_ids=memory.source_artifact_ids,
        grounding_source_ids=[source.source_id for source in grounding.sources],
        metadata_json={"legalGroundingStatus": grounding.status},
    )
