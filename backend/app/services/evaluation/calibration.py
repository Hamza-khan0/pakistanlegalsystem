from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case_prediction import CasePrediction
from app.models.ml_model import MlModel
from app.services.ml.datasets.labeling import get_case_label
from app.services.ml.registry import calibration_root, read_json, write_json


def _calibration_path(model_id: str) -> Path:
    return calibration_root() / f"{model_id}.json"


def _bin_payload(start: float, end: float, scores: list[float], correctness: list[float]) -> dict[str, Any]:
    count = len(scores)
    avg_confidence = round(sum(scores) / count, 4) if count else 0.0
    avg_accuracy = round(sum(correctness) / count, 4) if count else 0.0
    return {
        "binStart": round(start, 2),
        "binEnd": round(end, 2),
        "count": count,
        "avgConfidence": avg_confidence,
        "avgAccuracy": avg_accuracy,
        "gap": round(avg_confidence - avg_accuracy, 4) if count else 0.0,
    }


def build_calibration_record(
    db: Session,
    *,
    model: MlModel,
    persist: bool = True,
) -> dict[str, Any]:
    predictions = list(
        db.scalars(
            select(CasePrediction)
            .where(CasePrediction.model_id == model.id)
            .order_by(CasePrediction.created_at.desc())
        ).all()
    )

    scored_predictions: list[tuple[float, float, float]] = []
    warnings: list[str] = []
    for prediction in predictions:
        label_info = get_case_label(prediction.case_id, model.task_name)
        if label_info is None:
            continue
        predicted_probability = float(prediction.probabilities_json.get(label_info.label, 0.0))
        is_correct = 1.0 if prediction.predicted_label == label_info.label else 0.0
        scored_predictions.append((float(prediction.confidence), is_correct, predicted_probability))

    if not scored_predictions:
        warnings.append("No scored predictions with matching seed labels are available yet for calibration.")

    bins: list[dict[str, Any]] = []
    sample_count = len(scored_predictions)
    expected_calibration_error = 0.0
    brier_score = 0.0
    for index in range(10):
        start = index / 10
        end = 1.0 if index == 9 else (index + 1) / 10
        scores = [
            score
            for score, _, _ in scored_predictions
            if start <= score and (score <= end if index == 9 else score < end)
        ]
        correctness = [
            correct
            for score, correct, _ in scored_predictions
            if start <= score and (score <= end if index == 9 else score < end)
        ]
        payload = _bin_payload(start, end, scores, correctness)
        bins.append(payload)
        if sample_count:
            expected_calibration_error += abs(payload["gap"]) * (payload["count"] / sample_count)

    if sample_count:
        brier_score = round(
            sum((probability - correctness) ** 2 for _, correctness, probability in scored_predictions) / sample_count,
            4,
        )
    expected_calibration_error = round(expected_calibration_error, 4)

    if sample_count < 12:
        warnings.append("Calibration diagnostics are based on a very small sample and should be treated as provisional.")

    payload = {
        "modelId": model.id,
        "taskName": model.task_name.value,
        "calibrationMethod": "scaffold_only",
        "sampleCount": sample_count,
        "hasCalibratedScores": False,
        "supportedMethods": ["temperature_scaling", "platt_scaling", "isotonic_regression"],
        "metricsJson": {
            "expectedCalibrationError": expected_calibration_error,
            "brierScore": brier_score,
            "confidenceHistogram": bins,
        },
        "reliabilityJson": {
            "bins": bins,
            "warnings": warnings,
        },
        "notes": (
            "Phase 9 stores calibration scaffolding and reliability data. "
            "Final calibrated probabilities should be produced after larger real-data training."
        ),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    if persist:
        write_json(_calibration_path(model.id), payload)
    return payload


def get_calibration_record(model_id: str) -> dict[str, Any] | None:
    path = _calibration_path(model_id)
    if not path.exists():
        return None
    return read_json(path)
