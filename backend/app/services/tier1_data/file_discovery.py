from __future__ import annotations

from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".json", ".jsonl", ".csv", ".pdf"}


def discover_supported_files(root: str | Path) -> list[Path]:
    base = Path(root)
    if not base.exists():
        return []
    return sorted(
        path
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
