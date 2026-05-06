from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.case import Case
from app.models.case_prediction import CasePrediction
from app.models.chamber_run import ChamberRun
from app.models.enums import MlModelFamily, MlModelStatus, MlTaskName
from app.models.intelligence_artifact import IntelligenceArtifact
from app.models.ml_model import MlModel
from app.services.corpus.normalization import normalize_text, unique_tokens
from app.services.ml.datasets.features import build_case_text, build_structured_features
from app.services.ml.registry import read_json
from app.services.ml.training.imported_case_type import (
    LEGAL_AUTHORITY_WARNING,
    ensure_imported_case_type_model_record,
    predict_case_type_text,
)
from functools import lru_cache

SUPERVISED_CASE_PREDICTION_TASKS = [
    MlTaskName.CASE_OUTCOME,
    MlTaskName.MAINTAINABILITY,
    MlTaskName.RISK_SCORING,
    MlTaskName.CASE_TYPE,
]


@lru_cache(maxsize=1)
def _torch_module():
    import torch

    return torch


@lru_cache(maxsize=1)
def _transformer_inference_stack():
    from app.services.ml.training.transformer_runtime import ensure_text_only_transformers_runtime

    ensure_text_only_transformers_runtime()
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    return AutoModelForSequenceClassification, AutoTokenizer


def _case_query():
    return (
        select(Case)
        .options(
            selectinload(Case.documents),
            selectinload(Case.notes),
            selectinload(Case.research_entries),
            selectinload(Case.drafts),
            selectinload(Case.intelligence_artifacts).selectinload(IntelligenceArtifact.grounding_links),
            selectinload(Case.chamber_runs).selectinload(ChamberRun.grounding_links),
            selectinload(Case.predictions).selectinload(CasePrediction.model),
        )
    )


def get_case_for_prediction(db: Session, case_id: str) -> Case | None:
    return db.scalar(_case_query().where(Case.id == case_id))


def get_model_or_none(db: Session, model_id: str) -> MlModel | None:
    return db.scalar(select(MlModel).where(MlModel.id == model_id))


def get_latest_model_for_task(db: Session, task_name: MlTaskName) -> MlModel | None:
    preferred_family = settings.ml_default_inference_family.strip()
    if preferred_family:
        preferred_model = db.scalar(
            select(MlModel)
            .where(
                MlModel.task_name == task_name,
                MlModel.status == MlModelStatus.READY,
                MlModel.model_family == preferred_family,
            )
            .order_by(MlModel.created_at.desc())
        )
        if preferred_model:
            return preferred_model

    return db.scalar(
        select(MlModel)
        .where(MlModel.task_name == task_name, MlModel.status == MlModelStatus.READY)
        .order_by(MlModel.created_at.desc())
    )


def list_case_predictions(db: Session, case_id: str) -> list[CasePrediction]:
    return list(
        db.scalars(
            select(CasePrediction)
            .options(selectinload(CasePrediction.model))
            .where(CasePrediction.case_id == case_id)
            .order_by(CasePrediction.created_at.desc())
        ).all()
    )


def _build_case_row(case: Case, task_name: MlTaskName) -> dict[str, Any]:
    text = build_case_text(case)
    return {
        "id": f"inference:{case.id}:{task_name.value}",
        "case_id": case.id,
        "task_name": task_name.value,
        "text": text,
        "normalized_text": normalize_text(text),
        "structured_features": {
            **build_structured_features(case),
            "source_view": "case_core",
            "text_length": len(text),
            "normalized_length": len(normalize_text(text)),
        },
    }


def _predict_with_baseline(model: MlModel, row: dict[str, Any]) -> tuple[str, float, dict[str, float]]:
    bundle = joblib.load(Path(model.artifact_path) / "baseline.joblib")
    text_vectorizer = bundle["text_vectorizer"]
    struct_vectorizer = bundle["struct_vectorizer"]
    classifier = bundle["classifier"]
    text_matrix = text_vectorizer.transform([row["normalized_text"] or row["text"]])
    struct_matrix = struct_vectorizer.transform([row["structured_features"]])
    from scipy.sparse import hstack
    combined = hstack([text_matrix, struct_matrix])
    if model.task_name == MlTaskName.RISK_SCORING:
        probabilities = classifier.predict_proba(combined.toarray())[0]
    else:
        probabilities = classifier.predict_proba(combined)[0]
    labels = list(classifier.classes_)
    top_index = int(probabilities.argmax())
    return labels[top_index], float(probabilities[top_index]), {
        label: round(float(score), 4) for label, score in zip(labels, probabilities)
    }


def _predict_with_transformer(model: MlModel, row: dict[str, Any]) -> tuple[str, float, dict[str, float]]:
    torch = _torch_module()
    AutoModelForSequenceClassification, AutoTokenizer = _transformer_inference_stack()
    config = read_json(Path(model.artifact_path) / "transformer_config.json")
    tokenizer = AutoTokenizer.from_pretrained(model.artifact_path)
    classifier = AutoModelForSequenceClassification.from_pretrained(model.artifact_path)
    encoded = tokenizer(
        row["text"],
        truncation=True,
        padding="max_length",
        max_length=256,
        return_tensors="pt",
    )
    with torch.no_grad():
        logits = classifier(**encoded).logits
        probabilities_tensor = torch.softmax(logits, dim=1).squeeze(0)
    labels = list(config["labelSchema"])
    probabilities = probabilities_tensor.tolist()
    top_index = int(torch.argmax(probabilities_tensor).item())
    return labels[top_index], float(probabilities[top_index]), {
        label: round(float(score), 4) for label, score in zip(labels, probabilities)
    }


def _predict_with_hybrid(model: MlModel, row: dict[str, Any]) -> tuple[str, float, dict[str, float]]:
    torch = _torch_module()
    from app.services.ml.training.hybrid_mlp import HybridClassifier, _encode_structured

    preprocessor = read_json(Path(model.artifact_path) / "hybrid_preprocessor.json")
    label_schema = list(preprocessor["labelSchema"])
    vocab = {key: int(value) for key, value in preprocessor["vocab"].items()}
    category_maps = {
        key: {sub_key: int(sub_value) for sub_key, sub_value in value.items()}
        for key, value in preprocessor["categoryMaps"].items()
    }
    classifier = HybridClassifier(
        vocab_size=len(vocab),
        structured_dim=int(preprocessor["structuredDim"]),
        num_labels=len(label_schema),
    )
    classifier.load_state_dict(torch.load(Path(model.artifact_path) / "hybrid_model.pt", map_location="cpu"))
    classifier.eval()
    token_ids = [vocab.get(token, 1) for token in unique_tokens(row["normalized_text"] or row["text"])[:256]] or [0]
    structured = _encode_structured(row, category_maps=category_maps)
    with torch.no_grad():
        logits = classifier(
            torch.tensor(token_ids, dtype=torch.long),
            torch.tensor([0], dtype=torch.long),
            torch.tensor([structured], dtype=torch.float32),
        )
        probabilities_tensor = torch.softmax(logits, dim=1).squeeze(0)
    probabilities = probabilities_tensor.tolist()
    top_index = int(torch.argmax(probabilities_tensor).item())
    return label_schema[top_index], float(probabilities[top_index]), {
        label: round(float(score), 4) for label, score in zip(label_schema, probabilities)
    }


def predict_case(
    db: Session,
    *,
    case: Case,
    task_name: MlTaskName,
    model: MlModel,
) -> CasePrediction:
    row = _build_case_row(case, task_name)
    if model.model_family == MlModelFamily.BASELINE:
        predicted_label, confidence, probabilities = _predict_with_baseline(model, row)
    elif model.model_family == MlModelFamily.TRANSFORMER:
        predicted_label, confidence, probabilities = _predict_with_transformer(model, row)
    else:
        predicted_label, confidence, probabilities = _predict_with_hybrid(model, row)

    prediction = CasePrediction(
        case_id=case.id,
        model_id=model.id,
        task_name=task_name,
        predicted_label=predicted_label,
        confidence=round(confidence, 4),
        probabilities_json=probabilities,
        input_summary=(row["text"][:700] + "...") if len(row["text"]) > 700 else row["text"],
        warning_text="Predictive assistance only. Labels are derived from limited supervised signals and should not be treated as deterministic legal truth.",
        metadata_json={
            "modelFamily": model.model_family.value,
            "datasetVersion": model.metadata_json.get("datasetVersion"),
        },
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def predict_imported_case_type_for_case(
    db: Session,
    *,
    case: Case,
    load_model: bool = True,
) -> CasePrediction | None:
    model = ensure_imported_case_type_model_record(db)
    if model is None or model.status != MlModelStatus.READY:
        return None
    existing = db.scalar(
        select(CasePrediction)
        .where(
            CasePrediction.case_id == case.id,
            CasePrediction.task_name == MlTaskName.CASE_TYPE,
            CasePrediction.model_id == model.id,
        )
        .order_by(CasePrediction.created_at.desc())
    )
    if existing is not None:
        metadata = dict(existing.metadata_json or {})
        if metadata.get("modelSource") == "trained_imported" and "modelStatus" not in metadata:
            metadata.update(
                {
                    "modelStatus": "trained_imported_loaded",
                    "metrics": {
                        "primaryMetric": model.metrics_json.get("primaryMetric"),
                        "labels": model.metrics_json.get("labels", model.label_schema),
                    },
                    "legalAuthorityWarning": LEGAL_AUTHORITY_WARNING,
                }
            )
            existing.metadata_json = metadata
            db.add(existing)
            db.commit()
            db.refresh(existing)
        return existing

    if not load_model:
        return None

    row = _build_case_row(case, MlTaskName.CASE_TYPE)
    result = predict_case_type_text(row["text"])
    if result.get("model_source") != "trained_imported":
        return None

    prediction = CasePrediction(
        case=case,
        model_id=model.id,
        task_name=MlTaskName.CASE_TYPE,
        predicted_label=str(result["predicted_label"]),
        confidence=round(float(result["confidence"]), 4),
        probabilities_json=result["probabilities"],
        input_summary=(row["text"][:700] + "...") if len(row["text"]) > 700 else row["text"],
        warning_text=LEGAL_AUTHORITY_WARNING,
        metadata_json={
            "modelFamily": MlModelFamily.TRANSFORMER.value,
            "datasetVersion": model.dataset.version if model.dataset else "",
            "modelSource": "trained_imported",
            "modelStatus": result.get("model_status"),
            "bundleManifest": result.get("bundle_manifest", {}),
            "metrics": result.get("metrics", {}),
            "integration": "case_prediction_pipeline",
            "labelSchema": model.label_schema,
        },
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def predict_case_tasks(
    db: Session,
    *,
    case: Case,
    task_name: MlTaskName | None = None,
    model_id: str | None = None,
) -> list[CasePrediction]:
    explicit_model = get_model_or_none(db, model_id) if model_id else None
    if explicit_model and task_name is None:
        tasks = [explicit_model.task_name]
    else:
        tasks = [task_name] if task_name else SUPERVISED_CASE_PREDICTION_TASKS
    predictions: list[CasePrediction] = []
    for next_task in tasks:
        if next_task == MlTaskName.LEGAL_ISSUE_CLASSIFIER:
            continue
        if not explicit_model and next_task == MlTaskName.CASE_TYPE:
            imported_prediction = predict_imported_case_type_for_case(db, case=case)
            if imported_prediction is not None:
                predictions.append(imported_prediction)
                continue

        model = explicit_model if explicit_model else get_latest_model_for_task(db, next_task)
        if not model or model.status != MlModelStatus.READY:
            continue
        predictions.append(predict_case(db, case=case, task_name=next_task, model=model))
    return predictions
