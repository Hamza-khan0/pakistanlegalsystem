from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tier1_document import Tier1Document
from app.models.tier1_label import Tier1Label
from app.services.tier1_data.dataset_builder import tier1_readiness


def tier1_report(db: Session) -> dict:
    documents = list(db.scalars(select(Tier1Document)).all())
    labels = list(db.scalars(select(Tier1Label)).all())
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "documentCount": len(documents),
        "labelCount": len(labels),
        "sourceTypeCounts": dict(Counter(document.source_type for document in documents)),
        "languageCounts": dict(Counter(document.language for document in documents)),
        "reviewCounts": {
            "reviewed": sum(1 for label in labels if label.reviewed),
            "needsReview": sum(1 for label in labels if label.needs_review),
            "weak": sum(1 for label in labels if not label.reviewed),
        },
        "readiness": tier1_readiness(db),
    }
