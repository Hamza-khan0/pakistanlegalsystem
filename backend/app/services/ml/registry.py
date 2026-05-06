from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import settings


def ml_root() -> Path:
    root = Path(settings.ml_artifacts_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def datasets_root() -> Path:
    path = ml_root() / "datasets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def models_root() -> Path:
    path = ml_root() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def retrieval_root() -> Path:
    path = ml_root() / "retrieval"
    path.mkdir(parents=True, exist_ok=True)
    return path


def evaluation_root() -> Path:
    path = ml_root() / "evaluation"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reports_root() -> Path:
    path = evaluation_root() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def benchmarks_root() -> Path:
    path = evaluation_root() / "benchmarks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def calibration_root() -> Path:
    path = evaluation_root() / "calibration"
    path.mkdir(parents=True, exist_ok=True)
    return path


def dataset_dir(dataset_id: str) -> Path:
    path = datasets_root() / dataset_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def model_dir(model_id: str) -> Path:
    path = models_root() / model_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_dir(report_id: str) -> Path:
    path = reports_root() / report_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def benchmark_dir(benchmark_id: str) -> Path:
    path = benchmarks_root() / benchmark_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
