from __future__ import annotations

from statistics import mean
from typing import Any

from app.models.case import Case


def _safe_count(value: list[Any] | None) -> int:
    return len(value or [])


def build_case_text(case: Case) -> str:
    parts = [
        case.title,
        case.case_number,
        case.forum,
        case.matter_type,
        case.summary,
        " ".join(case.legal_issues),
        " ".join(case.relief_sought),
        " ".join(case.important_notes),
        " ".join(item.get("text", "") for item in case.facts_background),
        " ".join(case.procedural_alerts),
        " ".join(case.tags),
    ]
    return "\n".join(part.strip() for part in parts if part and str(part).strip())


def build_structured_features(case: Case) -> dict[str, Any]:
    document_confidences = [
        float(document.ocr_confidence_summary)
        for document in case.documents
        if getattr(document, "ocr_confidence_summary", None) is not None
    ]
    grounded_counts = [
        len(artifact.grounding_links)
        for artifact in case.intelligence_artifacts
    ]
    run_groundings = [len(run.grounding_links) for run in case.chamber_runs]
    return {
        "forum": case.forum,
        "matter_type": case.matter_type,
        "status": case.status.value,
        "priority": case.priority.value,
        "filing_stage": case.filing_stage,
        "tag_count": _safe_count(case.tags),
        "issue_count": _safe_count(case.legal_issues),
        "risk_flag_count": _safe_count(case.risk_flags),
        "procedural_alert_count": _safe_count(case.procedural_alerts),
        "document_count": _safe_count(case.documents),
        "note_count": _safe_count(case.notes),
        "research_count": _safe_count(case.research_entries),
        "draft_count": _safe_count(case.drafts),
        "artifact_count": _safe_count(case.intelligence_artifacts),
        "run_count": _safe_count(case.chamber_runs),
        "grounded_artifact_count": sum(1 for count in grounded_counts if count > 0),
        "grounded_run_count": sum(1 for count in run_groundings if count > 0),
        "grounding_link_count": sum(grounded_counts) + sum(run_groundings),
        "avg_document_ocr_confidence": round(mean(document_confidences), 4)
        if document_confidences
        else 0.0,
        "has_hearing_date": 1 if case.next_hearing_date else 0,
    }
