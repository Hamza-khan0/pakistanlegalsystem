from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.services.llm.provider import OPENAI_RESPONSES_URL, PRIVACY_NOTICE
from app.services.research_workflow.source_validation import (
    detect_citation_patterns,
    detect_statute_patterns,
    extract_domain,
    validate_sources,
)


logger = logging.getLogger(__name__)

TRUSTED_PAKISTANI_DOMAINS = [
    "supremecourt.gov.pk",
    "pakistancode.gov.pk",
    "na.gov.pk",
    "senate.gov.pk",
    "federalshariatcourt.gov.pk",
    "lahorehighcourt.gov.pk",
    "sindhhighcourt.gov.pk",
    "peshawarhighcourt.gov.pk",
    "ihc.gov.pk",
    "bhc.gov.pk",
    "punjablaws.gov.pk",
    "sindhlaws.gov.pk",
    "kpcode.kp.gov.pk",
    "balochistanlaws.gov.pk",
]


def is_openai_web_search_available() -> bool:
    return bool(
        settings.live_web_search_enabled
        and settings.search_provider.strip().casefold() == "openai"
        and settings.openai_api_key.strip()
    )


def get_openai_web_search_health() -> dict[str, Any]:
    enabled = bool(settings.live_web_search_enabled)
    provider_openai = settings.search_provider.strip().casefold() == "openai"
    key_configured = bool(settings.openai_api_key.strip())
    available = bool(enabled and provider_openai and key_configured)
    if not enabled:
        reason = "LIVE_WEB_SEARCH_ENABLED is false; local corpus retrieval will be used."
    elif not provider_openai:
        reason = "SEARCH_PROVIDER must be openai for this project."
    elif not key_configured:
        reason = "OPENAI_API_KEY is not configured; OpenAI web search is unavailable."
    else:
        reason = "OpenAI Responses API web search is enabled."
    return {
        "enabled": enabled,
        "available": available,
        "provider": "openai" if provider_openai else settings.search_provider,
        "model": settings.openai_web_search_model,
        "api_key_configured": key_configured,
        "maxResults": settings.web_search_max_results,
        "reason": reason,
        "privacy_notice": PRIVACY_NOTICE,
    }


def _enrich_query(query: str) -> str:
    cleaned = " ".join(query.split())
    lowered = cleaned.casefold()
    additions: list[str] = []
    if "pakistan" not in lowered:
        additions.append("Pakistan")
    if not any(term in lowered for term in ["supreme court", "high court", "pakistancode.gov.pk"]):
        additions.append("Supreme Court of Pakistan High Court Pakistan")
    if not any(term in lowered for term in ["pld", "scmr", "ylr", "clc", "constitution", "cpc", "crpc"]):
        additions.append("PLD SCMR Constitution CPC CrPC")
    return " ".join([cleaned, *additions])[:260]


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }


def _response_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    chunks: list[str] = []
    for item in data.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks)


def _walk(value: Any) -> list[Any]:
    items = [value]
    if isinstance(value, dict):
        for child in value.values():
            items.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            items.extend(_walk(child))
    return items


def _collect_url_sources(data: dict[str, Any]) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for item in _walk(data):
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            continue
        collected.append(
            {
                "title": str(item.get("title") or item.get("name") or url),
                "url": url,
                "snippet": str(item.get("snippet") or item.get("text") or item.get("content") or ""),
            }
        )
    return collected


def _extract_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"sources": parsed}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else {"sources": parsed}
    return {"sources": [], "web_search_summary": text.strip()}


def _normalize_source(source: dict[str, Any], *, query: str, rank: int) -> dict[str, Any]:
    url = source.get("url")
    excerpt = str(source.get("snippet") or source.get("excerpt") or source.get("relevance_note") or "")
    title = str(source.get("title") or source.get("case_name_or_title") or url or "OpenAI web search result")
    combined = " ".join(
        str(source.get(key) or "")
        for key in ["title", "snippet", "excerpt", "citation", "statute", "section", "relevance_note"]
    )
    citations = detect_citation_patterns(combined)
    sections = detect_statute_patterns(combined)
    normalized = {
        "id": str(url or f"openai-web-summary-{abs(hash((query, title, rank)))}"),
        "title": title,
        "source_type": source.get("source_type") or ("web_summary" if not url else "unknown"),
        "court": source.get("court"),
        "citation": source.get("citation") or (citations[0] if citations else None),
        "statute": source.get("statute"),
        "section": source.get("section") or (sections[0] if sections else None),
        "excerpt": excerpt[:900],
        "relevance_score": source.get("relevance_score") or source.get("score") or 0.0,
        "retrieval_method": "openai_web_search",
        "source_origin": "live_web",
        "url": url if isinstance(url, str) and url.startswith(("http://", "https://")) else None,
        "domain": extract_domain(url if isinstance(url, str) else None),
        "local_path": None,
        "confidence": 0.0,
        "query": query,
        "provider": "openai_web_search",
        "source_provider": "openai_web_search",
        "web_search_summary": source.get("web_search_summary"),
    }
    if not normalized["excerpt"]:
        normalized["excerpt"] = str(source.get("relevance") or source.get("summary") or "")[:900]
    return validate_sources([normalized])[0]


def _call_openai_web_search(query: str, max_results: int, *, tool_type: str) -> dict[str, Any]:
    prompt = f"""
You are searching for Pakistani legal authorities.

Find reliable sources for this query:
{query}

Prefer official court, statute, and government sources, including:
{", ".join(TRUSTED_PAKISTANI_DOMAINS)}

Return JSON only with:
{{
  "sources": [
    {{
      "title": "",
      "url": null,
      "snippet": "",
      "source_type": "case_law|statute|court_website|government|legal_article|web_summary|unknown",
      "court": null,
      "citation": null,
      "statute": null,
      "section": null,
      "relevance_note": ""
    }}
  ],
  "web_search_summary": "",
  "warnings": []
}}

Do not invent citations or URLs. If a URL is not visible, use null and mark it as a research lead only.
Return at most {max_results} sources.
"""
    payload: dict[str, Any] = {
        "model": settings.openai_web_search_model,
        "input": prompt,
        "tools": [{"type": tool_type}],
        "tool_choice": "auto",
        "include": ["web_search_call.action.sources"],
        "temperature": 0.1,
    }
    with httpx.Client(timeout=settings.web_search_timeout_seconds) as client:
        response = client.post(OPENAI_RESPONSES_URL, headers=_headers(), json=payload)
    response.raise_for_status()
    return response.json()


def run_openai_web_search(query: str, max_results: int = 8) -> dict[str, Any]:
    started = time.perf_counter()
    if not is_openai_web_search_available():
        return {
            "ok": False,
            "query": query,
            "provider": "openai_web_search",
            "results": [],
            "summary": "",
            "warning": get_openai_web_search_health()["reason"],
            "duration_ms": 0,
        }

    enriched = _enrich_query(query)
    last_error: Exception | None = None
    data: dict[str, Any] | None = None
    for tool_type in ("web_search", "web_search_preview"):
        try:
            data = _call_openai_web_search(enriched, max_results, tool_type=tool_type)
            break
        except Exception as exc:
            last_error = exc
            logger.warning("OPENAI_WEB_SEARCH_FAILED tool=%s error=%s", tool_type, type(exc).__name__)

    duration_ms = round((time.perf_counter() - started) * 1000)
    if data is None:
        return {
            "ok": False,
            "query": enriched,
            "provider": "openai_web_search",
            "results": [],
            "summary": "",
            "warning": f"OpenAI web search failed: {type(last_error).__name__ if last_error else 'unknown'}",
            "duration_ms": duration_ms,
        }

    output_text = _response_text(data)
    parsed = _extract_json_object(output_text)
    declared_sources = parsed.get("sources") if isinstance(parsed.get("sources"), list) else []
    annotation_sources = _collect_url_sources(data)
    summary = str(parsed.get("web_search_summary") or parsed.get("summary") or output_text)
    normalized: list[dict[str, Any]] = []
    for rank, source in enumerate([*declared_sources, *annotation_sources], start=1):
        if not isinstance(source, dict):
            continue
        source.setdefault("web_search_summary", summary[:700])
        normalized.append(_normalize_source(source, query=enriched, rank=rank))

    if not normalized and summary:
        normalized.append(
            _normalize_source(
                {
                    "title": "OpenAI web search summary",
                    "url": None,
                    "snippet": summary[:900],
                    "source_type": "web_summary",
                    "web_search_summary": summary[:900],
                },
                query=enriched,
                rank=1,
            )
        )

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for source in normalized:
        key = "|".join(
            [
                str(source.get("url") or "").casefold(),
                str(source.get("citation") or "").casefold(),
                str(source.get("title") or "").casefold(),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)

    deduped.sort(key=lambda item: float(item.get("confidence") or 0), reverse=True)
    return {
        "ok": True,
        "query": enriched,
        "provider": "openai_web_search",
        "results": deduped[:max_results],
        "summary": summary[:1200],
        "warning": "",
        "duration_ms": duration_ms,
    }


def search_live_pakistani_legal_sources(
    query_plan: list[dict[str, Any]],
    max_sources: int = 12,
) -> list[dict[str, Any]]:
    if not is_openai_web_search_available():
        return []

    collected: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_query = max(2, min(settings.web_search_max_results, max_sources))
    for query_item in query_plan[:8]:
        query = str(query_item.get("query") or "").strip()
        if not query:
            continue
        bundle = run_openai_web_search(query, max_results=per_query)
        for source in bundle.get("results", []):
            key = str(source.get("url") or source.get("citation") or source.get("title") or "").casefold()
            if not key or key in seen:
                continue
            seen.add(key)
            source["query_issue"] = query_item.get("issue")
            source["issue_priority"] = query_item.get("priority")
            collected.append(source)
            if len(collected) >= max_sources:
                break
        if len(collected) >= max_sources:
            break

    collected.sort(
        key=lambda item: (
            float(item.get("confidence") or 0),
            -int(item.get("issue_priority") or 99),
        ),
        reverse=True,
    )
    return collected[:max_sources]
