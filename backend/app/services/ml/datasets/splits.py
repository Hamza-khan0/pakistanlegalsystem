from __future__ import annotations

from hashlib import sha256

from app.models.enums import DatasetSplit


def deterministic_split(record_id: str) -> DatasetSplit:
    score = int(sha256(record_id.encode("utf-8")).hexdigest(), 16) % 100
    if score < 70:
        return DatasetSplit.TRAIN
    if score < 85:
        return DatasetSplit.VALIDATION
    return DatasetSplit.TEST
