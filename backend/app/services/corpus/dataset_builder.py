from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.corpus_entry import CorpusEntry


@dataclass(slots=True)
class DatasetBundle:
    retrieval_records: list[dict]
    classification_records: list[dict]
    bilingual_records: list[dict]


def build_dataset_bundle(db: Session) -> DatasetBundle:
    entries = list(
        db.scalars(
            select(CorpusEntry)
            .options(
                joinedload(CorpusEntry.legal_source),
                joinedload(CorpusEntry.crawled_document),
            )
            .where(CorpusEntry.ready_for_training.is_(True))
        ).all()
    )

    retrieval_records: list[dict] = []
    classification_records: list[dict] = []
    bilingual_records: list[dict] = []
    for entry in entries:
        metadata = dict(entry.metadata_json)
        source_type = str(metadata.get("sourceType") or "Unknown")
        record = {
            "id": entry.id,
            "title": entry.title,
            "language": entry.language,
            "text": entry.normalized_text,
            "split": entry.dataset_split.value,
            "sourceKind": entry.source_kind.value,
            "sourceType": source_type,
            "metadata": metadata,
        }
        retrieval_records.append(record)
        classification_records.append(
            {
                **record,
                "label": source_type,
            }
        )
        if entry.language in {"English", "Urdu", "Mixed"}:
            bilingual_records.append(record)

    return DatasetBundle(
        retrieval_records=retrieval_records,
        classification_records=classification_records,
        bilingual_records=bilingual_records,
    )
