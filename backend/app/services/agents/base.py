from __future__ import annotations

from statistics import mean

from app.models.case import Case
from app.services.llm.base import CaseContext
from app.services.orchestration.schemas import AgentStepResult, CaseMemoryBundle, LegalGroundingBundle, WorkflowPlan


def build_agent_input_summary(
    *,
    case: Case,
    plan: WorkflowPlan,
    memory: CaseMemoryBundle,
    grounding: LegalGroundingBundle | None = None,
) -> str:
    grounding_count = len(grounding.sources) if grounding else 0
    return (
        f"{plan.objective} Matter: {case.case_number} before {case.forum}. "
        f"Memory sources available: {len(memory.sources)}. "
        f"Legal grounding sources available: {grounding_count}."
    )


def mean_confidence(step_results: list[AgentStepResult]) -> float | None:
    values = [result.confidence_score for result in step_results if result.confidence_score is not None]
    return round(mean(values), 2) if values else None


def latest_output_by_agent(
    step_results: list[AgentStepResult],
    agent_name: str,
) -> AgentStepResult | None:
    for result in reversed(step_results):
        if result.agent_name == agent_name:
            return result
    return None


AgentContext = tuple[
    Case,
    CaseContext,
    WorkflowPlan,
    CaseMemoryBundle,
    LegalGroundingBundle,
    list[AgentStepResult],
]
