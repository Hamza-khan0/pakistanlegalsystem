from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import MlTaskName
from app.models.ml_dataset import MlDataset
from app.models.tier1_document import Tier1Document
from app.models.tier1_label import Tier1Label
from app.services.ml.registry import read_jsonl
from app.services.tier1_data.dataset_builder import tier1_readiness
from app.services.tier1_data.paths import training_export_dir


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _tier1_datasets(db: Session) -> list[MlDataset]:
    datasets = list(db.scalars(select(MlDataset).order_by(MlDataset.created_at.desc())).all())
    return [dataset for dataset in datasets if dataset.metadata_json.get("tier1") is True]


def _source_report(db: Session) -> dict[str, Any]:
    documents = list(db.scalars(select(Tier1Document)).all())
    return {
        "documentCount": len(documents),
        "sourceTypeCounts": dict(Counter(document.source_type for document in documents)),
        "sourceNameCounts": dict(Counter(document.source_name for document in documents)),
        "languageCounts": dict(Counter(document.language for document in documents)),
        "documentTypeCounts": dict(Counter(document.document_type for document in documents)),
    }


def _label_report(db: Session) -> dict[str, Any]:
    labels = list(db.scalars(select(Tier1Label)).all())
    by_task: dict[str, Counter] = defaultdict(Counter)
    for label in labels:
        by_task[label.task_name.value][label.label] += 1
    return {
        "labelCount": len(labels),
        "reviewedCount": sum(1 for label in labels if label.reviewed),
        "needsReviewCount": sum(1 for label in labels if label.needs_review),
        "labelSourceCounts": dict(Counter(label.label_source for label in labels)),
        "classCountsByTask": {task: dict(counter) for task, counter in by_task.items()},
    }


def export_training_bundle(db: Session) -> dict[str, Any]:
    export_dir = training_export_dir()
    if export_dir.exists():
        shutil.rmtree(export_dir)
    (export_dir / "datasets").mkdir(parents=True, exist_ok=True)
    (export_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (export_dir / "configs").mkdir(parents=True, exist_ok=True)

    dataset_counts: dict[str, dict[str, int]] = {}
    warnings: list[str] = []
    datasets = _tier1_datasets(db)
    for task in MlTaskName:
        dataset = next((item for item in datasets if item.task_name == task), None)
        rows = read_jsonl(Path(dataset.data_path)) if dataset else []
        counts: dict[str, int] = {}
        for split in ("train", "validation", "test"):
            split_rows = [row for row in rows if row.get("split") == split]
            suffix = "val" if split == "validation" else split
            _write_jsonl(export_dir / "datasets" / f"{task.value}.{suffix}.jsonl", split_rows)
            counts[suffix] = len(split_rows)
        dataset_counts[task.value] = counts
        if not rows:
            warnings.append(f"No Tier 1 dataset rows were available for {task.value}.")

    readiness = tier1_readiness(db)
    _write_json(export_dir / "metadata" / "dataset_report.json", {dataset.task_name.value: dataset.report_json for dataset in datasets})
    _write_json(export_dir / "metadata" / "label_report.json", _label_report(db))
    _write_json(export_dir / "metadata" / "readiness_report.json", readiness)
    _write_json(export_dir / "metadata" / "source_report.json", _source_report(db))
    (export_dir / "configs" / "training_config.yaml").write_text(
        "\n".join(
            [
                "project: AI Legal Chambers",
                "bundle_type: tier1_training_export",
                "auto_train: false",
                "tasks:",
                *[f"  - {task.value}" for task in MlTaskName],
                "recommended_local_training: baseline",
                "recommended_gpu_training: transformer, hybrid_mlp",
            ]
        ),
        encoding="utf-8",
    )
    (export_dir / "configs" / "README_TRAINING.md").write_text(
        "# Tier 1 Training Bundle\n\n"
        "This bundle contains JSONL datasets and metadata only. It does not contain credentials and does not start training automatically.\n\n"
        "Use baseline training locally for smoke tests. Run transformer or hybrid MLP training manually on suitable GPU/cloud hardware after label audit.\n",
        encoding="utf-8",
    )

    zip_path = Path("training_export_bundle.zip")
    if zip_path.exists():
        zip_path.unlink()
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in export_dir.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(export_dir.parent))

    return {
        "status": "success",
        "message": "Training bundle exported. No model training was started.",
        "exportDir": str(export_dir),
        "zipPath": str(zip_path),
        "datasetCounts": dataset_counts,
        "warnings": warnings,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
