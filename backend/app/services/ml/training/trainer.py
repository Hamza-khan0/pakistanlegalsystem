from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import MlModelFamily, MlModelStatus
from app.models.ml_dataset import MlDataset
from app.models.ml_model import MlModel
from app.services.ml.registry import model_dir, read_jsonl, write_json
from app.services.ml.training.diagnostics import get_model_diagnostics


def get_dataset_or_none(db: Session, dataset_id: str) -> MlDataset | None:
    return db.scalar(select(MlDataset).where(MlDataset.id == dataset_id))


def list_ml_datasets(db: Session) -> list[MlDataset]:
    return list(db.scalars(select(MlDataset).order_by(MlDataset.created_at.desc())).all())


def list_ml_models(db: Session) -> list[MlModel]:
    return list(db.scalars(select(MlModel).order_by(MlModel.created_at.desc())).all())


def get_ml_model_or_none(db: Session, model_id: str) -> MlModel | None:
    return db.scalar(select(MlModel).where(MlModel.id == model_id))


def train_ml_model(
    db: Session,
    *,
    dataset: MlDataset,
    model_family: MlModelFamily,
    model_name: str | None = None,
    hyperparameters: dict | None = None,
) -> MlModel:
    model = MlModel(
        dataset_id=dataset.id,
        task_name=dataset.task_name,
        model_family=model_family,
        name=model_name or f"{dataset.task_name.value}-{model_family.value.lower()}",
        status=MlModelStatus.TRAINING,
        config_json=hyperparameters or {},
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    rows = read_jsonl(Path(dataset.data_path))
    max_rows = int((hyperparameters or {}).get("maxRows", 0) or 0)
    if max_rows > 0 and len(rows) > max_rows:
        rows = rows[:max_rows]
    artifact_dir = model_dir(model.id)
    resolved_model_name = model_name
    experiment_id = uuid4().hex

    try:
        if model_family == MlModelFamily.BASELINE:
            from app.services.ml.training.baselines import train_baseline_model

            result = train_baseline_model(
                task_name=dataset.task_name,
                rows=rows,
                artifact_dir=artifact_dir,
            )
        elif model_family == MlModelFamily.TRANSFORMER:
            from app.services.ml.training.xlmr import train_transformer_model

            resolved_model_name = model_name
            result = train_transformer_model(
                task_name=dataset.task_name,
                rows=rows,
                artifact_dir=artifact_dir,
                model_name=model_name,
            )
        else:
            from app.services.ml.training.hybrid_mlp import train_hybrid_model

            result = train_hybrid_model(
                task_name=dataset.task_name,
                rows=rows,
                artifact_dir=artifact_dir,
            )

        metrics_path = artifact_dir / "metrics.json"
        write_json(metrics_path, result.metrics)
        model.status = MlModelStatus.READY
        model.artifact_path = str(artifact_dir)
        model.metrics_path = str(metrics_path)
        model.metrics_json = result.metrics
        model.label_schema = result.label_schema
        model.training_summary = result.summary
        model.metadata_json = {
            "experimentId": experiment_id,
            "artifactFiles": result.artifact_files,
            "datasetVersion": dataset.version,
            "modelName": resolved_model_name or model.name,
            "languageCoverage": sorted({row.get("language", "Unknown") for row in rows}),
            "featureConfiguration": {
                "text": True,
                "structured": model_family != MlModelFamily.TRANSFORMER,
            },
            "trainingConfig": hyperparameters or {},
            "trainingSeed": int((hyperparameters or {}).get("seed", 42)),
            "hardware": {
                "device": "cpu",
                "accelerator": "not_configured",
            },
            "splitStrategy": dataset.split_strategy,
            "labelStrategy": dataset.label_strategy,
        }
        model.metadata_json["diagnostics"] = get_model_diagnostics(model)
    except Exception as exc:
        model.status = MlModelStatus.FAILED
        model.training_summary = str(exc)
        model.metadata_json = {"error": str(exc)}
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
