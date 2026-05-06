from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.case import Case
from app.models.enums import ChamberTaskType
from app.models.legal_source import LegalSource
from app.models.legal_source_chunk import LegalSourceChunk
from app.services.corpus.normalization import detect_language
from app.services.knowledge.normalization import unique_tokens


@dataclass(slots=True)
class RetrievedLegalSource:
    source_id: str
    chunk_id: str | None
    title: str
    short_title: str
    citation_label: str
    source_type: str
    category: str
    act_name: str
    section_label: str
    language: str
    source_origin: str
    source_url: str
    excerpt: str
    relevance_score: float
    lexical_score: float | None = None
    semantic_score: float | None = None
    rerank_score: float | None = None
    retrieval_mode: str = "Lexical"
    explanation: str = ""
    matched_terms: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LegalRetrievalBundle:
    query: str
    status: str
    summary: str
    sources: list[RetrievedLegalSource] = field(default_factory=list)


def _task_terms(task_type: ChamberTaskType) -> list[str]:
    mapping = {
        ChamberTaskType.SUMMARY: [],
        ChamberTaskType.ISSUE_SPOTTING: ["maintainability", "jurisdiction", "injunction", "plaint"],
        ChamberTaskType.PRELIMINARY_OBJECTIONS: ["maintainability", "jurisdiction", "rejection", "plaint", "barred"],
        ChamberTaskType.HEARING_NOTES: ["injunction", "procedural", "hearing", "interim"],
        ChamberTaskType.DRAFT_OUTLINE: ["grounds", "relief", "injunction", "jurisdiction"],
        ChamberTaskType.DRAFT_REVIEW: ["maintainability", "record", "support", "legal basis"],
        ChamberTaskType.RESEARCH_MEMO: ["statute", "legal basis", "authority", "procedure"],
        ChamberTaskType.PROCEDURAL_CHECK: ["procedural", "hearing", "maintainability", "jurisdiction"],
    }
    return mapping.get(task_type, [])


def build_case_retrieval_query(
    case: Case,
    *,
    instruction: str,
    task_type: ChamberTaskType,
    focus_issue: str | None = None,
) -> str:
    parts = [
        instruction,
        focus_issue or "",
        case.matter_type,
        case.forum,
        case.filing_stage,
        " ".join(case.legal_issues[:3]),
        " ".join(case.linked_statutes[:3]),
        " ".join(case.tags[:4]),
        " ".join(_task_terms(task_type)),
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def _source_tokens(source: LegalSource, chunk: LegalSourceChunk | None) -> set[str]:
    metadata_keywords = source.metadata_json.get("keywords", []) if isinstance(source.metadata_json, dict) else []
    text = " ".join(
        [
            source.title,
            source.short_title,
            source.citation_label,
            source.category,
            source.act_name,
            source.section_label,
            chunk.text if chunk else source.content,
            " ".join(str(keyword) for keyword in metadata_keywords),
        ]
    )
    return set(unique_tokens(text))


def _score_candidate(
    *,
    query_terms: list[str],
    query_text: str,
    task_type: ChamberTaskType,
    source: LegalSource,
    chunk: LegalSourceChunk | None,
    effective_language: str | None,
) -> tuple[float, list[str]]:
    source_terms = _source_tokens(source, chunk)
    matched_terms = [term for term in query_terms if term in source_terms]
    if not matched_terms:
        return 0.0, []

    score = float(len(matched_terms))
    lowered_query = query_text.casefold()
    lowered_title = f"{source.title} {source.citation_label} {source.section_label}".casefold()
    if source.section_label and source.section_label.casefold() in lowered_query:
        score += 3.0
    if source.citation_label and source.citation_label.casefold() in lowered_query:
        score += 2.5
    if any(term in lowered_title for term in matched_terms):
        score += 1.5

    if task_type in {ChamberTaskType.PRELIMINARY_OBJECTIONS, ChamberTaskType.PROCEDURAL_CHECK} and (
        "order" in lowered_title or "rule" in lowered_title or "section 9" in lowered_title
    ):
        score += 1.2
    if task_type in {ChamberTaskType.HEARING_NOTES, ChamberTaskType.DRAFT_OUTLINE} and (
        "injunction" in source.category.casefold() or "order xxxix" in lowered_title
    ):
        score += 1.2
    if "article 199" in lowered_query and "article 199" in lowered_title:
        score += 2.0
    if "service" in lowered_query and "service tribunal" in lowered_title:
        score += 1.6
    if effective_language and effective_language != "Unknown":
        if source.language == effective_language:
            score += 1.1
        elif source.language == "Mixed":
            score += 0.4

    return round(score, 3), matched_terms


def _candidate_excerpt(source: LegalSource, chunk: LegalSourceChunk | None) -> str:
    text = chunk.text if chunk else source.content
    cleaned = " ".join(text.split())
    return cleaned[:360]


def _base_query():
    return select(LegalSource).options(selectinload(LegalSource.chunks))


def search_legal_sources(
    db: Session,
    *,
    query: str,
    task_type: ChamberTaskType = ChamberTaskType.RESEARCH_MEMO,
    limit: int = 8,
    language: str | None = None,
) -> LegalRetrievalBundle:
    query_terms = unique_tokens(query)
    effective_language = language or detect_language(query)
    explicit_language = bool(language and language != "Unknown")
    if not query_terms:
        return LegalRetrievalBundle(
            query=query,
            status="No relevant sources found",
            summary="No searchable legal query terms were supplied.",
            sources=[],
        )

    candidates: list[RetrievedLegalSource] = []
    for source in db.scalars(_base_query()).all():
        candidate_chunks = source.chunks or [None]
        best_result: RetrievedLegalSource | None = None
        for chunk in candidate_chunks:
            score, matched_terms = _score_candidate(
                query_terms=query_terms,
                query_text=query,
                task_type=task_type,
                source=source,
                chunk=chunk,
                effective_language=effective_language,
            )
            if score <= 0:
                continue
            result = RetrievedLegalSource(
                source_id=source.id,
                chunk_id=chunk.id if chunk else None,
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
                excerpt=_candidate_excerpt(source, chunk),
                relevance_score=score,
                lexical_score=score,
                rerank_score=score,
                retrieval_mode="Lexical",
                explanation=(
                    f"Lexical match on {len(matched_terms)} query term"
                    f"{'' if len(matched_terms) == 1 else 's'}."
                ),
                matched_terms=matched_terms[:8],
            )
            if best_result is None or result.relevance_score > best_result.relevance_score:
                best_result = result

        if best_result is not None:
            candidates.append(best_result)

    if explicit_language:
        exact_language_matches = [
            candidate
            for candidate in candidates
            if candidate.language == effective_language or candidate.language == "Mixed"
        ]
        if exact_language_matches:
            candidates = exact_language_matches

    ranked = sorted(candidates, key=lambda item: item.relevance_score, reverse=True)[:limit]
    if not ranked:
        return LegalRetrievalBundle(
            query=query,
            status="No relevant sources found",
            summary="No seeded legal source matched the current query with enough confidence.",
            sources=[],
        )

    status = "Grounded" if len(ranked) >= 3 else "Partially grounded"
    summary = (
        f"Retrieved {len(ranked)} legal source{'s' if len(ranked) != 1 else ''} for the current chamber query."
    )
    return LegalRetrievalBundle(
        query=query,
        status=status,
        summary=summary,
        sources=ranked,
    )


def retrieve_case_legal_grounding(
    db: Session,
    *,
    case: Case,
    instruction: str,
    task_type: ChamberTaskType,
    focus_issue: str | None = None,
    limit: int = 6,
    required: bool = True,
    language: str | None = None,
) -> LegalRetrievalBundle:
    query = build_case_retrieval_query(
        case,
        instruction=instruction,
        task_type=task_type,
        focus_issue=focus_issue,
    )
    bundle = search_legal_sources(
        db,
        query=query,
        task_type=task_type,
        limit=limit,
        language=language,
    )
    if not required and not bundle.sources:
        return LegalRetrievalBundle(
            query=query,
            status="Retrieval not used",
            summary="The selected workflow did not require legal retrieval for this pass.",
            sources=[],
        )
    return bundle
