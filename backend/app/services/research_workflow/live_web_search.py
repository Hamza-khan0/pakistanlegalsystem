from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.services.research_workflow.source_extractor import (
    classify_legal_source,
    extract_citation_patterns,
    extract_domain,
    extract_statute_section_patterns,
    fetch_url_text,
    score_source_confidence,
)


logger = logging.getLogger(__name__)


def _available_provider() -> str | None:
    configured = settings.search_provider.strip().casefold()
    providers = {
        "tavily": bool(settings.tavily_api_key),
        "serpapi": bool(settings.serpapi_api_key),
        "bing": bool(settings.bing_search_api_key),
        "google_cse": bool(settings.google_cse_api_key and settings.google_cse_id),
    }
    if configured != "auto":
        return configured if providers.get(configured) else None
    for provider in ["tavily", "serpapi", "bing", "google_cse"]:
        if providers[provider]:
            return provider
    return None


def is_live_web_search_available() -> bool:
    return bool(settings.live_web_search_enabled and _available_provider())


def get_live_web_search_health() -> dict[str, Any]:
    provider = _available_provider()
    return {
        "enabled": bool(settings.live_web_search_enabled),
        "available": bool(settings.live_web_search_enabled and provider),
        "provider": provider or "none",
        "configuredProvider": settings.search_provider,
        "reason": (
            f"{provider} search provider configured."
            if provider
            else "No live web search provider key is configured."
        ),
        "maxResults": settings.web_search_max_results,
        "privacy_notice": "When enabled, research queries may be sent to the configured search provider.",
    }


def _enrich_query(query: str) -> str:
    cleaned = " ".join(query.split())
    additions = []
    lowered = cleaned.casefold()
    if "pakistan" not in lowered:
        additions.append("Pakistan")
    if not any(term in lowered for term in ["supreme court", "high court", "pld", "scmr", "cpc", "crpc"]):
        additions.append("Supreme Court of Pakistan")
    if len(cleaned) < 120 and not any(term in lowered for term in ["pld", "scmr", "ylr", "clc"]):
        additions.append("PLD SCMR")
    return " ".join([cleaned, *additions])[:240]


def _normalize_result(
    *,
    title: str,
    url: str,
    snippet: str,
    provider: str,
    rank: int,
    query: str,
    raw_score: float | None = None,
) -> dict[str, Any]:
    domain = extract_domain(url)
    return {
        "title": title.strip() or url,
        "url": url,
        "snippet": snippet.strip(),
        "source_provider": provider,
        "rank": rank,
        "query": query,
        "domain": domain,
        "raw_score": raw_score,
        "fetched_text": "",
        "source_type": "unknown",
        "court": None,
        "citation": None,
        "statute": None,
        "section": None,
        "confidence": 0.0,
        "retrieval_method": "live_web",
    }


def _search_tavily(query: str, max_results: int) -> list[dict[str, Any]]:
    with httpx.Client(timeout=settings.web_search_timeout_seconds) as client:
        response = client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
        )
    response.raise_for_status()
    results = response.json().get("results", [])
    return [
        _normalize_result(
            title=str(item.get("title") or ""),
            url=str(item.get("url") or ""),
            snippet=str(item.get("content") or ""),
            provider="tavily",
            rank=index,
            query=query,
            raw_score=item.get("score"),
        )
        for index, item in enumerate(results, start=1)
        if item.get("url")
    ]


def _search_serpapi(query: str, max_results: int) -> list[dict[str, Any]]:
    params = urlencode({"engine": "google", "q": query, "api_key": settings.serpapi_api_key, "num": max_results})
    with httpx.Client(timeout=settings.web_search_timeout_seconds) as client:
        response = client.get(f"https://serpapi.com/search.json?{params}")
    response.raise_for_status()
    results = response.json().get("organic_results", [])
    return [
        _normalize_result(
            title=str(item.get("title") or ""),
            url=str(item.get("link") or ""),
            snippet=str(item.get("snippet") or ""),
            provider="serpapi",
            rank=index,
            query=query,
            raw_score=None,
        )
        for index, item in enumerate(results[:max_results], start=1)
        if item.get("link")
    ]


def _search_bing(query: str, max_results: int) -> list[dict[str, Any]]:
    params = urlencode({"q": query, "count": max_results, "mkt": "en-PK"})
    with httpx.Client(timeout=settings.web_search_timeout_seconds) as client:
        response = client.get(
            f"https://api.bing.microsoft.com/v7.0/search?{params}",
            headers={"Ocp-Apim-Subscription-Key": settings.bing_search_api_key},
        )
    response.raise_for_status()
    results = response.json().get("webPages", {}).get("value", [])
    return [
        _normalize_result(
            title=str(item.get("name") or ""),
            url=str(item.get("url") or ""),
            snippet=str(item.get("snippet") or ""),
            provider="bing",
            rank=index,
            query=query,
            raw_score=None,
        )
        for index, item in enumerate(results[:max_results], start=1)
        if item.get("url")
    ]


def _search_google_cse(query: str, max_results: int) -> list[dict[str, Any]]:
    params = urlencode(
        {
            "key": settings.google_cse_api_key,
            "cx": settings.google_cse_id,
            "q": query,
            "num": min(max_results, 10),
        }
    )
    with httpx.Client(timeout=settings.web_search_timeout_seconds) as client:
        response = client.get(f"https://www.googleapis.com/customsearch/v1?{params}")
    response.raise_for_status()
    results = response.json().get("items", [])
    return [
        _normalize_result(
            title=str(item.get("title") or ""),
            url=str(item.get("link") or ""),
            snippet=str(item.get("snippet") or ""),
            provider="google_cse",
            rank=index,
            query=query,
            raw_score=None,
        )
        for index, item in enumerate(results[:max_results], start=1)
        if item.get("link")
    ]


def run_live_legal_web_search(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    provider = _available_provider()
    if not settings.live_web_search_enabled or not provider:
        return []
    enriched = _enrich_query(query)
    try:
        if provider == "tavily":
            return _search_tavily(enriched, max_results)
        if provider == "serpapi":
            return _search_serpapi(enriched, max_results)
        if provider == "bing":
            return _search_bing(enriched, max_results)
        if provider == "google_cse":
            return _search_google_cse(enriched, max_results)
    except Exception as exc:
        logger.warning("LIVE_WEB_SEARCH_FAILED provider=%s error=%s", provider, type(exc).__name__)
        return []
    return []


def fetch_and_extract_web_source(url: str) -> dict[str, Any]:
    return fetch_url_text(url)


def _hydrate_result(result: dict[str, Any]) -> dict[str, Any]:
    extraction = fetch_and_extract_web_source(str(result.get("url") or ""))
    fetched_text = str(extraction.get("text") or "")
    title = str(extraction.get("title") or result.get("title") or "")
    combined = " ".join([title, str(result.get("snippet") or ""), fetched_text])
    citations = extract_citation_patterns(combined)
    sections = extract_statute_section_patterns(combined)
    result = {
        **result,
        "title": title or result.get("title") or result.get("url"),
        "fetched": bool(extraction.get("fetched")),
        "fetch_error": extraction.get("error") or "",
        "fetched_text": fetched_text,
        "source_type": classify_legal_source({**result, "title": title, "fetched_text": fetched_text}),
        "citation": citations[0] if citations else None,
        "section": sections[0] if sections else None,
    }
    result["confidence"] = score_source_confidence(result)
    return result


def search_live_pakistani_legal_sources(
    query_plan: list[dict[str, Any]],
    max_sources: int = 12,
) -> list[dict[str, Any]]:
    if not is_live_web_search_available():
        return []

    hydrated: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    per_query = max(2, min(settings.web_search_max_results, max_sources))
    for query_item in query_plan[:8]:
        query = str(query_item.get("query") or "").strip()
        if not query:
            continue
        for result in run_live_legal_web_search(query, max_results=per_query):
            url = str(result.get("url") or "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            hydrated.append(_hydrate_result(result))
            if len(hydrated) >= max_sources:
                break
        if len(hydrated) >= max_sources:
            break

    hydrated.sort(key=lambda item: float(item.get("confidence") or 0), reverse=True)
    return hydrated[:max_sources]
