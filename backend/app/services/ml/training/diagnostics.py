from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.models.case_prediction import CasePrediction
from app.models.enums import MlModelFamily
from app.models.ml_model import MlModel
from app.services.ml.registry import read_json
from app.services.ml.training.inference import get_case_for_prediction, list_case_predictions


def _baseline_diagnostics(model: MlModel) -> dict[str, Any]:
    artifact_path = Path(model.artifact_path or "")
    model_path = artifact_path / "baseline.joblib"
    if not model.artifact_path or not model_path.exists():
        return {
            "classifier": "Unavailable",
            "artifactMissing": True,
            "artifactPath": str(model_path),
            "explanationNote": (
                "Diagnostics are unavailable because the stored baseline artifact is missing. "
                "Retrain this model before relying on feature-level explanations."
            ),
        }
    bundle = joblib.load(model_path)
    classifier = bundle["classifier"]
    text_vectorizer = bundle["text_vectorizer"]
    struct_vectorizer = bundle["struct_vectorizer"]
    diagnostics: dict[str, Any] = {
        "classifier": classifier.__class__.__name__,
        "textFeatureCount": len(text_vectorizer.get_feature_names_out()),
        "structuredFeatureCount": len(struct_vectorizer.feature_names_),
    }
    if hasattr(classifier, "coef_"):
        coef = classifier.coef_
        feature_names = list(text_vectorizer.get_feature_names_out()) + list(struct_vectorizer.feature_names_)
        if coef.ndim == 2 and coef.shape[0] > 0:
            mean_weights = np.mean(np.abs(coef), axis=0)
            top_indices = np.argsort(mean_weights)[::-1][:10]
            diagnostics["topFeatures"] = [
                {"feature": feature_names[int(index)], "weight": round(float(mean_weights[int(index)]), 4)}
                for index in top_indices
            ]
    return diagnostics


def _transformer_diagnostics(model: MlModel) -> dict[str, Any]:
    config_path = Path(model.artifact_path or "") / "transformer_config.json"
    config = read_json(config_path) if model.artifact_path and config_path.exists() else {}
    return {
        "checkpoint": config.get("checkpoint", model.metadata_json.get("modelName", "")),
        "labelSchema": config.get("labelSchema", model.label_schema),
        "explanationNote": (
            "Transformer predictions are supported by multilingual text patterns and chamber context, "
            "but this system does not claim token-level interpretability."
        ),
    }


def _hybrid_diagnostics(model: MlModel) -> dict[str, Any]:
    config_path = Path(model.artifact_path or "") / "hybrid_preprocessor.json"
    config = read_json(config_path) if model.artifact_path and config_path.exists() else {}
    return {
        "structuredDim": config.get("structuredDim", 0),
        "categoryMaps": {key: len(value) for key, value in config.get("categoryMaps", {}).items()},
        "explanationNote": (
            "Hybrid predictions combine text patterns with structured matter signals such as forum, stage, "
            "risk flags, and grounded-source counts."
        ),
    }


def get_model_diagnostics(model: MlModel) -> dict[str, Any]:
    if model.model_family == MlModelFamily.BASELINE:
        return _baseline_diagnostics(model)
    if model.model_family == MlModelFamily.TRANSFORMER:
        return _transformer_diagnostics(model)
    return _hybrid_diagnostics(model)


def explain_case_predictions(db: Session, case_id: str) -> list[dict[str, Any]]:
    case = get_case_for_prediction(db, case_id)
    if case is None:
        return []
    latest_by_task: dict[str, CasePrediction] = {}
    for prediction in list_case_predictions(db, case_id):
        latest_by_task.setdefault(prediction.task_name.value, prediction)

    structured_summary = {
        "forum": case.forum,
        "filingStage": case.filing_stage,
        "issueCount": len(case.legal_issues),
        "riskFlagCount": len(case.risk_flags),
        "documentCount": len(case.documents),
        "researchCount": len(case.research_entries),
        "draftCount": len(case.drafts),
        "groundedArtifacts": sum(1 for artifact in case.intelligence_artifacts if artifact.grounding_links),
        "groundedRuns": sum(1 for run in case.chamber_runs if run.grounding_links),
    }

    explanations: list[dict[str, Any]] = []
    for prediction in latest_by_task.values():
        model = prediction.model
        diagnostics = get_model_diagnostics(model) if model else {}
        top_probabilities = sorted(
            prediction.probabilities_json.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:3]
        explanations.append(
            {
                "predictionId": prediction.id,
                "taskName": prediction.task_name.value,
                "predictedLabel": prediction.predicted_label,
                "confidence": prediction.confidence,
                "modelFamily": model.model_family.value if model else "Unknown",
                "modelName": model.name if model else "Unknown",
                "explanationNote": diagnostics.get(
                    "explanationNote",
                    "Prediction derived from the trained legal matter model for this task.",
                ),
                "topProbabilities": [
                    {"label": label, "score": round(float(score), 4)} for label, score in top_probabilities
                ],
                "structuredSignals": structured_summary,
                "diagnostics": diagnostics,
            }
        )
    return explanations
