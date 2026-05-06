from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.case import Case
from app.models.enums import ChamberTaskType, RetrievalMode
from app.services.corpus.normalization import detect_language, unique_tokens
from app.services.knowledge.retrieval import (
    LegalRetrievalBundle,
    RetrievedLegalSource,
    build_case_retrieval_query,
    search_legal_sources,
)
from app.services.knowledge.reranking import reranker_metadata, score_retrieval_candidate
from app.services.knowledge.semantic_index import (
    INDEX_NAME,
    build_semantic_index,
    describe_semantic_query,
    embed_query,
    load_semantic_index,
)


@dataclass(slots=True)
class RetrievalEvaluationResult:
    mode: str
    query: str
    top_labels: list[str]
    source_type_mix: dict[str, int]
    average_score: float
    diagnostics: dict[str, Any]


def _task_weights(task_type: ChamberTaskType) -> tuple[float, float]:
    if task_type in {ChamberTaskType.PRELIMINARY_OBJECTIONS, ChamberTaskType.PROCEDURAL_CHECK}:
        return 0.65, 0.35
    if task_type in {ChamberTaskType.RESEARCH_MEMO, ChamberTaskType.ISSUE_SPOTTING}:
        return 0.45, 0.55
    if task_type in {ChamberTaskType.HEARING_NOTES, ChamberTaskType.DRAFT_REVIEW}:
        return 0.5, 0.5
    return 0.55, 0.45


def _build_result(
    *,
    item: RetrievedLegalSource,
    lexical_score: float | None,
    semantic_score: float | None,
    rerank_score: float,
    retrieval_mode: RetrievalMode,
    explanation: str,
) -> RetrievedLegalSource:
    item.lexical_score = lexical_score
    item.semantic_score = semantic_score
    item.rerank_score = rerank_score
    item.relevance_score = rerank_score
    item.retrieval_mode = retrieval_mode.value
    item.explanation = explanation
    return item


def _fast_semantic_scores(query: str, records) -> np.ndarray:
    query_terms = set(unique_tokens(query))
    if not query_terms:
        return np.zeros(len(records), dtype=np.float32)

    scores: list[float] = []
    for record in records:
        weighted_text = " ".join(
            [
                record.title,
                record.short_title,
                record.citation_label,
                record.source_type,
                record.category,
                record.act_name,
                record.section_label,
                record.text,
            ]
        )
        record_terms = set(unique_tokens(weighted_text))
        if not record_terms:
            scores.append(0.0)
            continue

        overlap = len(query_terms & record_terms)
        coverage = overlap / max(len(query_terms), 1)
        density = overlap / max(len(record_terms), 1)
        title_bonus = 0.0
        title_terms = set(unique_tokens(f"{record.title} {record.citation_label} {record.section_label}"))
        if query_terms & title_terms:
            title_bonus = 0.08
        scores.append(round((coverage * 0.75) + (density * 0.25) + title_bonus, 4))
    return np.array(scores, dtype=np.float32)


def semantic_search_legal_sources(
    db: Session,
    *,
    query: str,
    task_type: ChamberTaskType = ChamberTaskType.RESEARCH_MEMO,
    limit: int = 8,
    language: str | None = None,
    index_name: str = INDEX_NAME,
) -> LegalRetrievalBundle:
    metadata, records, vectors = load_semantic_index(db, index_name=index_name)
    if vectors is None or not len(records):
        return LegalRetrievalBundle(
            query=query,
            status="Semantic index unavailable",
            summary="Build the semantic index to enable embedding-based legal retrieval.",
            sources=[],
        )

    if settings.semantic_query_mode.casefold() == "transformer":
        query_vector = embed_query(query, model_name=metadata.model_name if metadata else None)
        scores = np.dot(vectors, query_vector)
        score_note = "Semantic embedding similarity match"
    else:
        scores = _fast_semantic_scores(query, records)
        score_note = "Fast multilingual concept-overlap match over the semantic index"

    language_hint = language or detect_language(query)
    top_indices = np.argsort(scores)[::-1][: max(limit * 2, limit)]
    ranked: list[RetrievedLegalSource] = []
    seen: set[tuple[str, str | None]] = set()

    for index in top_indices:
        record = records[int(index)]
        key = (record.source_id, record.chunk_id)
        if key in seen:
            continue
        seen.add(key)
        semantic_score = float(scores[int(index)])
        language_bonus = 0.06 if language_hint and record.language in {language_hint, "Mixed"} else 0.0
        rerank_score = semantic_score + language_bonus
        ranked.append(
            _build_result(
                item=RetrievedLegalSource(
                    source_id=record.source_id,
                    chunk_id=record.chunk_id,
                    title=record.title,
                    short_title=record.short_title,
                    citation_label=record.citation_label,
                    source_type=record.source_type,
                    category=record.category,
                    act_name=record.act_name,
                    section_label=record.section_label,
                    language=record.language,
                    source_origin=record.source_origin,
                    source_url=record.source_url,
                    excerpt=record.excerpt,
                    relevance_score=semantic_score,
                ),
                lexical_score=None,
                semantic_score=semantic_score,
                rerank_score=rerank_score,
                retrieval_mode=RetrievalMode.SEMANTIC,
                explanation=(
                    score_note
                    + (f" with language bonus for {language_hint}." if language_bonus else ".")
                ),
            )
        )
        if len(ranked) >= limit:
            break

    status = "Grounded" if ranked else "No relevant sources found"
    return LegalRetrievalBundle(
        query=query,
        status=status,
        summary=(
            f"Semantic retrieval returned {len(ranked)} source{'s' if len(ranked) != 1 else ''}"
            f" using {metadata.model_name if metadata else 'the configured embedding model'}"
            f" ({settings.semantic_query_mode} query mode)."
        ),
        sources=ranked,
    )


def hybrid_search_legal_sources(
    db: Session,
    *,
    query: str,
    task_type: ChamberTaskType = ChamberTaskType.RESEARCH_MEMO,
    limit: int = 8,
    language: str | None = None,
    ensure_index: bool = False,
) -> LegalRetrievalBundle:
    lexical = search_legal_sources(
        db,
        query=query,
        task_type=task_type,
        limit=max(limit, 8),
        language=language,
    )
    metadata, records, vectors = load_semantic_index(db)
    if ensure_index and (vectors is None or not len(records)):
        build_semantic_index(db)
        metadata, records, vectors = load_semantic_index(db)
    semantic = semantic_search_legal_sources(
        db,
        query=query,
        task_type=task_type,
        limit=max(limit, 8),
        language=language,
    )

    if not semantic.sources:
        fallback = lexical
        fallback.summary = (
            f"{fallback.summary} Semantic retrieval was unavailable, so the chamber used lexical grounding only."
        )
        return fallback

    lexical_weight, semantic_weight = _task_weights(task_type)
    lexical_lookup = {
        (source.source_id, source.chunk_id): source
        for source in lexical.sources
    }
    semantic_lookup = {
        (source.source_id, source.chunk_id): source
        for source in semantic.sources
    }
    all_keys = list(dict.fromkeys([*lexical_lookup.keys(), *semantic_lookup.keys()]))
    language_hint = language or detect_language(query)

    fused: list[RetrievedLegalSource] = []
    for key in all_keys:
        lexical_source = lexical_lookup.get(key)
        semantic_source = semantic_lookup.get(key)
        source = lexical_source or semantic_source
        if source is None:
            continue

        lexical_score = lexical_source.lexical_score if lexical_source else 0.0
        semantic_score = semantic_source.semantic_score if semantic_source else 0.0
        reranked = score_retrieval_candidate(
            query=query,
            task_type=task_type,
            source=source,
            lexical_weight=lexical_weight,
            semantic_weight=semantic_weight,
            language_hint=language_hint,
        )
        fused.append(
            _build_result(
                item=source,
                lexical_score=lexical_score if lexical_source else None,
                semantic_score=semantic_score if semantic_source else None,
                rerank_score=reranked.final_score,
                retrieval_mode=RetrievalMode.HYBRID,
                explanation=reranked.explanation,
            )
        )

    ranked = sorted(fused, key=lambda item: item.rerank_score or item.relevance_score, reverse=True)[:limit]
    status = "Grounded" if ranked else "No relevant sources found"
    return LegalRetrievalBundle(
        query=query,
        status=status,
        summary=(
            f"Hybrid retrieval fused {len(lexical.sources)} lexical and {len(semantic.sources)} semantic candidates"
            f" for {len(ranked)} final grounded sources."
        ),
        sources=ranked,
    )


def retrieve_case_legal_grounding_hybrid(
    db: Session,
    *,
    case: Case,
    instruction: str,
    task_type: ChamberTaskType,
    focus_issue: str | None = None,
    limit: int = 6,
) -> LegalRetrievalBundle:
    query = build_case_retrieval_query(
        case,
        instruction=instruction,
        task_type=task_type,
        focus_issue=focus_issue,
    )
    bundle = hybrid_search_legal_sources(
        db,
        query=query,
        task_type=task_type,
        limit=limit,
        language=detect_language(f"{case.title} {instruction}"),
        ensure_index=False,
    )
    bundle.query = query
    return bundle


def retrieval_leaderboard_snapshot(
    db: Session,
) -> list[RetrievalEvaluationResult]:
    sample_queries = [
        ("order vii rule 11 plaint rejection jurisdiction objections", ChamberTaskType.PRELIMINARY_OBJECTIONS),
        ("article 199 writ maintainability public law relief", ChamberTaskType.RESEARCH_MEMO),
        ("interim injunction order xxxix rules 1 and 2 hearing", ChamberTaskType.HEARING_NOTES),
        ("service tribunal maintainability reinstatement", ChamberTaskType.PROCEDURAL_CHECK),
    ]

    results: list[RetrievalEvaluationResult] = []
    for query, task_type in sample_queries:
        lexical = search_legal_sources(db, query=query, task_type=task_type, limit=5)
        semantic = semantic_search_legal_sources(db, query=query, task_type=task_type, limit=5)
        hybrid = hybrid_search_legal_sources(db, query=query, task_type=task_type, limit=5)
        for mode, bundle in [("Lexical", lexical), ("Semantic", semantic), ("Hybrid", hybrid)]:
            source_type_mix: dict[str, int] = {}
            for source in bundle.sources:
                source_type_mix[source.source_type] = source_type_mix.get(source.source_type, 0) + 1
            average_score = (
                round(
                    sum(source.relevance_score or 0.0 for source in bundle.sources) / len(bundle.sources),
                    4,
                )
                if bundle.sources
                else 0.0
            )
            results.append(
                RetrievalEvaluationResult(
                    mode=mode,
                    query=query,
                    top_labels=[source.citation_label or source.title for source in bundle.sources[:3]],
                    source_type_mix=source_type_mix,
                    average_score=average_score,
                    diagnostics=(
                        {
                            **describe_semantic_query(query),
                            "reranking": reranker_metadata(),
                        }
                        if mode != "Lexical"
                        else {"queryPreview": query[:120], "reranking": reranker_metadata()}
                    ),
                )
            )
    return results
