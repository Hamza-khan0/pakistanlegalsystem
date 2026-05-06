from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.corpus.dataset_builder import build_dataset_bundle


@dataclass(slots=True)
class CorpusExportStats:
    output_dir: str
    retrieval_records: int
    classification_records: int
    bilingual_records: int
    files: list[str]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def export_corpus_datasets(
    db: Session,
    *,
    output_dir: str | None = None,
) -> CorpusExportStats:
    bundle = build_dataset_bundle(db)
    target_dir = Path(output_dir or settings.corpus_exports_dir)
    retrieval_path = target_dir / "retrieval_corpus.jsonl"
    classification_path = target_dir / "classification_corpus.jsonl"
    bilingual_path = target_dir / "bilingual_corpus.jsonl"

    _write_jsonl(retrieval_path, bundle.retrieval_records)
    _write_jsonl(classification_path, bundle.classification_records)
    _write_jsonl(bilingual_path, bundle.bilingual_records)

    return CorpusExportStats(
        output_dir=str(target_dir),
        retrieval_records=len(bundle.retrieval_records),
        classification_records=len(bundle.classification_records),
        bilingual_records=len(bundle.bilingual_records),
        files=[str(retrieval_path), str(classification_path), str(bilingual_path)],
    )
