from __future__ import annotations

import re
from typing import Any

from app.services.research_workflow.source_extractor import (
    TRUSTED_DOMAINS,
    classify_legal_source,
    extract_citation_patterns,
    extract_domain as _extract_domain,
    extract_statute_section_patterns,
    score_source_confidence,
)


EXTRA_CITATION_PATTERNS = [
    re.compile(r"\b\d{4}\s+SCMR\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b\d{4}\s+YLR\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b\d{4}\s+CLC\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bPLD\s+\d{4}\s+[A-Z][A-Za-z.\s]{1,25}\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b(?:Civil|Criminal|Constitution)\s+(?:Appeal|Petition)\s+No\.?\s*[\w/-]+", re.IGNORECASE),
]

EXTRA_STATUTE_PATTERNS = [
    re.compile(r"\bArticle\s+199\b", re.IGNORECASE),
    re.compile(r"\b[Ss]ection\s+497\s+CrPC\b", re.IGNORECASE),
    re.compile(r"\bOrder\s+XXXIX\s+Rules?\s+1(?:\s+and\s+2)?\s+CPC\b", re.IGNORECASE),
    re.compile(r"\bQanun-e-Shahadat\b", re.IGNORECASE),
    re.compile(r"\bSpecific Relief Act\b", re.IGNORECASE),
    re.compile(r"\bLimitation Act\b", re.IGNORECASE),
    re.compile(r"\bContract Act\b", re.IGNORECASE),
    re.compile(r"\bTransfer of Property Act\b", re.IGNORECASE),
]


def extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    domain = _extract_domain(url)
    return domain or None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        cleaned = " ".join(str(value).split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            ordered.append(cleaned)
    return ordered


def detect_citation_patterns(text: str) -> list[str]:
    found = extract_citation_patterns(text)
    for pattern in EXTRA_CITATION_PATTERNS:
        found.extend(str(match) for match in pattern.findall(text or ""))
    return _unique(found)[:10]


def detect_statute_patterns(text: str) -> list[str]:
    found = extract_statute_section_patterns(text)
    for pattern in EXTRA_STATUTE_PATTERNS:
        found.extend(str(match) for match in pattern.findall(text or ""))
    return _unique(found)[:10]


def classify_source_type(source: dict[str, Any]) -> str:
    current = str(source.get("source_type") or source.get("sourceType") or "").strip()
    if current and current != "unknown":
        return current
    return classify_legal_source(source)


def _relevance_bonus(source: dict[str, Any]) -> float:
    query_terms = {
        term.casefold()
        for term in str(source.get("query") or "").split()
        if len(term) > 4
    }
    haystack = " ".join(
        str(source.get(key) or "")
        for key in ["title", "excerpt", "snippet", "fetched_text"]
    ).casefold()
    if not query_terms:
        return 0.0
    overlap = sum(1 for term in query_terms if term in haystack)
    return min(0.12, overlap * 0.025)


def score_source_confidence_normalized(source: dict[str, Any]) -> float:
    domain = extract_domain(str(source.get("url") or "")) or str(source.get("domain") or "")
    text = " ".join(
        str(source.get(key) or "")
        for key in ["title", "excerpt", "snippet", "fetched_text", "citation", "section", "statute"]
    )
    source = {
        **source,
        "domain": domain,
        "citation": source.get("citation") or (detect_citation_patterns(text) or [None])[0],
        "section": source.get("section") or (detect_statute_patterns(text) or [None])[0],
    }
    score = float(score_source_confidence(source))
    if domain in TRUSTED_DOMAINS:
        score += 0.08
    if not source.get("url"):
        score = min(score, 0.35)
    if source.get("source_type") == "web_summary":
        score = min(score, 0.35)
    return round(max(0.05, min(0.98, score + _relevance_bonus(source))), 3)


def validate_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        text = " ".join(
            str(source.get(key) or "")
            for key in ["title", "excerpt", "snippet", "fetched_text", "citation", "section", "statute"]
        )
        citations = detect_citation_patterns(text)
        statutes = detect_statute_patterns(text)
        normalized = {
            **source,
            "id": source.get("id") or source.get("url") or f"source-{index}",
            "domain": source.get("domain") or extract_domain(str(source.get("url") or "")),
            "citation": source.get("citation") or (citations[0] if citations else None),
            "section": source.get("section") or (statutes[0] if statutes else None),
            "source_type": classify_source_type(source),
        }
        normalized["confidence"] = score_source_confidence_normalized(normalized)
        normalized["validation"] = {
            "citationsDetected": citations,
            "statutesDetected": statutes,
            "trustedDomain": normalized.get("domain") in TRUSTED_DOMAINS,
            "usableAsAuthority": bool(normalized.get("url")) and normalized["confidence"] >= 0.45,
        }
        validated.append(normalized)
    return validated
