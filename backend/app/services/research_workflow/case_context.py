from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.case import Case
from app.models.enums import MlTaskName


MAX_CONTEXT_CHARS = 70000


def _value_list(values: list[str] | None) -> str:
    return "; ".join(item for item in (values or []) if item)


def _facts(case: Case) -> str:
    facts = []
    for item in case.facts_background or []:
        label = str(item.get("label") or "Fact")
        text = str(item.get("text") or "").strip()
        if text:
            facts.append(f"{label}: {text}")
    if case.summary:
        facts.insert(0, case.summary)
    return "\n".join(facts)


def _document_payload(case: Case, include_documents: bool) -> list[dict[str, Any]]:
    if not include_documents:
        return []
    documents: list[dict[str, Any]] = []
    for document in sorted(case.documents, key=lambda item: item.upload_date, reverse=True):
        text = document.extracted_text or document.extracted_text_preview or document.summary or ""
        documents.append(
            {
                "id": document.id,
                "name": document.name,
                "type": document.document_type.value,
                "status": document.status.value,
                "extractionStatus": document.extraction_status.value,
                "ocrStatus": document.ocr_status.value,
                "summary": document.summary,
                "text": text,
                "pages": document.pages,
            }
        )
    return documents


def _note_payload(case: Case, include_prior_notes: bool) -> list[dict[str, Any]]:
    if not include_prior_notes:
        return []
    return [
        {
            "id": note.id,
            "title": note.title,
            "type": note.note_type.value,
            "author": note.author,
            "content": note.content,
        }
        for note in sorted(case.notes, key=lambda item: item.updated_at, reverse=True)
    ]


def _timeline_payload(case: Case, include_timeline: bool) -> list[dict[str, Any]]:
    if not include_timeline:
        return []
    return [
        {
            "id": event.id,
            "title": event.title,
            "type": event.event_type.value,
            "date": event.event_date.isoformat(),
            "actor": event.actor,
            "description": event.description,
        }
        for event in sorted(case.timeline_events, key=lambda item: (item.event_date, item.created_at), reverse=True)
    ]


def _prediction_payload(case: Case) -> list[dict[str, Any]]:
    predictions = []
    for prediction in sorted(case.predictions, key=lambda item: item.created_at, reverse=True):
        predictions.append(
            {
                "taskName": prediction.task_name.value
                if isinstance(prediction.task_name, MlTaskName)
                else str(prediction.task_name),
                "predictedLabel": prediction.predicted_label,
                "confidence": prediction.confidence,
                "metadata": prediction.metadata_json,
            }
        )
    return predictions[:8]


def assemble_case_context(db: Session, case_id: str, options: dict[str, Any] | None = None) -> dict[str, Any] | None:
    options = options or {}
    case = db.scalars(
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.documents),
            selectinload(Case.notes),
            selectinload(Case.timeline_events),
            selectinload(Case.research_entries),
            selectinload(Case.chamber_runs),
            selectinload(Case.predictions),
        )
    ).first()
    if case is None:
        return None

    documents = _document_payload(case, bool(options.get("include_documents", True)))
    notes = _note_payload(case, bool(options.get("include_prior_notes", True)))
    timeline = _timeline_payload(case, bool(options.get("include_timeline", True)))
    facts = _facts(case)
    relief_sought = _value_list(case.relief_sought)

    missing_context: list[str] = []
    if not facts.strip():
        missing_context.append("No detailed factual background was available.")
    if not relief_sought.strip():
        missing_context.append("No specific relief sought was recorded.")
    if not documents:
        missing_context.append("No processed documents were available for this run.")
    if documents and not any(document.get("text") for document in documents):
        missing_context.append("Documents exist, but no extracted text was available.")

    document_text = "\n\n".join(
        f"Document: {document['name']}\n{document.get('summary') or ''}\n{document.get('text') or ''}"
        for document in documents
        if document.get("summary") or document.get("text")
    )
    notes_text = "\n\n".join(f"Note: {note['title']}\n{note['content']}" for note in notes if note.get("content"))
    timeline_text = "\n".join(
        f"{event['date']} - {event['title']}: {event.get('description') or ''}" for event in timeline
    )
    previous_research = [
        {
            "id": entry.id,
            "title": entry.title,
            "query": entry.query,
            "summary": entry.summary,
            "citations": entry.citations,
            "status": entry.status.value,
        }
        for entry in sorted(case.research_entries, key=lambda item: item.updated_at, reverse=True)[:5]
    ]
    previous_research_text = "\n\n".join(
        f"Prior research: {entry['title']}\n{entry['summary']}" for entry in previous_research
    )

    combined_parts = [
        f"Case title: {case.title}",
        f"Case number: {case.case_number}",
        f"Forum: {case.forum}",
        f"Matter type: {case.matter_type}",
        f"Stage: {case.filing_stage}",
        f"Client: {case.client_name}",
        f"Opposing party: {case.opposing_party}",
        f"Relief sought: {relief_sought}",
        f"Legal issues already recorded: {_value_list(case.legal_issues)}",
        f"Linked statutes: {_value_list(case.linked_statutes)}",
        f"Facts: {facts}",
        document_text,
        notes_text,
        timeline_text,
        previous_research_text,
    ]
    combined_text = "\n\n".join(part for part in combined_parts if part and part.strip())[:MAX_CONTEXT_CHARS]

    return {
        "case_id": case.id,
        "case_title": case.title,
        "case_number": case.case_number,
        "forum": case.forum,
        "court": case.forum,
        "matter_type": case.matter_type,
        "stage": case.filing_stage,
        "client": case.client_name,
        "opposing_party": case.opposing_party,
        "facts": facts,
        "relief_sought": relief_sought,
        "recorded_issues": list(case.legal_issues or []),
        "linked_statutes": list(case.linked_statutes or []),
        "precedents": list(case.precedents or []),
        "risk_flags": list(case.risk_flags or []),
        "documents": documents,
        "notes": notes,
        "timeline": timeline,
        "previous_research": previous_research,
        "predictions": _prediction_payload(case),
        "combined_text": combined_text,
        "missing_context": missing_context,
    }
