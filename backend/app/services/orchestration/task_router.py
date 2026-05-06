from __future__ import annotations

from app.models.enums import ChamberTaskType


def classify_task_type(
    instruction: str,
    explicit_task_type: ChamberTaskType | None = None,
) -> ChamberTaskType:
    if explicit_task_type is not None:
        return explicit_task_type

    lowered = instruction.casefold()

    if any(keyword in lowered for keyword in ["preliminary objection", "objection", "maintainability"]):
        return ChamberTaskType.PRELIMINARY_OBJECTIONS
    if any(keyword in lowered for keyword in ["hearing", "oral argument", "bench note"]):
        return ChamberTaskType.HEARING_NOTES
    if any(keyword in lowered for keyword in ["review draft", "review the draft", "critique draft"]):
        return ChamberTaskType.DRAFT_REVIEW
    if any(keyword in lowered for keyword in ["research", "precedent", "authority", "statute"]):
        return ChamberTaskType.RESEARCH_MEMO
    if any(keyword in lowered for keyword in ["procedural", "filing stage", "deadline", "procedure"]):
        return ChamberTaskType.PROCEDURAL_CHECK
    if any(keyword in lowered for keyword in ["issue", "risk", "missing information", "missing document"]):
        return ChamberTaskType.ISSUE_SPOTTING
    if any(keyword in lowered for keyword in ["draft", "petition", "reply", "memo", "outline"]):
        return ChamberTaskType.DRAFT_OUTLINE
    return ChamberTaskType.SUMMARY


def workflow_name_for_task_type(task_type: ChamberTaskType) -> str:
    workflow_map = {
        ChamberTaskType.SUMMARY: "Workflow A - Matter Summary",
        ChamberTaskType.ISSUE_SPOTTING: "Workflow B - Maintainability / Objections",
        ChamberTaskType.PRELIMINARY_OBJECTIONS: "Workflow B - Maintainability / Objections",
        ChamberTaskType.HEARING_NOTES: "Workflow C - Hearing Preparation",
        ChamberTaskType.DRAFT_OUTLINE: "Workflow C - Hearing Preparation",
        ChamberTaskType.DRAFT_REVIEW: "Workflow D - Draft Review",
        ChamberTaskType.RESEARCH_MEMO: "Workflow A - Matter Summary",
        ChamberTaskType.PROCEDURAL_CHECK: "Workflow C - Hearing Preparation",
    }
    return workflow_map[task_type]


def requires_legal_retrieval(task_type: ChamberTaskType) -> bool:
    return task_type in {
        ChamberTaskType.ISSUE_SPOTTING,
        ChamberTaskType.PRELIMINARY_OBJECTIONS,
        ChamberTaskType.HEARING_NOTES,
        ChamberTaskType.DRAFT_OUTLINE,
        ChamberTaskType.DRAFT_REVIEW,
        ChamberTaskType.RESEARCH_MEMO,
        ChamberTaskType.PROCEDURAL_CHECK,
    }


def default_draft_type(task_type: ChamberTaskType, instruction: str) -> str | None:
    lowered = instruction.casefold()
    if task_type == ChamberTaskType.PRELIMINARY_OBJECTIONS:
        return "Preliminary objections outline"
    if task_type == ChamberTaskType.HEARING_NOTES:
        return "Hearing preparation notes"
    if task_type == ChamberTaskType.DRAFT_REVIEW:
        return "Internal strategy note"
    if task_type == ChamberTaskType.DRAFT_OUTLINE:
        if "petition" in lowered:
            return "Petition skeleton"
        if "reply" in lowered:
            return "Reply skeleton"
        if "memo" in lowered:
            return "Case summary memo"
        if "strategy" in lowered:
            return "Internal strategy note"
        return "Draft outline"
    return None
