from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def build_dataset_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(record["label"] for record in records)
    language_counts = Counter(record["language"] for record in records)
    split_counts = Counter(record["split"] for record in records)
    label_source_counts = Counter(record["label_source"] for record in records)
    source_view_counts = Counter(record["source_view"] for record in records)
    case_counts = Counter(record["case_id"] for record in records)
    by_split_labels: dict[str, dict[str, int]] = defaultdict(dict)

    for split in split_counts:
        subset = [record for record in records if record["split"] == split]
        by_split_labels[split] = dict(Counter(record["label"] for record in subset))

    return {
        "recordCount": len(records),
        "uniqueCases": len(case_counts),
        "labelCounts": dict(label_counts),
        "languageMix": dict(language_counts),
        "splitCounts": dict(split_counts),
        "labelSourceMix": dict(label_source_counts),
        "sourceViewMix": dict(source_view_counts),
        "caseRecordCounts": dict(case_counts),
        "labelsBySplit": by_split_labels,
    }
