from __future__ import annotations

from pathlib import Path
from time import sleep
from urllib.parse import unquote, urlparse

import httpx

from app.services.crawling.base import FetchedResource


def _guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return "text/html"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".txt", ".md"}:
        return "text/plain"
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        return f"image/{suffix.lstrip('.')}"
    return "application/octet-stream"


def fetch_resource(
    url: str,
    *,
    rate_limit_seconds: float = 0.0,
    retries: int = 2,
    timeout_seconds: float = 20.0,
) -> FetchedResource:
    parsed = urlparse(url)
    if rate_limit_seconds > 0:
        sleep(rate_limit_seconds)

    if parsed.scheme == "file":
        raw_path = unquote(parsed.path or "")
        if raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
            raw_path = raw_path[1:]
        if parsed.netloc:
            raw_path = f"//{parsed.netloc}{raw_path}"
        path = Path(raw_path)
        content = path.read_bytes()
        text = content.decode("utf-8", errors="ignore")
        return FetchedResource(
            url=url,
            content=content,
            content_type=_guess_content_type(path),
            text=text,
        )

    last_error: Exception | None = None
    for _ in range(retries + 1):
        try:
            response = httpx.get(url, timeout=timeout_seconds, follow_redirects=True)
            response.raise_for_status()
            return FetchedResource(
                url=str(response.url),
                content=response.content,
                content_type=response.headers.get("content-type", "application/octet-stream"),
                text=response.text,
            )
        except Exception as exc:  # pragma: no cover - network fallbacks are environment dependent
            last_error = exc
            if rate_limit_seconds > 0:
                sleep(rate_limit_seconds)

    raise RuntimeError(f"Unable to fetch crawl resource: {url}. {last_error}")
