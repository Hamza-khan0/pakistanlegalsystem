from pathlib import Path

from app.models.agent_log import AgentRunLog
from app.models.case import Case
from app.models.chamber_run import ChamberRun
from app.models.chamber_run_step import ChamberRunStep
from app.models.corpus_entry import CorpusEntry
from app.models.crawl_job import CrawlJob
from app.models.crawl_source import CrawlSource
from app.models.crawled_document import CrawledDocument
from app.models.document import Document
from app.models.draft import Draft
from app.models.embedding_index_metadata import EmbeddingIndexMetadata
from app.models.grounding_link import GroundingLink
from app.models.intelligence_artifact import IntelligenceArtifact
from app.models.legal_source import LegalSource
from app.models.legal_source_chunk import LegalSourceChunk
from app.models.ml_dataset import MlDataset
from app.models.ml_model import MlModel
from app.models.case_prediction import CasePrediction
from app.models.enums import AgentRunStatus, PriorityLevel
from app.models.note import Note
from app.models.research import ResearchEntry
from app.models.timeline import TimelineEvent
from app.schemas.legal_sources import GroundingSourceRead, LegalSourceChunkRead, LegalSourceRead
from app.schemas.ml import CasePredictionRead, MlDatasetRead, MlLeaderboardEntry, MlModelRead, MlTaskLeaderboardRead
from app.schemas.retrieval import EmbeddingIndexRead
from app.schemas.corpus import CorpusEntryRead
from app.schemas.crawl import CrawlJobRead, CrawledDocumentRead, CrawlSourceRead
from app.schemas.agent_log import AgentRunLogRead
from app.schemas.case import CaseRead
from app.schemas.case_detail import CaseDetailRead
from app.schemas.common import CaseFactRead, DashboardActivityRead, DeadlineRead, NotificationRead
from app.schemas.document import DocumentRead
from app.schemas.draft import DraftRead
from app.schemas.intelligence import IntelligenceArtifactRead
from app.schemas.note import NoteRead
from app.schemas.research import ResearchEntryRead
from app.schemas.runs import AgentActivityRead, ChamberRunRead, ChamberRunStepRead, ChamberRunSummaryRead, MemorySourceRead
from app.schemas.timeline import TimelineEventRead


def serialize_case(case: Case) -> CaseRead:
    return CaseRead(
        id=case.id,
        title=case.title,
        case_number=case.case_number,
        forum=case.forum,
        matter_type=case.matter_type,
        status=case.status,
        priority=case.priority,
        client=case.client_name,
        opposing_party=case.opposing_party,
        summary=case.summary,
        issues=case.legal_issues,
        relief_sought=case.relief_sought,
        next_hearing_date=case.next_hearing_date,
        assigned_counsel=case.assigned_counsel,
        stage=case.filing_stage,
        risk_flags=case.risk_flags,
        important_notes=case.important_notes,
        facts_background=[CaseFactRead(**fact) for fact in case.facts_background],
        linked_statutes=case.linked_statutes,
        precedents=case.precedents,
        procedural_alerts=case.procedural_alerts,
        tags=case.tags,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def build_file_url(file_path: str) -> str:
    path = Path(file_path).as_posix().replace("\\", "/")
    uploads_index = path.find("/uploads/")
    if uploads_index != -1:
        return path[uploads_index:]
    crawl_storage_index = path.find("/crawl_storage/")
    if crawl_storage_index != -1:
        return path[crawl_storage_index:].replace("/crawl_storage/", "/crawl-storage/", 1)
    uploads_index = path.find("uploads/")
    if uploads_index != -1:
        return "/" + path[uploads_index:]
    crawl_storage_index = path.find("crawl_storage/")
    if crawl_storage_index != -1:
        return "/" + path[crawl_storage_index:].replace("crawl_storage/", "crawl-storage/", 1)
    return path


def serialize_document(document: Document) -> DocumentRead:
    case = document.case
    return DocumentRead(
        id=document.id,
        case_id=document.case_id,
        name=document.name,
        type=document.document_type,
        status=document.status,
        category=document.category,
        file_name=document.file_name,
        file_path=document.file_path,
        file_url=build_file_url(document.file_path),
        mime_type=document.mime_type,
        tags=document.tags,
        upload_date=document.upload_date,
        extraction_status=document.extraction_status,
        ocr_status=document.ocr_status,
        parsing_status=document.parsing_status,
        intelligence_status=document.intelligence_status,
        preview_text=document.extracted_text_preview,
        extracted_text=document.extracted_text,
        extraction_error=document.extraction_error,
        processed_at=document.processed_at,
        summary=document.summary,
        filed_by=document.filed_by,
        pages=document.pages,
        metadata_json=document.metadata_json,
        created_at=document.created_at,
        updated_at=document.updated_at,
        case_title=case.title if case else None,
        case_number=case.case_number if case else None,
        case_forum=case.forum if case else None,
        case_priority=case.priority if case else None,
    )


def serialize_timeline_event(event: TimelineEvent) -> TimelineEventRead:
    return TimelineEventRead(
        id=event.id,
        case_id=event.case_id,
        title=event.title,
        type=event.event_type,
        description=event.description,
        actor=event.actor,
        date=event.event_date,
        created_at=event.created_at,
    )


def serialize_note(note: Note) -> NoteRead:
    return NoteRead(
        id=note.id,
        case_id=note.case_id,
        title=note.title,
        content=note.content,
        note_type=note.note_type,
        author=note.author,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def serialize_research_entry(entry: ResearchEntry) -> ResearchEntryRead:
    return ResearchEntryRead(
        id=entry.id,
        case_id=entry.case_id,
        title=entry.title,
        query=entry.query,
        summary=entry.summary,
        citations=entry.citations,
        source_type=entry.source_type,
        status=entry.status,
        author=entry.author,
        next_question=entry.next_question,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def serialize_draft(draft: Draft) -> DraftRead:
    return DraftRead(
        id=draft.id,
        case_id=draft.case_id,
        title=draft.title,
        type=draft.draft_type,
        status=draft.status,
        content=draft.content,
        version=draft.version,
        owner=draft.owner,
        summary=draft.summary,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


def serialize_agent_log(log: AgentRunLog) -> AgentRunLogRead:
    if log.status == AgentRunStatus.COMPLETED:
        confidence = f"{round((log.confidence_score or 0) * 100)}%"
    else:
        confidence = log.status.value

    return AgentRunLogRead(
        id=log.id,
        case_id=log.case_id,
        agent_name=log.agent_name,
        title=log.title,
        task_type=log.task_type,
        input_summary=log.input_summary,
        output_summary=log.output_summary,
        status=log.status,
        confidence_score=log.confidence_score,
        citations=log.citations,
        next_action=log.next_action,
        metadata_json=log.metadata_json,
        started_at=log.started_at,
        completed_at=log.completed_at,
        confidence=confidence,
    )


def serialize_grounding_link(link: GroundingLink) -> GroundingSourceRead:
    source = link.source
    return GroundingSourceRead(
        source_id=source.id,
        chunk_id=link.chunk_id,
        title=source.title,
        short_title=source.short_title,
        citation_label=source.citation_label,
        source_type=source.source_type.value,
        category=source.category,
        act_name=source.act_name,
        section_label=source.section_label,
        language=source.language,
        source_origin=str(source.metadata_json.get("originKind") or "Seeded Legal Source"),
        source_url=str(source.metadata_json.get("sourceUrl") or ""),
        excerpt=link.excerpt or (link.chunk.text[:360] if link.chunk else source.content[:360]),
        relevance_score=link.relevance_score,
        lexical_score=(link.metadata_json or {}).get("lexicalScore"),
        semantic_score=(link.metadata_json or {}).get("semanticScore"),
        rerank_score=(link.metadata_json or {}).get("rerankScore"),
        retrieval_mode=str((link.metadata_json or {}).get("retrievalMode") or "Lexical"),
        explanation=str((link.metadata_json or {}).get("explanation") or ""),
        usage_type=link.usage_type,
    )


def serialize_embedding_index(index: EmbeddingIndexMetadata) -> EmbeddingIndexRead:
    return EmbeddingIndexRead(
        id=index.id,
        name=index.name,
        retrieval_mode=index.retrieval_mode,
        model_name=index.model_name,
        status=index.status,
        corpus_version=index.corpus_version,
        index_path=index.index_path,
        vector_dimension=index.vector_dimension,
        source_count=index.source_count,
        metadata_json=index.metadata_json,
        created_at=index.created_at,
        updated_at=index.updated_at,
    )


def serialize_legal_source_chunk(chunk: LegalSourceChunk) -> LegalSourceChunkRead:
    return LegalSourceChunkRead(
        id=chunk.id,
        source_id=chunk.source_id,
        chunk_index=chunk.chunk_index,
        heading=chunk.heading,
        text=chunk.text,
        token_count=chunk.token_count,
        metadata_json=chunk.metadata_json,
    )


def serialize_legal_source(source: LegalSource) -> LegalSourceRead:
    return LegalSourceRead(
        id=source.id,
        source_type=source.source_type,
        title=source.title,
        short_title=source.short_title,
        jurisdiction=source.jurisdiction,
        category=source.category,
        act_name=source.act_name,
        section_label=source.section_label,
        section_number=source.section_number,
        order_rule_label=source.order_rule_label,
        year=source.year,
        language=source.language,
        citation_label=source.citation_label,
        content=source.content,
        source_origin=str(source.metadata_json.get("originKind") or "Seeded Legal Source"),
        source_url=str(source.metadata_json.get("sourceUrl") or ""),
        metadata_json=source.metadata_json,
        chunks=[serialize_legal_source_chunk(chunk) for chunk in source.chunks],
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


def serialize_crawl_source(source: CrawlSource) -> CrawlSourceRead:
    return CrawlSourceRead(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        base_url=source.base_url,
        allowed_domains=source.allowed_domains,
        crawl_mode=source.crawl_mode,
        language_hint=source.language_hint,
        category=source.category,
        is_active=source.is_active,
        config_json=source.config_json,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


def serialize_crawl_job(job: CrawlJob) -> CrawlJobRead:
    return CrawlJobRead(
        id=job.id,
        source_id=job.source_id,
        source_name=job.source.name if job.source else "",
        status=job.status,
        started_at=job.started_at,
        completed_at=job.completed_at,
        pages_fetched=job.pages_fetched,
        documents_discovered=job.documents_discovered,
        documents_saved=job.documents_saved,
        errors_count=job.errors_count,
        metadata_json=job.metadata_json,
    )


def serialize_crawled_document(document: CrawledDocument) -> CrawledDocumentRead:
    return CrawledDocumentRead(
        id=document.id,
        source_id=document.source_id,
        source_name=document.source.name if document.source else "",
        legal_source_id=document.legal_source_id,
        source_url=document.source_url,
        title=document.title,
        document_type=document.document_type,
        language=document.language,
        jurisdiction=document.jurisdiction,
        raw_html_path=document.raw_html_path,
        raw_html_url=build_file_url(document.raw_html_path) if document.raw_html_path else "",
        downloaded_file_path=document.downloaded_file_path,
        downloaded_file_url=build_file_url(document.downloaded_file_path) if document.downloaded_file_path else "",
        mime_type=document.mime_type,
        crawl_status=document.crawl_status,
        processing_status=document.processing_status,
        duplicate_hash=document.duplicate_hash,
        extracted_text=document.extracted_text,
        extracted_text_preview=document.extracted_text_preview,
        normalized_text=document.normalized_text,
        ocr_engine=document.ocr_engine,
        ocr_status=document.ocr_status,
        ocr_confidence_summary=document.ocr_confidence_summary,
        language_detected=document.language_detected,
        page_count=document.page_count,
        errors_json=document.errors_json,
        processed_at=document.processed_at,
        metadata_json=document.metadata_json,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def serialize_corpus_entry(entry: CorpusEntry) -> CorpusEntryRead:
    return CorpusEntryRead(
        id=entry.id,
        source_kind=entry.source_kind,
        crawled_document_id=entry.crawled_document_id,
        legal_source_id=entry.legal_source_id,
        title=entry.title,
        language=entry.language,
        normalized_text=entry.normalized_text,
        chunk_count=entry.chunk_count,
        ready_for_retrieval=entry.ready_for_retrieval,
        ready_for_training=entry.ready_for_training,
        dataset_split=entry.dataset_split,
        metadata_json=entry.metadata_json,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def serialize_intelligence_artifact(artifact: IntelligenceArtifact) -> IntelligenceArtifactRead:
    legal_sources = [serialize_grounding_link(link) for link in artifact.grounding_links]
    return IntelligenceArtifactRead(
        id=artifact.id,
        case_id=artifact.case_id,
        document_id=artifact.document_id,
        artifact_type=artifact.artifact_type,
        title=artifact.title,
        content=artifact.content,
        structured_json=artifact.structured_json,
        source=artifact.source,
        status=artifact.status,
        grounding_status=str(
            artifact.structured_json.get("groundingStatus")
            or ("Grounded" if legal_sources else "Retrieval not used")
        ),
        legal_sources=legal_sources,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


def serialize_ml_dataset(dataset: MlDataset) -> MlDatasetRead:
    return MlDatasetRead(
        id=dataset.id,
        task_name=dataset.task_name,
        name=dataset.name,
        version=dataset.version,
        status=dataset.status,
        record_count=dataset.record_count,
        label_strategy=dataset.label_strategy,
        split_strategy=dataset.split_strategy,
        data_path=dataset.data_path,
        report_path=dataset.report_path,
        report_json=dataset.report_json,
        notes=dataset.notes,
        metadata_json=dataset.metadata_json,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


def serialize_ml_model(model: MlModel) -> MlModelRead:
    return MlModelRead(
        id=model.id,
        dataset_id=model.dataset_id,
        task_name=model.task_name,
        model_family=model.model_family,
        name=model.name,
        status=model.status,
        artifact_path=model.artifact_path,
        metrics_path=model.metrics_path,
        metrics_json=model.metrics_json,
        config_json=model.config_json,
        label_schema=model.label_schema,
        training_summary=model.training_summary,
        metadata_json=model.metadata_json,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def serialize_case_prediction(prediction: CasePrediction) -> CasePredictionRead:
    model = prediction.model
    return CasePredictionRead(
        id=prediction.id,
        case_id=prediction.case_id,
        model_id=prediction.model_id,
        task_name=prediction.task_name,
        predicted_label=prediction.predicted_label,
        confidence=prediction.confidence,
        probabilities_json=prediction.probabilities_json,
        input_summary=prediction.input_summary,
        warning_text=prediction.warning_text,
        metadata_json=prediction.metadata_json,
        created_at=prediction.created_at,
        model_name=model.name if model else "",
        model_family=model.model_family if model else "Baseline",
        dataset_id=model.dataset_id if model else "",
    )


def serialize_ml_leaderboard(task_name, models: list[MlModel]) -> MlTaskLeaderboardRead:
    entries = [
        MlLeaderboardEntry(
            model_id=model.id,
            name=model.name,
            model_family=model.model_family,
            primary_metric=float(model.metrics_json.get("primaryMetric", 0.0)),
            metrics_json=model.metrics_json,
            created_at=model.created_at,
        )
        for model in models
    ]
    return MlTaskLeaderboardRead(task_name=task_name, entries=entries)


def _serialize_memory_source(item: object) -> MemorySourceRead | None:
    if not isinstance(item, dict):
        return None

    source_id = item.get("sourceId") or item.get("source_id")
    source_type = item.get("sourceType") or item.get("source_type")
    title = item.get("title")
    if not isinstance(source_id, str) or not isinstance(source_type, str) or not isinstance(title, str):
        return None

    detail = item.get("detail") if isinstance(item.get("detail"), str) else ""
    excerpt = item.get("excerpt") if isinstance(item.get("excerpt"), str) else ""

    return MemorySourceRead(
        source_id=source_id,
        source_type=source_type,
        title=title,
        detail=detail,
        excerpt=excerpt,
    )


def _run_memory_sources(run: ChamberRun) -> list[MemorySourceRead]:
    raw_sources = run.metadata_json.get("memorySources")
    if not isinstance(raw_sources, list):
        return []
    return [source for source in (_serialize_memory_source(item) for item in raw_sources) if source is not None]


def serialize_chamber_run_step(step: ChamberRunStep) -> ChamberRunStepRead:
    return ChamberRunStepRead(
        id=step.id,
        run_id=step.run_id,
        step_order=step.step_order,
        agent_name=step.agent_name,
        task_label=step.task_label,
        input_summary=step.input_summary,
        output_summary=step.output_summary,
        full_output=step.full_output,
        structured_json=step.structured_json,
        status=step.status,
        confidence_score=step.confidence_score,
        source_artifact_ids=step.source_artifact_ids,
        metadata_json=step.metadata_json,
        created_at=step.created_at,
        completed_at=step.completed_at,
    )


def serialize_chamber_run_summary(run: ChamberRun) -> ChamberRunSummaryRead:
    steps = sorted(run.steps, key=lambda item: item.step_order)
    legal_sources = [serialize_grounding_link(link) for link in run.grounding_links]
    return ChamberRunSummaryRead(
        id=run.id,
        case_id=run.case_id,
        task_type=run.task_type,
        user_instruction=run.user_instruction,
        selected_workflow=run.selected_workflow,
        status=run.status,
        final_summary=run.final_summary,
        confidence_score=run.confidence_score,
        agent_names=list(dict.fromkeys(step.agent_name for step in steps)),
        memory_sources=_run_memory_sources(run),
        critic_summary=str(run.metadata_json.get("criticSummary") or ""),
        final_artifact_id=run.metadata_json.get("finalArtifactId"),
        linked_draft_id=run.metadata_json.get("linkedDraftId"),
        linked_research_entry_id=run.metadata_json.get("linkedResearchEntryId"),
        grounding_status=str(run.metadata_json.get("legalGroundingStatus") or ("Grounded" if legal_sources else "Retrieval not used")),
        retrieval_mode=str(run.metadata_json.get("retrievalMode") or "Lexical"),
        retrieval_diagnostics={
            "weights": run.metadata_json.get("retrievalWeights", {}),
            "semanticIndex": run.metadata_json.get("semanticIndex", {}),
        },
        legal_retrieval_query=str(run.metadata_json.get("legalRetrievalQuery") or ""),
        legal_source_count=len(legal_sources),
        legal_sources=legal_sources,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


def serialize_chamber_run(run: ChamberRun) -> ChamberRunRead:
    summary = serialize_chamber_run_summary(run).model_dump()
    return ChamberRunRead(
        **summary,
        final_output=run.final_output,
        steps=[serialize_chamber_run_step(step) for step in sorted(run.steps, key=lambda item: item.step_order)],
        metadata_json=run.metadata_json,
    )


def serialize_agent_activity(step: ChamberRunStep) -> AgentActivityRead:
    run = step.run
    case = run.case
    return AgentActivityRead(
        step_id=step.id,
        run_id=run.id,
        case_id=case.id,
        case_title=case.title,
        agent_name=step.agent_name,
        task_label=step.task_label,
        status=step.status,
        output_summary=step.output_summary,
        confidence_score=step.confidence_score,
        completed_at=step.completed_at,
    )


def serialize_case_detail(
    case: Case,
    *,
    legal_basis: list[GroundingLink] | None = None,
) -> CaseDetailRead:
    base = serialize_case(case).model_dump()
    return CaseDetailRead(
        **base,
        documents=[
            serialize_document(document)
            for document in sorted(case.documents, key=lambda item: item.upload_date, reverse=True)
        ],
        timeline=[
            serialize_timeline_event(event)
            for event in sorted(
                case.timeline_events,
                key=lambda item: (item.event_date, item.created_at),
                reverse=True,
            )
        ],
        notes=[
            serialize_note(note)
            for note in sorted(case.notes, key=lambda item: item.updated_at, reverse=True)
        ],
        research=[
            serialize_research_entry(entry)
            for entry in sorted(case.research_entries, key=lambda item: item.updated_at, reverse=True)
        ],
        drafts=[
            serialize_draft(draft)
            for draft in sorted(case.drafts, key=lambda item: item.updated_at, reverse=True)
        ],
        agent_outputs=[
            serialize_agent_log(log)
            for log in sorted(case.agent_run_logs, key=lambda item: item.started_at, reverse=True)
        ],
        intelligence=[
            serialize_intelligence_artifact(artifact)
            for artifact in sorted(
                case.intelligence_artifacts,
                key=lambda item: item.updated_at,
                reverse=True,
            )
        ],
        runs=[
            serialize_chamber_run_summary(run)
            for run in sorted(case.chamber_runs, key=lambda item: item.started_at, reverse=True)
        ],
        legal_basis=[serialize_grounding_link(link) for link in (legal_basis or [])],
    )


def make_deadline(
    *,
    item_id: str,
    case_id: str,
    title: str,
    due_date,
    owner: str,
    severity: str,
    note: str,
) -> DeadlineRead:
    return DeadlineRead(
        id=item_id,
        case_id=case_id,
        title=title,
        due_date=due_date,
        owner=owner,
        severity=severity,
        note=note,
    )


def make_activity(
    *,
    item_id: str,
    title: str,
    detail: str,
    timestamp: str,
    category: str,
) -> DashboardActivityRead:
    return DashboardActivityRead(
        id=item_id,
        title=title,
        detail=detail,
        timestamp=timestamp,
        category=category,
    )


def make_notification(
    *,
    item_id: str,
    title: str,
    detail: str,
    timestamp,
    tone: str,
) -> NotificationRead:
    return NotificationRead(
        id=item_id,
        title=title,
        detail=detail,
        timestamp=timestamp,
        tone=tone,
    )


def severity_from_priority(priority: PriorityLevel) -> str:
    return priority.value
