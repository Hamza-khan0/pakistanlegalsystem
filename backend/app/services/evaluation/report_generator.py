from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.evaluation.dataset_readiness import evaluate_all_datasets
from app.services.evaluation.model_evaluation import build_model_registry_snapshot
from app.services.evaluation.retrieval_benchmark import list_retrieval_benchmarks
from app.services.ml.registry import read_json, report_dir, reports_root, write_json, write_text
from app.services.ml.training.trainer import list_ml_datasets, list_ml_models


def _markdown_report(payload: dict[str, Any]) -> str:
    readiness_lines = []
    for item in payload["payloadJson"]["datasetReadiness"]:
        readiness_lines.append(
            f"- `{item['taskName']}`: **{item['status']}** ({item['totalExamples']} examples, "
            f"class imbalance ratio {item['classImbalanceRatio']})"
        )
    comparison_lines = []
    for item in payload["payloadJson"]["modelSummary"]["comparisons"]:
        comparison_lines.append(
            f"- `{item['taskName']}`: baseline `{item['baselineModel']}` = `{item['baselineMetric']}`, "
            f"DNN `{item['dnnModel']}` = `{item['dnnMetric']}`, delta `{item['improvement']}`"
        )
    benchmark = payload["payloadJson"]["retrievalBenchmarkSummary"]
    benchmark_lines = [
        f"- `{mode}`: hit@k `{metrics['averageHitAtK']}`, MRR `{metrics['averageMrr']}`, average score `{metrics['averageScore']}`"
        for mode, metrics in benchmark.get("aggregate", {}).items()
    ]
    limitations = [f"- {item}" for item in payload["payloadJson"]["limitations"]]
    return "\n".join(
        [
            f"# {payload['title']}",
            "",
            "## Dataset readiness",
            *readiness_lines,
            "",
            "## Baseline vs DNN comparison",
            *comparison_lines,
            "",
            "## Retrieval benchmark summary",
            *benchmark_lines,
            "",
            "## Limitations and caveats",
            *limitations,
            "",
        ]
    )


def build_evaluation_report(db: Session, *, title: str | None = None) -> dict[str, Any]:
    datasets = list_ml_datasets(db)
    models = list_ml_models(db)
    readiness = evaluate_all_datasets(datasets)
    model_summary = build_model_registry_snapshot(models)
    benchmarks = list_retrieval_benchmarks()
    latest_benchmark = benchmarks[0] if benchmarks else {
        "queryCount": 0,
        "metricsJson": {"aggregate": {}, "heuristicEvaluation": True},
    }

    report_id = uuid4().hex
    payload_json = {
        "datasetReadiness": readiness,
        "modelSummary": model_summary,
        "retrievalBenchmarkSummary": latest_benchmark.get("metricsJson", {}),
        "latestBenchmarkId": latest_benchmark.get("id"),
        "limitations": [
            "Prediction confidence remains provisional until larger real-data training and calibration are completed.",
            "Retrieval benchmarking currently uses heuristic relevance expectations for the seeded corpus subset.",
            "Grouped case-level dataset splitting should be enforced before final large-scale training.",
            "Transformer explanations remain approximate and are not token-level attributions.",
        ],
    }
    base_payload = {
        "id": report_id,
        "reportType": "phase9_evaluation",
        "title": title or "Phase 9 training-readiness and evaluation report",
        "taskName": None,
        "datasetId": None,
        "modelId": None,
        "payloadJson": payload_json,
        "markdownPath": str(report_dir(report_id) / "report.md"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    markdown = _markdown_report(base_payload)
    write_json(report_dir(report_id) / "report.json", base_payload)
    write_text(report_dir(report_id) / "report.md", markdown)
    return base_payload


def list_evaluation_reports() -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for path in sorted(reports_root().glob("*/report.json"), reverse=True):
        reports.append(read_json(path))
    return reports


def get_evaluation_report(report_id: str) -> dict[str, Any] | None:
    path = report_dir(report_id) / "report.json"
    if not path.exists():
        return None
    return read_json(path)
