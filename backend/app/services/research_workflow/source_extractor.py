from __future__ import annotations

from io import BytesIO
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx
from pypdf import PdfReader

from app.core.config import settings


MAX_SOURCE_BYTES = 2_000_000
TRUSTED_DOMAINS = {
    "supremecourt.gov.pk",
    "pakistancode.gov.pk",
    "na.gov.pk",
    "senate.gov.pk",
    "federalshariatcourt.gov.pk",
    "lahorehighcourt.gov.pk",
    "sindhhighcourt.gov.pk",
    "peshawarhighcourt.gov.pk",
    "bhc.gov.pk",
    "ihc.gov.pk",
    "kpcode.kp.gov.pk",
    "punjablaws.gov.pk",
    "sindhlaws.gov.pk",
    "balochistanlaws.gov.pk",
}

CITATION_PATTERNS = [
    re.compile(r"\bPLD\s+\d{4}\s+[A-Z][A-Za-z.\s]{1,25}\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b\d{4}\s+SCMR\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b\d{4}\s+YLR\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b\d{4}\s+CLC\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b(?:Civil|Criminal|Constitution)\s+(?:Appeal|Petition)\s+No\.?\s*[\w/-]+", re.IGNORECASE),
]
SECTION_PATTERNS = [
    re.compile(r"\bArticle\s+\d+[A-Za-z-]*\b", re.IGNORECASE),
    re.compile(r"\b[Ss]ection\s+\d+[A-Za-z-]*(?:\s+(?:CPC|CrPC|PPC|Qanun-e-Shahadat))?\b"),
    re.compile(r"\bOrder\s+[IVXLCDM]+(?:\s+Rule\s+\d+(?:\s+and\s+\d+)?)?\s+CPC\b", re.IGNORECASE),
    re.compile(r"\bQanun-e-Shahadat\s+Article\s+\d+\b", re.IGNORECASE),
]


def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.casefold().removeprefix("www.")
    except Exception:
        return ""


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_html_text(content: bytes) -> tuple[str, str]:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    title = _clean_text(soup.title.get_text(" ")) if soup.title else ""
    candidates = soup.find_all(["main", "article"])
    text_parts = [item.get_text(" ", strip=True) for item in candidates] or [
        soup.get_text(" ", strip=True)
    ]
    return title, _clean_text(" ".join(text_parts))


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = []
    for page in reader.pages[:12]:
        pages.append(page.extract_text() or "")
    return _clean_text(" ".join(pages))


def fetch_url_text(url: str) -> dict[str, Any]:
    try:
        with httpx.Client(
            timeout=settings.web_source_fetch_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "AI Legal Chambers research fetcher/1.0"},
        ) as client:
            response = client.get(url)
        response.raise_for_status()
        content = response.content[:MAX_SOURCE_BYTES]
        content_type = response.headers.get("content-type", "").casefold()
        if "application/pdf" in content_type or url.casefold().endswith(".pdf"):
            text = _extract_pdf_text(content)
            title = urlparse(str(response.url)).path.rsplit("/", 1)[-1] or "PDF source"
        elif "text/html" in content_type or "text/plain" in content_type or not content_type:
            title, text = _extract_html_text(content)
        else:
            return {
                "fetched": False,
                "title": "",
                "text": "",
                "error": f"Unsupported content type: {content_type}",
            }
        return {
            "fetched": bool(text),
            "title": title,
            "text": text[:25000],
            "error": "" if text else "No extractable text found.",
            "contentType": content_type,
        }
    except Exception as exc:
        return {"fetched": False, "title": "", "text": "", "error": str(exc)}


def extract_citation_patterns(text: str) -> list[str]:
    found: list[str] = []
    for pattern in CITATION_PATTERNS:
        for match in pattern.findall(text or ""):
            cleaned = _clean_text(str(match))
            if cleaned and cleaned not in found:
                found.append(cleaned)
    return found[:8]


def extract_statute_section_patterns(text: str) -> list[str]:
    found: list[str] = []
    for pattern in SECTION_PATTERNS:
        for match in pattern.findall(text or ""):
            cleaned = _clean_text(str(match))
            if cleaned and cleaned not in found:
                found.append(cleaned)
    return found[:8]


def classify_legal_source(result: dict[str, Any]) -> str:
    domain = str(result.get("domain") or extract_domain(str(result.get("url") or "")))
    text = " ".join(
        str(result.get(key) or "")
        for key in ["title", "snippet", "fetched_text", "url"]
    ).casefold()
    if domain in TRUSTED_DOMAINS and ("code" in domain or "laws" in domain or "na.gov" in domain):
        return "statute"
    if "judgment" in text or "appeal no" in text or "petition no" in text or extract_citation_patterns(text):
        return "case_law"
    if "constitution" in text or "article 199" in text or "section " in text or "order " in text:
        return "statute"
    if domain in TRUSTED_DOMAINS:
        return "court_website"
    if "law" in text or "legal" in text:
        return "article"
    return "unknown"


def score_source_confidence(source: dict[str, Any]) -> float:
    domain = str(source.get("domain") or extract_domain(str(source.get("url") or "")))
    text = " ".join(
        str(source.get(key) or "")
        for key in ["title", "snippet", "fetched_text", "citation", "section"]
    ).casefold()
    score = 0.15
    if domain in TRUSTED_DOMAINS:
        score += 0.35
    if source.get("citation") or extract_citation_patterns(text):
        score += 0.2
    if source.get("section") or extract_statute_section_patterns(text):
        score += 0.15
    if source.get("fetched_text"):
        score += 0.1
    if any(term in text for term in ["pakistan", "supreme court", "high court", "article 199", "cpc", "crpc"]):
        score += 0.1
    if domain and any(part in domain for part in ["blog", "wordpress", "medium"]):
        score -= 0.15
    return round(max(0.05, min(0.98, score)), 3)
