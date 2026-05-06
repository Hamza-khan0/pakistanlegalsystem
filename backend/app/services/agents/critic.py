from __future__ import annotations

from app.models.case import Case
from app.models.enums import ChamberTaskType
from app.services.agents.base import (
    build_agent_input_summary,
    latest_output_by_agent,
    mean_confidence,
)
from app.services.llm.base import CaseContext
from app.services.orchestration.schemas import AgentStepResult, CaseMemoryBundle, LegalGroundingBundle, WorkflowPlan


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        lowered = cleaned.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(cleaned)
    return ordered


def _read_string_list(result: AgentStepResult | None, key: str) -> list[str]:
    if not result:
        return []
    candidate = result.structured_output.get(key)
    if not isinstance(candidate, list):
        return []
    return [item for item in candidate if isinstance(item, str) and item.strip()]


def _build_revised_summary(
    *,
    plan: WorkflowPlan,
    primary_output: AgentStepResult | None,
    missing_facts: list[str],
    suggested_improvements: list[str],
) -> str:
    if primary_output and primary_output.output_summary:
        base = primary_output.output_summary
    elif plan.task_type == ChamberTaskType.SUMMARY:
        base = "Matter summary prepared for chamber review."
    elif plan.task_type == ChamberTaskType.RESEARCH_MEMO:
        base = "Research note prepared for chamber review."
    elif plan.task_type == ChamberTaskType.PROCEDURAL_CHECK:
        base = "Procedural review prepared for chamber review."
    else:
        base = "Drafting support prepared for chamber review."

    cautions: list[str] = []
    if missing_facts:
        cautions.append(f"Key gap: {missing_facts[0]}")
    if suggested_improvements:
        cautions.append(f"Immediate improvement: {suggested_improvements[0]}")

    if cautions:
        return f"{base} {' '.join(cautions)}"
    return base


def run_critic_agent(
    case: Case,
    case_context: CaseContext,
    plan: WorkflowPlan,
    memory: CaseMemoryBundle,
    grounding: LegalGroundingBundle,
    step_results: list[AgentStepResult],
) -> AgentStepResult:
    research_output = latest_output_by_agent(step_results, "Research Agent")
    drafting_output = latest_output_by_agent(step_results, "Drafting Agent")
    procedural_output = latest_output_by_agent(step_results, "Procedural Agent")
    primary_output = drafting_output or research_output or procedural_output

    missing_facts = _dedupe(
        [
            *_read_string_list(research_output, "missingInformation"),
            *case_context.risk_flags,
        ]
    )
    unsupported_assumptions: list[str] = []
    if not case_context.documents:
        unsupported_assumptions.append(
            "No processed document set currently supports the chamber output, so factual confidence remains provisional."
        )
    if plan.requires_legal_retrieval and not grounding.sources:
        unsupported_assumptions.append(
            "No retrieved Pakistani legal source backed the current output, so legal propositions remain only partially grounded."
        )
    if not case_context.timeline:
        unsupported_assumptions.append(
            "Procedural chronology is thin because the timeline record is sparse."
        )
    if case_context.next_hearing_date is None and plan.task_type == ChamberTaskType.HEARING_NOTES:
        unsupported_assumptions.append(
            "Hearing-focused output is operating without a stored next hearing date."
        )

    structural_weaknesses: list[str] = []
    if primary_output and len(primary_output.full_output.split()) < 120:
        structural_weaknesses.append(
            "Primary output is concise and may need a fuller issue ladder before partner use."
        )
    if primary_output and "placeholder" in primary_output.full_output.casefold():
        structural_weaknesses.append(
            "Authority or drafting leads remain placeholders and must be verified against the live record."
        )
    if not primary_output:
        structural_weaknesses.append(
            "No substantive research or drafting pass ran before review, so the critic can only give a limited chamber caution note."
        )

    procedural_dependencies = _dedupe(
        [
            *_read_string_list(procedural_output, "cautionFlags"),
            *_read_string_list(procedural_output, "nextActions"),
            *case_context.procedural_alerts,
        ]
    )
    suggested_improvements = _dedupe(
        [
            *(_read_string_list(research_output, "recommendations")),
            *(_read_string_list(research_output, "missingInformation")),
            *procedural_dependencies[:2],
            (
                f"Strengthen the legal basis with retrieved authority such as {grounding.sources[0].citation_label}."
                if grounding.sources
                else "Add a stronger retrieved statutory or provision-level basis before relying on the output externally."
            ),
            "Pressure-test the generated position against the live pleadings before external circulation.",
        ]
    )

    if not missing_facts:
        missing_facts.append("No additional material gap was surfaced beyond the current chamber record.")
    if not unsupported_assumptions:
        unsupported_assumptions.append("No critical unsupported assumption was obvious from the loaded case memory.")
    if not structural_weaknesses:
        structural_weaknesses.append("Structure is serviceable for chamber use, but still needs counsel review before filing reliance.")
    if not procedural_dependencies:
        procedural_dependencies.append("No fresh procedural dependency was identified beyond the stored case posture.")

    revised_output_summary = _build_revised_summary(
        plan=plan,
        primary_output=primary_output,
        missing_facts=missing_facts,
        suggested_improvements=suggested_improvements,
    )
    citations = _dedupe(
        [
            *(primary_output.citations if primary_output else []),
            *(research_output.citations if research_output else []),
        ]
    )
    confidence_floor = mean_confidence(step_results) or 0.62
    confidence_penalty = min(0.2, 0.03 * (len(missing_facts) + len(unsupported_assumptions)))
    confidence_score = round(max(0.42, confidence_floor - confidence_penalty), 2)

    full_output = (
        "Critic Review Scope\n"
        f"{plan.objective}\n\n"
        f"Grounding Status\n{grounding.status}\n\n"
        "Missing Facts or Record Gaps\n- "
        + "\n- ".join(missing_facts)
        + "\n\nUnsupported Assumptions\n- "
        + "\n- ".join(unsupported_assumptions)
        + "\n\nStructural Weaknesses\n- "
        + "\n- ".join(structural_weaknesses)
        + "\n\nProcedural Dependencies\n- "
        + "\n- ".join(procedural_dependencies)
        + "\n\nSuggested Improvements\n- "
        + "\n- ".join(suggested_improvements[:5])
        + "\n\nCritic-Reviewed Position\n"
        + revised_output_summary
    )

    return AgentStepResult(
        agent_name="Critic Agent",
        task_label="Critic and reliability review",
        input_summary=build_agent_input_summary(
            case=case,
            plan=plan,
            memory=memory,
            grounding=grounding,
        ),
        output_summary=revised_output_summary,
        full_output=full_output,
        structured_output={
            "missingFacts": missing_facts,
            "unsupportedAssumptions": unsupported_assumptions,
            "structuralWeaknesses": structural_weaknesses,
            "proceduralDependencies": procedural_dependencies,
            "suggestedImprovements": suggested_improvements[:5],
            "revisedOutputSummary": revised_output_summary,
            "groundingStatus": grounding.status,
            "groundingSources": [
                {
                    "citationLabel": source.citation_label,
                    "excerpt": source.excerpt,
                }
                for source in grounding.sources[:4]
            ],
        },
        confidence_score=confidence_score,
        citations=citations,
        source_artifact_ids=memory.source_artifact_ids,
        grounding_source_ids=[source.source_id for source in grounding.sources],
        metadata_json={
            "reviewedAgents": [result.agent_name for result in step_results],
            "legalGroundingStatus": grounding.status,
        },
    )
