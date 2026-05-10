from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm.attributes import flag_modified

from app.models.research_run import ResearchRun
from app.schemas.research import LEGAL_RESEARCH_WARNING


def _value(data: dict[str, Any], snake: str, camel: str, default: Any = None) -> Any:
    return data.get(snake, data.get(camel, default))


def normalize_generated_draft(draft: dict[str, Any] | None) -> dict[str, Any] | None:
    if not draft:
        return None

    draft_markdown = str(_value(draft, "draft_markdown", "draftMarkdown", "") or "")
    edited = _value(draft, "edited_draft_markdown", "editedDraftMarkdown")
    edited_text = str(edited) if edited not in (None, "") else None
    final_text = edited_text or str(_value(draft, "final_draft_markdown", "finalDraftMarkdown", draft_markdown) or "")

    return {
        "draft_type": str(_value(draft, "draft_type", "draftType", "research_memo") or "research_memo"),
        "title": str(draft.get("title") or "Generated Legal Draft"),
        "draft_markdown": draft_markdown,
        "edited_draft_markdown": edited_text,
        "final_draft_markdown": final_text,
        "sections": list(draft.get("sections") or []),
        "authorities_used": list(_value(draft, "authorities_used", "authoritiesUsed", []) or []),
        "facts_used": list(_value(draft, "facts_used", "factsUsed", []) or []),
        "assumptions": list(draft.get("assumptions") or []),
        "missing_information": list(_value(draft, "missing_information", "missingInformation", []) or []),
        "lawyer_review_checklist": list(
            _value(draft, "lawyer_review_checklist", "lawyerReviewChecklist", []) or []
        ),
        "legal_authority_warning": str(
            _value(draft, "legal_authority_warning", "legalAuthorityWarning", LEGAL_RESEARCH_WARNING)
            or LEGAL_RESEARCH_WARNING
        ),
        "last_edited_at": _value(draft, "last_edited_at", "lastEditedAt"),
        "pdf_stale": bool(_value(draft, "pdf_stale", "pdfStale", False)),
        "pdf_generated_at": _value(draft, "pdf_generated_at", "pdfGeneratedAt"),
        "previous_draft_markdown": _value(draft, "previous_draft_markdown", "previousDraftMarkdown"),
        "_llm_used": bool(draft.get("_llm_used", False)),
        "_llm_warning": draft.get("_llm_warning"),
        "edit_notes": list(_value(draft, "edit_notes", "editNotes", []) or []),
    }


def get_final_draft_markdown(payload: dict[str, Any] | None) -> str:
    draft = normalize_generated_draft(payload)
    return str(draft.get("final_draft_markdown") or "" if draft else "")


def set_edited_draft_markdown(
    run: ResearchRun,
    edited_text: str,
    *,
    edit_note: str | None = None,
) -> dict[str, Any]:
    draft = normalize_generated_draft(run.generated_draft_json)
    if not draft or not draft.get("draft_markdown"):
        raise ValueError("No generated draft is available for this run.")

    edited_text = edited_text.strip()
    if not edited_text:
        raise ValueError("Edited draft cannot be empty.")

    edited_at = datetime.now(UTC).isoformat()
    draft["edited_draft_markdown"] = edited_text
    draft["final_draft_markdown"] = edited_text
    draft["last_edited_at"] = edited_at
    draft["pdf_stale"] = True
    if edit_note:
        notes = list(draft.get("edit_notes") or [])
        notes.append({"note": edit_note.strip(), "edited_at": edited_at})
        draft["edit_notes"] = notes

    run.generated_draft_json = draft
    flag_modified(run, "generated_draft_json")
    return draft


def mark_pdf_generated(run: ResearchRun) -> dict[str, Any]:
    draft = normalize_generated_draft(run.generated_draft_json)
    if not draft or not draft.get("draft_markdown"):
        raise ValueError("No generated draft is available for this run.")
    draft["pdf_stale"] = False
    draft["pdf_generated_at"] = datetime.now(UTC).isoformat()
    run.generated_draft_json = draft
    flag_modified(run, "generated_draft_json")
    return draft


def research_draft_response_payload(run: ResearchRun) -> dict[str, Any]:
    draft = normalize_generated_draft(run.generated_draft_json)
    if not draft or not draft.get("draft_markdown"):
        raise ValueError("No generated draft is available for this run.")
    return {
        "run_id": run.id,
        "case_id": run.case_id,
        "saved": True,
        "draft_markdown": draft["draft_markdown"],
        "edited_draft_markdown": draft.get("edited_draft_markdown"),
        "final_draft_markdown": draft["final_draft_markdown"],
        "last_edited_at": draft.get("last_edited_at"),
        "generated_draft": draft,
        "legal_authority_warning": LEGAL_RESEARCH_WARNING,
    }
