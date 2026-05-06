from __future__ import annotations

from app.models.case import Case
from app.models.enums import ChamberTaskType
from app.services.orchestration.schemas import WorkflowPlan
from app.services.orchestration.task_router import (
    classify_task_type,
    default_draft_type,
    requires_legal_retrieval,
    workflow_name_for_task_type,
)


def _infer_focus_issue(case: Case, instruction: str) -> str | None:
    lowered = instruction.casefold()
    for issue in case.legal_issues:
        tokens = [token for token in issue.casefold().replace(",", " ").split() if len(token) > 4]
        if any(token in lowered for token in tokens):
            return issue
    return case.legal_issues[0] if case.legal_issues else None


def _decomposition(task_type: ChamberTaskType, case: Case) -> list[str]:
    common_lead = f"Open matter context for {case.case_number} and collect live chamber memory."
    legal_grounding_step = "Retrieve relevant Pakistani legal materials and provision-level support for the task."

    if task_type == ChamberTaskType.SUMMARY:
        return [
            common_lead,
            "Assemble factual and procedural context from stored case materials.",
            "Generate a concise matter summary suitable for chamber review.",
            "Run critic review to tighten caution notes and missing-fact flags.",
        ]
    if task_type == ChamberTaskType.PRELIMINARY_OBJECTIONS:
        return [
            common_lead,
            legal_grounding_step,
            "Check procedural posture and likely maintainability objections.",
            "Surface supporting issue and authority directions from the live matter record.",
            "Draft the objections outline and send it through critic review.",
        ]
    if task_type == ChamberTaskType.HEARING_NOTES:
        return [
            common_lead,
            legal_grounding_step,
            "Check hearing posture, timing, and procedural cautions.",
            "Surface the issues and research directions most likely to matter at hearing.",
            "Draft hearing notes and pressure-test them through the critic pass.",
        ]
    if task_type == ChamberTaskType.DRAFT_REVIEW:
        return [
            common_lead,
            legal_grounding_step,
            "Pull prior draft and supporting matter memory into a review packet.",
            "Generate a chamber review note focused on structure, risk, and missing support.",
            "Run critic review before storing the final reviewed position.",
        ]
    if task_type == ChamberTaskType.RESEARCH_MEMO:
        return [
            common_lead,
            legal_grounding_step,
            "Retrieve prior research and issue memory from the same matter.",
            "Generate a structured research-style note with clearly labeled leads.",
            "Run critic review before the memo is stored against the matter.",
        ]
    if task_type == ChamberTaskType.PROCEDURAL_CHECK:
        return [
            common_lead,
            legal_grounding_step,
            "Review procedural posture, filing stage, and timing sensitivities.",
            "Surface live risks and dependencies from the stored record.",
            "Run critic review before storing the procedural chamber note.",
        ]
    if task_type == ChamberTaskType.ISSUE_SPOTTING:
        return [
            common_lead,
            legal_grounding_step,
            "Pull prior issue and risk memory from the matter.",
            "Surface live legal issues, maintainability concerns, and missing material.",
            "Run critic review and store the reviewed issue note.",
        ]

    return [
        common_lead,
        legal_grounding_step,
        "Retrieve the strongest matter memory from the current record.",
        "Generate a drafting-oriented chamber output for review.",
        "Run critic review before storing the reviewed output.",
    ]


def _agent_sequence(task_type: ChamberTaskType) -> list[str]:
    if task_type in {ChamberTaskType.SUMMARY, ChamberTaskType.RESEARCH_MEMO}:
        return ["Manager Agent", "Memory Agent", "Research Agent", "Critic Agent"]
    if task_type == ChamberTaskType.PROCEDURAL_CHECK:
        return ["Manager Agent", "Memory Agent", "Procedural Agent", "Critic Agent"]
    if task_type == ChamberTaskType.DRAFT_REVIEW:
        return ["Manager Agent", "Memory Agent", "Drafting Agent", "Critic Agent"]
    if task_type in {
        ChamberTaskType.PRELIMINARY_OBJECTIONS,
        ChamberTaskType.HEARING_NOTES,
        ChamberTaskType.DRAFT_OUTLINE,
        ChamberTaskType.ISSUE_SPOTTING,
    }:
        agent_sequence = [
            "Manager Agent",
            "Memory Agent",
            "Procedural Agent",
            "Research Agent",
        ]
        if task_type != ChamberTaskType.ISSUE_SPOTTING:
            agent_sequence.append("Drafting Agent")
        agent_sequence.append("Critic Agent")
        return [
            *agent_sequence,
        ]

    return ["Manager Agent", "Memory Agent", "Research Agent", "Drafting Agent", "Critic Agent"]


def _routing_notes(task_type: ChamberTaskType) -> str:
    if task_type == ChamberTaskType.SUMMARY:
        return "Matter summary was selected because the instruction is centered on factual or procedural orientation."
    if task_type == ChamberTaskType.PRELIMINARY_OBJECTIONS:
        return "Maintainability / objections workflow was selected because the instruction signals threshold objections or jurisdiction concerns."
    if task_type == ChamberTaskType.HEARING_NOTES:
        return "Hearing preparation workflow was selected because the instruction points to a live or upcoming court appearance."
    if task_type == ChamberTaskType.DRAFT_REVIEW:
        return "Draft review workflow was selected because the instruction points to reviewing or pressure-testing an existing draft posture."
    if task_type == ChamberTaskType.RESEARCH_MEMO:
        return "Research workflow was selected because the instruction emphasizes authorities, research direction, or legal analysis."
    if task_type == ChamberTaskType.PROCEDURAL_CHECK:
        return "Procedural workflow was selected because the instruction focuses on posture, timing, or filing-stage caution."
    if task_type == ChamberTaskType.ISSUE_SPOTTING:
        return "Issue-spotting workflow was selected because the instruction targets risks, missing material, or legal issues."
    return "Drafting workflow was selected because the instruction seeks structured written work product."


def _retrieval_focus(case: Case, task_type: ChamberTaskType, focus_issue: str | None) -> list[str]:
    focus = [focus_issue] if focus_issue else []
    focus.extend(case.linked_statutes[:2])

    if task_type in {
        ChamberTaskType.ISSUE_SPOTTING,
        ChamberTaskType.PRELIMINARY_OBJECTIONS,
        ChamberTaskType.PROCEDURAL_CHECK,
    }:
        focus.extend(["maintainability", "jurisdiction", "procedural posture"])
    elif task_type == ChamberTaskType.HEARING_NOTES:
        focus.extend(["interim relief", "hearing posture", "urgent relief"])
    elif task_type in {ChamberTaskType.DRAFT_OUTLINE, ChamberTaskType.DRAFT_REVIEW}:
        focus.extend(["pleadable grounds", "legal basis", "supporting provisions"])
    elif task_type == ChamberTaskType.RESEARCH_MEMO:
        focus.extend(["issue-based statutory support", "authority leads"])

    deduped: list[str] = []
    seen: set[str] = set()
    for item in focus:
        if not item:
            continue
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped[:6]


def build_workflow_plan(
    case: Case,
    *,
    instruction: str,
    task_type: ChamberTaskType | None = None,
    selected_workflow: str | None = None,
) -> WorkflowPlan:
    resolved_task_type = classify_task_type(instruction, task_type)
    workflow_name = selected_workflow.strip() if selected_workflow and selected_workflow.strip() else workflow_name_for_task_type(resolved_task_type)
    focus_issue = _infer_focus_issue(case, instruction)
    draft_type = default_draft_type(resolved_task_type, instruction)

    return WorkflowPlan(
        task_type=resolved_task_type,
        workflow_name=workflow_name,
        objective=(
            f"Produce a critic-reviewed chamber output for {case.case_number} responding to: "
            f"{instruction.strip() or resolved_task_type.value}."
        ),
        routing_notes=_routing_notes(resolved_task_type),
        decomposition=_decomposition(resolved_task_type, case),
        agent_sequence=_agent_sequence(resolved_task_type),
        draft_type=draft_type,
        focus_issue=focus_issue,
        requires_legal_retrieval=requires_legal_retrieval(resolved_task_type),
        retrieval_focus=_retrieval_focus(case, resolved_task_type, focus_issue),
    )
