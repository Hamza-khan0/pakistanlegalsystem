from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import ChamberTaskType
from app.services.knowledge.hybrid_retrieval import hybrid_search_legal_sources
from app.services.knowledge.retrieval import RetrievedLegalSource, search_legal_sources
from app.services.research_workflow.live_web_search import (
    get_live_web_search_health,
    search_live_pakistani_legal_sources,
)
from app.services.research_workflow.source_validation import validate_sources


def _confidence(score: float | None) -> float | None:
    if score is None:
        return None
    if score <= 0:
        return 0.0
    return round(min(0.98, score / (score + 4.0)), 3)


def _source_key(source: RetrievedLegalSource) -> tuple[str, str, str]:
    return (
        (source.source_id or "").casefold(),
        (source.citation_label or source.title or "").casefold(),
        " ".join((source.excerpt or "").split())[:120].casefold(),
    )


def _serialize_source(source: RetrievedLegalSource) -> dict[str, Any]:
    citation = source.citation_label.strip() or None
    return {
        "id": source.source_id,
        "title": source.title or source.short_title or "Untitled legal source",
        "source_type": source.source_type or "Legal Source",
        "court": source.category or None,
        "citation": citation,
        "statute": source.act_name or None,
        "section": source.section_label or None,
        "excerpt": source.excerpt or "",
        "relevance_score": source.relevance_score,
        "retrieval_method": source.retrieval_mode or "Hybrid",
        "url": source.source_url or None,
        "local_path": None,
        "confidence": _confidence(source.relevance_score),
        "source_origin": "local_corpus",
        "explanation": source.explanation,
        "matched_terms": source.matched_terms,
        "chunk_id": source.chunk_id,
    }


def _serialize_live_source(source: dict[str, Any]) -> dict[str, Any]:
    text = str(
        source.get("fetched_text")
        or source.get("excerpt")
        or source.get("snippet")
        or source.get("web_search_summary")
        or ""
    )
    excerpt = " ".join(text.split())[:700]
    return {
        "id": source.get("url"),
        "title": source.get("title") or source.get("url") or "Live web source",
        "source_type": source.get("source_type") or "unknown",
        "court": source.get("court"),
        "citation": source.get("citation"),
        "statute": source.get("statute"),
        "section": source.get("section"),
        "excerpt": excerpt,
        "relevance_score": source.get("confidence"),
        "retrieval_method": "live_web",
        "url": source.get("url"),
        "local_path": None,
        "confidence": source.get("confidence"),
        "source_origin": "live_web",
        "domain": source.get("domain"),
        "query": source.get("query"),
        "source_provider": source.get("source_provider") or source.get("provider"),
        "provider": source.get("provider") or "openai_web_search",
        "snippet": source.get("snippet"),
        "fetched": source.get("fetched", False),
        "fetch_error": source.get("fetch_error", ""),
        "validation": source.get("validation", {}),
        "web_search_summary": source.get("web_search_summary"),
    }


def _normalized_key(source: dict[str, Any]) -> tuple[str, str, str]:
    citation = str(source.get("citation") or "").casefold().strip()
    url = str(source.get("url") or source.get("id") or "").casefold().strip()
    title = " ".join(str(source.get("title") or "").casefold().split())
    excerpt = " ".join(str(source.get("excerpt") or "").casefold().split())[:160]
    return citation, url, title or excerpt


def retrieve_pakistani_legal_sources(
    db: Session,
    query_plan: list[dict[str, Any]],
    max_sources: int = 12,
    *,
    include_live_web: bool = True,
    use_openai_web_search: bool = True,
    max_live_sources: int = 8,
) -> dict[str, Any]:
    ranked: list[RetrievedLegalSource] = []
    seen: set[tuple[str, str, str]] = set()
    per_query_limit = max(3, min(max_sources, 6))
    retrieval_warnings: list[str] = []

    for query_item in query_plan:
        query = str(query_item.get("query") or "").strip()
        if not query:
            continue
        try:
            bundle = hybrid_search_legal_sources(
                db,
                query=query,
                task_type=ChamberTaskType.RESEARCH_MEMO,
                limit=per_query_limit,
                ensure_index=False,
            )
        except Exception as exc:
            retrieval_warnings.append(f"Hybrid retrieval failed for one query; lexical fallback used. {type(exc).__name__}")
            try:
                bundle = search_legal_sources(
                    db,
                    query=query,
                    task_type=ChamberTaskType.RESEARCH_MEMO,
                    limit=per_query_limit,
                )
            except Exception as fallback_exc:
                retrieval_warnings.append(f"Local retrieval failed for one query. {type(fallback_exc).__name__}")
                continue

        for source in bundle.sources:
            key = _source_key(source)
            if key in seen:
                continue
            seen.add(key)
            if query_item.get("issue") and source.explanation:
                source.explanation = f"{source.explanation} Query issue: {query_item['issue']}."
            ranked.append(source)

    ranked.sort(
        key=lambda item: (
            float(item.rerank_score if item.rerank_score is not None else item.relevance_score or 0),
            float(item.semantic_score or 0),
            float(item.lexical_score or 0),
        ),
        reverse=True,
    )
    local_sources = validate_sources([_serialize_source(source) for source in ranked[: max_sources * 2]])
    normalized = list(local_sources)

    web_health = get_live_web_search_health()
    live_sources: list[dict[str, Any]] = []
    if include_live_web and use_openai_web_search:
        if not web_health.get("available"):
            retrieval_warnings.append(str(web_health.get("reason") or "OpenAI web search unavailable."))
        else:
            try:
                live_sources = validate_sources(
                    [
                        _serialize_live_source(source)
                        for source in search_live_pakistani_legal_sources(query_plan, max_sources=max_live_sources)
                    ]
                )
                normalized.extend(live_sources)
            except Exception as exc:
                retrieval_warnings.append(f"OpenAI web search failed; local sources retained. {type(exc).__name__}")

    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for source in normalized:
        key = _normalized_key(source)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(source)

    origin_boost = {"local_corpus": 0.08, "live_web": 0.0, "uploaded_documents": 0.04, "fallback": -0.1}
    deduped.sort(
        key=lambda item: (
            float(item.get("confidence") or 0) + origin_boost.get(str(item.get("source_origin")), 0),
            float(item.get("relevance_score") or 0),
        ),
        reverse=True,
    )
    top_sources = deduped[:max_sources]
    sources_by_origin: dict[str, list[dict[str, Any]]] = {
        "local_corpus": [],
        "live_web": [],
        "uploaded_documents": [],
        "fallback": [],
    }
    for source in top_sources:
        origin = str(source.get("source_origin") or "fallback")
        sources_by_origin.setdefault(origin, []).append(source)

    return {
        "sources": top_sources,
        "sources_by_origin": sources_by_origin,
        "retrieval_warnings": retrieval_warnings,
        "provider_status": {
            "localRetrievalAvailable": True,
            "liveWebSearchEnabled": bool(web_health.get("enabled")),
            "liveWebSearchAvailable": bool(web_health.get("available")),
            "searchProvider": "openai",
            "openaiWebSearchUsed": bool(sources_by_origin.get("live_web")),
            "openaiWebSearchHealth": web_health,
        },
    }
