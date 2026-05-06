from __future__ import annotations

from app.models.case import Case
from app.services.agents.base import build_agent_input_summary
from app.services.llm.base import CaseContext
from app.services.orchestration.schemas import AgentStepResult, CaseMemoryBundle, LegalGroundingBundle, WorkflowPlan


def run_memory_agent(
    case: Case,
    case_context: CaseContext,
    plan: WorkflowPlan,
    memory: CaseMemoryBundle,
    grounding: LegalGroundingBundle,
) -> AgentStepResult:
    sources = [
        f"[{source.source_type}] {source.title}"
        + (f" - {source.detail}" if source.detail else "")
        for source in memory.sources
    ]
    return AgentStepResult(
        agent_name="Memory Agent",
        task_label="Matter continuity retrieval",
        input_summary=build_agent_input_summary(
            case=case,
            plan=plan,
            memory=memory,
            grounding=grounding,
        ),
        output_summary=f"Retrieved {len(memory.sources)} matter memory sources for the run.",
        full_output=(
            f"Memory Summary\n{memory.summary}\n\n"
            "Memory Sources Used\n- "
            + ("\n- ".join(sources) if sources else "No prior matter sources were available.")
        ),
        structured_output={
            "summary": memory.summary,
            "sources": [
                {
                    "sourceId": source.source_id,
                    "sourceType": source.source_type,
                    "title": source.title,
                    "detail": source.detail,
                    "excerpt": source.excerpt,
                }
                for source in memory.sources
            ],
        },
        confidence_score=0.82 if memory.sources else 0.5,
        source_artifact_ids=memory.source_artifact_ids,
        grounding_source_ids=[source.source_id for source in grounding.sources],
        metadata_json={
            "sourceDocumentIds": memory.source_document_ids,
            "sourceRunIds": memory.source_run_ids,
            "legalGroundingStatus": grounding.status,
        },
    )
