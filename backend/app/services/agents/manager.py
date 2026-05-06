from __future__ import annotations

from app.models.case import Case
from app.services.agents.base import build_agent_input_summary
from app.services.llm.base import CaseContext
from app.services.orchestration.schemas import AgentStepResult, CaseMemoryBundle, LegalGroundingBundle, WorkflowPlan


def run_manager_agent(
    case: Case,
    case_context: CaseContext,
    plan: WorkflowPlan,
    memory: CaseMemoryBundle,
    grounding: LegalGroundingBundle,
) -> AgentStepResult:
    output_summary = (
        f"Selected the {plan.workflow_name} workflow for {plan.task_type.value} "
        f"on {case_context.case_number}."
    )
    full_output = (
        f"Objective\n{plan.objective}\n\n"
        f"Selected Workflow\n{plan.workflow_name}\n\n"
        f"Routing Notes\n{plan.routing_notes}\n\n"
        "Task Decomposition\n- "
        + "\n- ".join(plan.decomposition)
        + "\n\n"
        f"Memory Context\n{memory.summary}\n\n"
        f"Legal Grounding\n{grounding.summary}"
    )
    return AgentStepResult(
        agent_name="Manager Agent",
        task_label="Task routing and chamber plan",
        input_summary=build_agent_input_summary(
            case=case,
            plan=plan,
            memory=memory,
            grounding=grounding,
        ),
        output_summary=output_summary,
        full_output=full_output,
        structured_output={
            "objective": plan.objective,
            "selectedWorkflow": plan.workflow_name,
            "taskType": plan.task_type.value,
            "routingNotes": plan.routing_notes,
            "decomposition": plan.decomposition,
            "agentSequence": plan.agent_sequence,
            "legalGroundingStatus": grounding.status,
            "legalSourceCount": len(grounding.sources),
        },
        confidence_score=0.86,
        grounding_source_ids=[source.source_id for source in grounding.sources],
        metadata_json={
            "workflow": plan.workflow_name,
            "legalGroundingStatus": grounding.status,
            "legalSources": [
                {
                    "sourceId": source.source_id,
                    "citationLabel": source.citation_label,
                    "sectionLabel": source.section_label,
                    "relevanceScore": source.relevance_score,
                }
                for source in grounding.sources
            ],
        },
    )
