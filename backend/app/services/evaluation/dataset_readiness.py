from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.models.ml_dataset import MlDataset
from app.services.ml.registry import read_jsonl

READINESS_STATUSES = (
    "not_ready",
    "weak",
    "usable_for_demo",
    "usable_for_training",
    "strong",
)

WEAK_LABEL_SOURCES = {
    "heuristic",
    "weak_supervision",
    "synthetic",
    "generated",
    "llm_inferred",
}

STRONG_LABEL_SOURCES = {
    "manual_seed",
    "manual_curated",
    "verified_metadata",
}


def load_dataset_rows(dataset: MlDataset) -> list[dict[str, Any]]:
    return read_jsonl(Path(dataset.data_path))


def _safe_float(value: Any) -> float | None:
    if isinstance(value, (float, int)):
        return float(value)
    return None


def _readiness_bucket(score: int) -> str:
    if score < 25:
        return "not_ready"
    if score < 50:
        return "weak"
    if score < 70:
        return "usable_for_demo"
    if score < 85:
        return "usable_for_training"
    return "strong"


def evaluate_dataset_readiness(dataset: MlDataset) -> dict[str, Any]:
    rows = load_dataset_rows(dataset)
    label_counts = Counter(str(row.get("label") or "unlabeled") for row in rows)
    split_counts = Counter(str(row.get("split") or "unknown") for row in rows)
    label_source_counts = Counter(str(row.get("label_source") or "unknown") for row in rows)
    language_counts = Counter(str(row.get("language") or "Unknown") for row in rows)
    source_view_counts = Counter(str(row.get("source_view") or "unknown") for row in rows)

    missing_text_count = 0
    near_empty_count = 0
    duplicate_count = 0
    weak_label_count = 0
    low_ocr_count = 0
    seen_payloads: set[tuple[str, str, str, str]] = set()
    case_splits: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        case_id = str(row.get("case_id") or "")
        split = str(row.get("split") or "unknown")
        case_splits[case_id].add(split)

        text = str(row.get("normalized_text") or row.get("text") or "").strip()
        if not text:
            missing_text_count += 1
        elif len(text) < 80:
            near_empty_count += 1

        duplicate_key = (
            case_id,
            str(row.get("label") or ""),
            str(row.get("source_view") or ""),
            text[:320],
        )
        if duplicate_key in seen_payloads:
            duplicate_count += 1
        else:
            seen_payloads.add(duplicate_key)

        label_source = str(row.get("label_source") or "unknown").casefold()
        label_confidence = _safe_float(row.get("label_confidence"))
        if label_source in WEAK_LABEL_SOURCES or (label_confidence is not None and label_confidence < 0.75):
            weak_label_count += 1

        structured = row.get("structured_features")
        if isinstance(structured, dict):
            ocr_confidence = _safe_float(structured.get("avg_document_ocr_confidence"))
            if ocr_confidence is not None and ocr_confidence < 0.6:
                low_ocr_count += 1

    total = len(rows)
    unique_cases = len({str(row.get("case_id") or "") for row in rows if row.get("case_id")})
    class_counts = list(label_counts.values())
    minority_count = min(class_counts) if class_counts else 0
    class_imbalance_ratio = round((max(class_counts) / max(minority_count, 1)), 2) if class_counts else 0.0
    weak_label_percentage = round((weak_label_count / total) * 100, 2) if total else 0.0
    low_ocr_percentage = round((low_ocr_count / total) * 100, 2) if total else 0.0
    leakage_cases = sorted(case_id for case_id, splits in case_splits.items() if case_id and len(splits) > 1)
    leakage_ratio = round((len(leakage_cases) / unique_cases) * 100, 2) if unique_cases else 0.0

    warnings: list[str] = []
    recommendations: list[str] = []
    score = 100

    if total < 20:
        warnings.append("Dataset volume is too small for meaningful training.")
        recommendations.append("Add more labeled matters before attempting real training.")
        score -= 55
    elif total < 60:
        warnings.append("Dataset volume is still limited and best suited for demos or smoke tests.")
        recommendations.append("Expand the labeled corpus to improve generalization.")
        score -= 25

    validation_count = split_counts.get("validation", 0)
    test_count = split_counts.get("test", 0)
    if validation_count < 5 or test_count < 5:
        warnings.append("Validation or test split is too small for stable metrics.")
        recommendations.append("Rebuild the split strategy so validation and test sets have enough coverage.")
        score -= 20

    if len(label_counts) < 2:
        warnings.append("Only one class is represented in the current label set.")
        recommendations.append("Add labeled examples for the missing classes.")
        score -= 60
    elif minority_count < 3:
        warnings.append("At least one class has very few examples.")
        recommendations.append("Add more examples for minority classes to reduce imbalance.")
        score -= 20

    if class_imbalance_ratio >= 4:
        warnings.append("Class imbalance is pronounced.")
        recommendations.append("Balance the label distribution or apply class-aware sampling during training.")
        score -= 18

    if weak_label_percentage >= 45:
        warnings.append("A high share of labels is weak, synthetic, or low-confidence.")
        recommendations.append("Replace heuristic labels with stronger supervision before final training.")
        score -= 22

    if missing_text_count:
        warnings.append("Some records have no usable text input.")
        recommendations.append("Backfill missing text or exclude empty records from training.")
        score -= 15

    if near_empty_count / max(total, 1) >= 0.15:
        warnings.append("Many records are near-empty and may not support text learning.")
        recommendations.append("Increase extracted text coverage or merge sparse records into richer matter summaries.")
        score -= 12

    if duplicate_count / max(total, 1) >= 0.1:
        warnings.append("Duplicate or near-duplicate examples are present.")
        recommendations.append("Deduplicate repeated views before final training runs.")
        score -= 12

    if low_ocr_percentage >= 20:
        warnings.append("A noticeable portion of records comes from low-confidence OCR.")
        recommendations.append("Improve OCR quality or filter the weakest records before training.")
        score -= 10

    if leakage_cases:
        warnings.append("The same matter appears across multiple data splits, creating leakage risk.")
        recommendations.append("Adopt grouped splitting at the case level before serious model training.")
        score -= 30

    urdu_count = language_counts.get("Urdu", 0) + language_counts.get("Mixed", 0)
    if total and urdu_count / total < 0.1:
        warnings.append("Urdu and mixed-language examples are underrepresented.")
        recommendations.append("Add more Urdu or mixed-language records before multilingual final training.")
        score -= 8

    label_quality_notes = [
        source
        for source, count in label_source_counts.items()
        if count and source.casefold() not in STRONG_LABEL_SOURCES
    ]
    if label_quality_notes:
        recommendations.append(
            f"Review weaker label sources before final training: {', '.join(sorted(label_quality_notes))}."
        )

    return {
        "datasetId": dataset.id,
        "taskName": dataset.task_name.value,
        "datasetName": dataset.name,
        "datasetVersion": dataset.version,
        "status": _readiness_bucket(max(score, 0)),
        "score": max(score, 0),
        "totalExamples": total,
        "uniqueCases": unique_cases,
        "classDistribution": dict(label_counts),
        "classImbalanceRatio": class_imbalance_ratio,
        "splitCounts": dict(split_counts),
        "labelSourceDistribution": dict(label_source_counts),
        "languageDistribution": dict(language_counts),
        "sourceViewDistribution": dict(source_view_counts),
        "missingTextExamples": missing_text_count,
        "nearEmptyExamples": near_empty_count,
        "duplicateExamples": duplicate_count,
        "weakLabelPercentage": weak_label_percentage,
        "lowOcrConfidencePercentage": low_ocr_percentage,
        "leakageCaseCount": len(leakage_cases),
        "leakageCaseIds": leakage_cases[:12],
        "warnings": warnings,
        "recommendations": recommendations,
    }


def evaluate_all_datasets(datasets: list[MlDataset]) -> list[dict[str, Any]]:
    return [evaluate_dataset_readiness(dataset) for dataset in datasets]
