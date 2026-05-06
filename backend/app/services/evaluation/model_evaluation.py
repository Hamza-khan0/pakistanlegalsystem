from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.models.ml_model import MlModel


def _metric(model: MlModel) -> float:
    raw = model.metrics_json.get("primaryMetric")
    if isinstance(raw, (float, int)):
        return float(raw)
    return 0.0


def _language_metrics(model: MlModel) -> dict[str, Any]:
    test_metrics = model.metrics_json.get("test")
    if isinstance(test_metrics, dict):
        per_language = test_metrics.get("per_language")
        if isinstance(per_language, dict):
            return per_language
    return {}


def build_model_registry_snapshot(models: list[MlModel]) -> dict[str, Any]:
    grouped: dict[str, list[MlModel]] = defaultdict(list)
    for model in models:
        grouped[model.task_name.value].append(model)

    experiments: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    leaderboard: dict[str, list[dict[str, Any]]] = {}

    for task_name, task_models in grouped.items():
        ranked = sorted(task_models, key=_metric, reverse=True)
        leaderboard[task_name] = []
        for model in ranked:
            experiment = {
                "experimentId": model.metadata_json.get("experimentId") or model.id,
                "taskName": task_name,
                "modelId": model.id,
                "modelFamily": model.model_family.value,
                "modelName": model.name,
                "datasetVersion": model.metadata_json.get("datasetVersion"),
                "featureConfiguration": model.metadata_json.get("featureConfiguration", {}),
                "trainingConfig": model.config_json,
                "seed": model.metadata_json.get("trainingSeed", 42),
                "hardware": model.metadata_json.get("hardware", {}),
                "trainMetrics": model.metrics_json.get("train", {}),
                "validationMetrics": model.metrics_json.get("validation", {}),
                "testMetrics": model.metrics_json.get("test", {}),
                "perLanguageMetrics": _language_metrics(model),
                "confusionMatrix": model.metrics_json.get("test", {}).get("confusion_matrix", [])
                if isinstance(model.metrics_json.get("test"), dict)
                else [],
                "artifactPath": model.artifact_path,
                "metricsPath": model.metrics_path,
                "notes": model.training_summary,
                "createdAt": model.created_at.isoformat(),
            }
            experiments.append(experiment)
            leaderboard[task_name].append(
                {
                    "modelId": model.id,
                    "modelName": model.name,
                    "modelFamily": model.model_family.value,
                    "primaryMetric": round(_metric(model), 4),
                    "status": model.status.value,
                    "datasetVersion": model.metadata_json.get("datasetVersion"),
                    "perLanguageMetrics": _language_metrics(model),
                }
            )

        best_baseline = next((model for model in ranked if model.model_family.value == "Baseline"), None)
        best_dnn = next((model for model in ranked if model.model_family.value != "Baseline"), None)
        if best_baseline or best_dnn:
            baseline_metric = _metric(best_baseline) if best_baseline else None
            dnn_metric = _metric(best_dnn) if best_dnn else None
            comparisons.append(
                {
                    "taskName": task_name,
                    "baselineModel": best_baseline.name if best_baseline else None,
                    "baselineMetric": round(baseline_metric, 4) if baseline_metric is not None else None,
                    "dnnModel": best_dnn.name if best_dnn else None,
                    "dnnMetric": round(dnn_metric, 4) if dnn_metric is not None else None,
                    "improvement": (
                        round(dnn_metric - baseline_metric, 4)
                        if baseline_metric is not None and dnn_metric is not None
                        else None
                    ),
                }
            )

    return {
        "experiments": experiments,
        "leaderboard": leaderboard,
        "comparisons": comparisons,
    }
