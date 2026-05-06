from __future__ import annotations

from collections import Counter
from typing import Any

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score


def classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
    *,
    languages: list[str] | None = None,
) -> dict[str, Any]:
    if not y_true:
        return {
            "accuracy": 0.0,
            "precision_macro": 0.0,
            "recall_macro": 0.0,
            "f1_macro": 0.0,
            "f1_weighted": 0.0,
            "confusion_matrix": [],
            "labels": labels,
            "support": {},
            "per_class": {},
            "per_language": {},
        }

    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    per_class = {
        label: {
            "precision": round(float(report.get(label, {}).get("precision", 0.0)), 4),
            "recall": round(float(report.get(label, {}).get("recall", 0.0)), 4),
            "f1": round(float(report.get(label, {}).get("f1-score", 0.0)), 4),
            "support": int(report.get(label, {}).get("support", 0)),
        }
        for label in labels
    }
    per_language: dict[str, Any] = {}
    if languages and len(languages) == len(y_true):
        grouped: dict[str, tuple[list[str], list[str]]] = {}
        for truth, pred, language in zip(y_true, y_pred, languages):
            bucket = grouped.setdefault(language or "Unknown", ([], []))
            bucket[0].append(truth)
            bucket[1].append(pred)
        per_language = {
            language: {
                "accuracy": round(float(accuracy_score(values[0], values[1])), 4),
                "f1_macro": round(float(f1_score(values[0], values[1], average="macro", zero_division=0)), 4),
                "support": len(values[0]),
            }
            for language, values in grouped.items()
        }

    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "labels": labels,
        "support": dict(Counter(y_true)),
        "per_class": per_class,
        "per_language": per_language,
    }


def combine_split_metrics(
    *,
    train_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
    test_metrics: dict[str, Any],
    label_schema: list[str],
) -> dict[str, Any]:
    return {
        "primaryMetric": test_metrics.get("f1_macro", 0.0),
        "labelSchema": label_schema,
        "train": train_metrics,
        "validation": validation_metrics,
        "test": test_metrics,
    }
