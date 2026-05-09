from __future__ import annotations

from typing import Any

from app.services.research_workflow.openai_web_search import (
    get_openai_web_search_health,
    is_openai_web_search_available,
    run_openai_web_search,
    search_live_pakistani_legal_sources,
)


def is_live_web_search_available() -> bool:
    return is_openai_web_search_available()


def get_live_web_search_health() -> dict[str, Any]:
    return get_openai_web_search_health()


def run_live_legal_web_search(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    bundle = run_openai_web_search(query, max_results=max_results)
    return list(bundle.get("results", []))
