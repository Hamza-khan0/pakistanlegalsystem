from __future__ import annotations

from app.models.case import Case
from app.services.agents.base import build_agent_input_summary
from app.services.llm.base import CaseContext
from app.services.orchestration.schemas import AgentStepResult, CaseMemoryBundle, LegalGroundingBundle, WorkflowPlan


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cleaned)
    return ordered


def run_procedural_agent(
    case: Case,
    case_context: CaseContext,
    plan: WorkflowPlan,
    memory: CaseMemoryBundle,
    grounding: LegalGroundingBundle,
) -> AgentStepResult:
    latest_timeline = [
        f"{entry['date']}: {entry['title']}"
        for entry in case_context.timeline[:3]
        if entry.get("date") and entry.get("title")
    ]
    caution_flags = list(case_context.procedural_alerts)

    if case_context.next_hearing_date:
        caution_flags.append(
            f"Next listed hearing is {case_context.next_hearing_date}; any chamber output should be aligned to that listing."
        )
    else:
        caution_flags.append("No next hearing date is stored, so procedural timing remains provisional.")

    if not case_context.documents:
        caution_flags.append("No linked document set is currently available for a procedure-backed review.")
    elif not any(document.document_type == "Order Sheet" for document in case_context.documents):
        caution_flags.append("No order sheet is linked, so bench-facing procedural chronology may still be incomplete.")
    if grounding.sources:
        caution_flags.append(
            f"Ground the procedure note in the retrieved legal basis, including {grounding.sources[0].citation_label}."
        )
    elif plan.requires_legal_retrieval:
        caution_flags.append("No sufficiently relevant legal source was retrieved, so procedural grounding is partial.")

    checkpoints = _dedupe(
        [
            f"The matter is currently at: {case_context.filing_stage}.",
            *case_context.procedural_alerts,
            *(f"Grounding source: {source.citation_label}" for source in grounding.sources[:3]),
            *(f"Recent procedural event: {item}" for item in latest_timeline),
            "Cross-check maintainability posture against the present forum before locking submissions.",
        ]
    )
    next_actions = _dedupe(
        [
            *caution_flags,
            "Confirm that every cited annexure is actually linked and processable before relying on it.",
        ]
    )[:5]

    full_output = (
        f"Procedural Posture\nThe matter is presently at {case_context.filing_stage} before {case_context.forum}.\n\n"
        "Checkpoints\n- "
        + "\n- ".join(checkpoints)
        + "\n\nProcedural Cautions\n- "
        + "\n- ".join(_dedupe(caution_flags))
        + "\n\nNext Actions\n- "
        + "\n- ".join(next_actions)
    )
    return AgentStepResult(
        agent_name="Procedural Agent",
        task_label="Procedural posture and risk check",
        input_summary=build_agent_input_summary(
            case=case,
            plan=plan,
            memory=memory,
            grounding=grounding,
        ),
        output_summary=checkpoints[0] if checkpoints else "Procedural review completed.",
        full_output=full_output,
        structured_output={
            "proceduralPosture": case_context.filing_stage,
            "checkpoints": checkpoints,
            "cautionFlags": _dedupe(caution_flags),
            "nextActions": next_actions,
            "hearingDate": case_context.next_hearing_date,
            "legalBasis": [
                {
                    "citationLabel": source.citation_label,
                    "excerpt": source.excerpt,
                }
                for source in grounding.sources[:4]
            ],
        },
        confidence_score=0.79 if case_context.timeline else 0.62,
        source_artifact_ids=memory.source_artifact_ids,
        grounding_source_ids=[source.source_id for source in grounding.sources],
        metadata_json={"legalGroundingStatus": grounding.status},
    )
