from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.agent_log import AgentRunLog
from app.models.case import Case
from app.models.document import Document
from app.models.enums import (
    AgentRunStatus,
    ChamberTaskType,
    GroundingUsageType,
    IntelligenceArtifactType,
    IntelligenceStatus,
)
from app.models.intelligence_artifact import IntelligenceArtifact
from app.services.grounding.provenance import persist_grounding_links
from app.services.knowledge.retrieval import LegalRetrievalBundle, retrieve_case_legal_grounding
from app.services.intelligence.document_extraction import can_extract_document, process_document
from app.services.llm.base import CaseContext, DocumentContext, GroundedSourceContext, GroundingContext


def dedupe(items: list[str]) -> list[str]:
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


def select_documents(case: Case, document_ids: list[str] | None = None) -> list[Document]:
    if not document_ids:
        return list(case.documents)
    wanted = set(document_ids)
    return [document for document in case.documents if document.id in wanted]


def build_case_context(
    db: Session,
    case: Case,
    *,
    document_ids: list[str] | None = None,
) -> CaseContext:
    selected_documents = select_documents(case, document_ids)
    if not selected_documents:
        selected_documents = list(case.documents)

    processed_documents: list[Document] = []
    for document in selected_documents:
        if document.intelligence_status == IntelligenceStatus.PROCESSED:
            processed_documents.append(document)
            continue
        if can_extract_document(document):
            processed_documents.append(process_document(db, document))
        else:
            processed_documents.append(document)

    document_context = [
        DocumentContext(
            id=document.id,
            name=document.name,
            document_type=document.document_type.value,
            summary=document.summary,
            excerpt=(document.extracted_text or document.extracted_text_preview or document.summary).strip()[:1500],
            tags=document.tags,
        )
        for document in processed_documents
    ]

    source_parts = [
        case.summary,
        *(fact.get("text", "") for fact in case.facts_background),
        *(document.excerpt for document in document_context),
        *(note.content for note in case.notes),
    ]
    source_excerpt = "\n\n".join(part.strip() for part in source_parts if part.strip())[:7000]

    return CaseContext(
        case_id=case.id,
        title=case.title,
        case_number=case.case_number,
        forum=case.forum,
        matter_type=case.matter_type,
        client_name=case.client_name,
        opposing_party=case.opposing_party,
        summary=case.summary,
        legal_issues=list(case.legal_issues),
        relief_sought=list(case.relief_sought),
        assigned_counsel=list(case.assigned_counsel),
        filing_stage=case.filing_stage,
        next_hearing_date=case.next_hearing_date.isoformat() if case.next_hearing_date else None,
        risk_flags=list(case.risk_flags),
        important_notes=list(case.important_notes),
        facts_background=list(case.facts_background),
        linked_statutes=list(case.linked_statutes),
        precedents=list(case.precedents),
        procedural_alerts=list(case.procedural_alerts),
        documents=document_context,
        timeline=[
            {
                "title": event.title,
                "date": event.event_date.isoformat(),
                "description": event.description,
                "actor": event.actor,
                "type": event.event_type.value,
            }
            for event in sorted(case.timeline_events, key=lambda item: item.event_date, reverse=True)
        ],
        notes=[
            {
                "title": note.title,
                "content": note.content,
                "type": note.note_type.value,
                "author": note.author,
            }
            for note in sorted(case.notes, key=lambda item: item.updated_at, reverse=True)
        ],
        research_entries=[
            {
                "title": entry.title,
                "summary": entry.summary,
                "query": entry.query,
                "citations": entry.citations,
            }
            for entry in sorted(case.research_entries, key=lambda item: item.updated_at, reverse=True)
        ],
        source_excerpt=source_excerpt,
    )


def create_artifact(
    db: Session,
    *,
    case_id: str,
    artifact_type: IntelligenceArtifactType,
    title: str,
    content: str,
    structured_json: dict,
    source: str,
    status: IntelligenceStatus,
    document_id: str | None = None,
) -> IntelligenceArtifact:
    artifact = IntelligenceArtifact(
        case_id=case_id,
        document_id=document_id,
        artifact_type=artifact_type,
        title=title,
        content=content,
        structured_json=structured_json,
        source=source,
        status=status,
    )
    db.add(artifact)
    db.flush()
    return artifact


def create_generation_log(
    db: Session,
    *,
    case_id: str,
    agent_name: str,
    title: str,
    task_type: str,
    input_summary: str,
    output_summary: str,
    next_action: str,
    citations: list[str],
    confidence_score: float,
    metadata_json: dict,
) -> AgentRunLog:
    timestamp = datetime.now(timezone.utc)
    log = AgentRunLog(
        case_id=case_id,
        agent_name=agent_name,
        title=title,
        task_type=task_type,
        input_summary=input_summary,
        output_summary=output_summary,
        status=AgentRunStatus.COMPLETED,
        confidence_score=confidence_score,
        citations=dedupe(citations),
        next_action=next_action,
        started_at=timestamp,
        completed_at=timestamp,
        metadata_json=metadata_json,
    )
    db.add(log)
    db.flush()
    return log


def build_grounding_context(
    db: Session,
    case: Case,
    *,
    task_type: ChamberTaskType,
    instruction: str,
    focus_issue: str | None = None,
) -> tuple[GroundingContext, LegalRetrievalBundle]:
    retrieved = retrieve_case_legal_grounding(
        db,
        case=case,
        instruction=instruction,
        task_type=task_type,
        focus_issue=focus_issue,
        limit=6,
        required=True,
    )
    grounding = GroundingContext(
        query=retrieved.query,
        status=retrieved.status,
        summary=retrieved.summary,
        sources=[
            GroundedSourceContext(
                source_id=source.source_id,
                chunk_id=source.chunk_id,
                title=source.title,
                short_title=source.short_title,
                citation_label=source.citation_label,
                source_type=source.source_type,
                category=source.category,
                act_name=source.act_name,
                section_label=source.section_label,
                excerpt=source.excerpt,
                relevance_score=source.relevance_score,
            )
            for source in retrieved.sources
        ],
    )
    return grounding, retrieved


def attach_grounding_to_artifact(
    db: Session,
    artifact: IntelligenceArtifact,
    *,
    retrieved: LegalRetrievalBundle,
    usage_type: GroundingUsageType = GroundingUsageType.RELIED_ON,
) -> None:
    if not retrieved.sources:
        return
    persist_grounding_links(
        db,
        artifact=artifact,
        sources=retrieved.sources,
        usage_type=usage_type,
    )
