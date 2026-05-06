from __future__ import annotations

import json
import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.models.enums import MlDatasetStatus, MlModelFamily, MlModelStatus, MlTaskName
from app.models.ml_dataset import MlDataset
from app.models.ml_model import MlModel
from app.services.ml.registry import datasets_root, write_jsonl
from app.services.ml.training.transformer_runtime import ensure_text_only_transformers_runtime

logger = logging.getLogger(__name__)

LEGAL_AUTHORITY_WARNING = (
    "This model is experimental and trained on weak or dataset-derived labels. "
    "It is not legal advice and not legally authoritative."
)

BACKEND_DIR = PROJECT_ROOT / "backend"
TRAINED_MODELS_DIR = BACKEND_DIR / "trainedmodels"
IMPORTED_DIR = TRAINED_MODELS_DIR / "imported"
EXTRACTED_DIR = TRAINED_MODELS_DIR / "extracted"
IMPORTED_ZIP_PATH = IMPORTED_DIR / "trained_model_bundle_case_type.zip"

IMPORTED_DATASET_VERSION = "colab-imported-case-type-v1"
IMPORTED_MODEL_NAME = "Imported Colab Case Type Transformer"

CASE_TYPE_LABELS = [
    "civil",
    "criminal",
    "constitutional",
    "revenue",
    "customs",
    "service",
    "property",
    "family",
    "tax",
    "commercial",
    "unknown",
]


@dataclass(frozen=True)
class CaseTypeModelDiscovery:
    found: bool
    zip_path: Path
    extract_dir: Path
    bundle_root: Path | None
    task_dir: Path | None
    model_dir: Path | None
    tokenizer_dir: Path | None
    label_mapping_path: Path | None
    metrics_path: Path | None
    manifest_path: Path | None
    reason: str
    zip_found: bool
    extracted: bool
    model_dir_exists: bool
    tokenizer_dir_exists: bool
    label_mapping_loaded: bool
    metrics_loaded: bool
    manifest_loaded: bool
    required_files_valid: bool


@dataclass
class ImportedCaseTypeRuntime:
    discovery: CaseTypeModelDiscovery
    tokenizer: Any | None = None
    model: Any | None = None
    label_mapping: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    status: str = "demo_fallback"


_IMPORTED_CASE_TYPE_RUNTIME: ImportedCaseTypeRuntime | None = None


def _ensure_model_dirs() -> None:
    TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    IMPORTED_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _safe_extract_zip(zip_path: Path, extract_dir: Path) -> bool:
    if not zip_path.exists():
        logger.info("TRAINED_CASE_TYPE_MODEL_NOT_FOUND zip_path=%s", zip_path)
        return False

    marker = extract_dir / ".extracted"
    if marker.exists():
        return True

    try:
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            root_resolved = extract_dir.resolve()
            for member in archive.infolist():
                target = (extract_dir / member.filename).resolve()
                if root_resolved not in [target, *target.parents]:
                    raise ValueError(f"Unsafe zip member path: {member.filename}")
            archive.extractall(extract_dir)
        marker.write_text(zip_path.name, encoding="utf-8")
        logger.info("TRAINED_CASE_TYPE_MODEL_EXTRACTED path=%s", extract_dir)
        return True
    except Exception as exc:
        logger.warning("TRAINED_CASE_TYPE_MODEL_LOAD_FAILED_FALLING_BACK zip_extract_failed=%s", exc)
        return False


def _has_model_weight(model_dir: Path) -> bool:
    return any((model_dir / filename).exists() for filename in ["model.safetensors", "pytorch_model.bin", "tf_model.h5"])


def _has_tokenizer_file(tokenizer_dir: Path) -> bool:
    return any((tokenizer_dir / filename).exists() for filename in ["vocab.txt", "tokenizer.json", "spiece.model"])


def _find_manifest(task_dir: Path, bundle_root: Path) -> Path | None:
    for candidate in [
        bundle_root / "model_manifest.json",
        task_dir.parent / "model_manifest.json",
        task_dir.parent.parent / "model_manifest.json",
    ]:
        if candidate.exists():
            return candidate
    return None


def _candidate_search_roots(extract_dir: Path) -> list[Path]:
    legacy_canonical = BACKEND_DIR / "trained_models" / "imported"
    return [IMPORTED_DIR, extract_dir, legacy_canonical]


def _discover_task_dir(search_roots: list[Path]) -> tuple[Path | None, Path | None]:
    candidates: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for label_mapping in root.rglob("label_mapping.json"):
            task_dir = label_mapping.parent
            if task_dir.name != "case_type":
                continue
            candidates.append(task_dir)

    for task_dir in candidates:
        model_dir = task_dir / "model"
        tokenizer_dir = task_dir / "tokenizer"
        if (
            (task_dir / "label_mapping.json").exists()
            and (task_dir / "metrics.json").exists()
            and (model_dir / "config.json").exists()
            and model_dir.exists()
            and tokenizer_dir.exists()
        ):
            return task_dir, task_dir.parent
    return None, None


def _validate_discovery(task_dir: Path | None, bundle_root: Path | None) -> tuple[bool, str, dict[str, bool]]:
    if not task_dir or not bundle_root:
        return False, "case_type task folder not discovered", {}

    model_dir = task_dir / "model"
    tokenizer_dir = task_dir / "tokenizer"
    checks = {
        "model_dir_exists": model_dir.exists(),
        "tokenizer_dir_exists": tokenizer_dir.exists(),
        "config_exists": (model_dir / "config.json").exists(),
        "weight_exists": _has_model_weight(model_dir),
        "tokenizer_file_exists": _has_tokenizer_file(tokenizer_dir),
        "label_mapping_exists": (task_dir / "label_mapping.json").exists(),
        "metrics_exists": (task_dir / "metrics.json").exists(),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        return False, f"missing required model files: {', '.join(missing)}", checks
    return True, "trained imported model discovered and validated", checks


def discover_imported_case_type_model(reset_cache: bool = False) -> CaseTypeModelDiscovery:
    if reset_cache:
        reset_imported_case_type_runtime()

    _ensure_model_dirs()
    zip_found = IMPORTED_ZIP_PATH.exists()
    if zip_found:
        logger.info("TRAINED_CASE_TYPE_MODEL_ZIP_FOUND path=%s", IMPORTED_ZIP_PATH)

    extract_dir = EXTRACTED_DIR / IMPORTED_ZIP_PATH.stem
    extracted = _safe_extract_zip(IMPORTED_ZIP_PATH, extract_dir) if zip_found else False
    task_dir, bundle_root = _discover_task_dir(_candidate_search_roots(extract_dir))
    valid, reason, checks = _validate_discovery(task_dir, bundle_root)

    model_dir = task_dir / "model" if task_dir else None
    tokenizer_dir = task_dir / "tokenizer" if task_dir else None
    label_mapping_path = task_dir / "label_mapping.json" if task_dir else None
    metrics_path = task_dir / "metrics.json" if task_dir else None
    manifest_path = _find_manifest(task_dir, bundle_root) if task_dir and bundle_root else None

    manifest = _read_json(manifest_path)
    metrics = _read_json(metrics_path)
    label_mapping = _read_json(label_mapping_path)

    discovery = CaseTypeModelDiscovery(
        found=valid,
        zip_path=IMPORTED_ZIP_PATH,
        extract_dir=extract_dir,
        bundle_root=bundle_root,
        task_dir=task_dir,
        model_dir=model_dir,
        tokenizer_dir=tokenizer_dir,
        label_mapping_path=label_mapping_path,
        metrics_path=metrics_path,
        manifest_path=manifest_path,
        reason=reason,
        zip_found=zip_found,
        extracted=extracted,
        model_dir_exists=bool(checks.get("model_dir_exists")),
        tokenizer_dir_exists=bool(checks.get("tokenizer_dir_exists")),
        label_mapping_loaded=bool(label_mapping),
        metrics_loaded=bool(metrics),
        manifest_loaded=bool(manifest),
        required_files_valid=valid,
    )

    if valid:
        logger.info("TRAINED_CASE_TYPE_MODEL_DISCOVERED path=%s", task_dir)
        logger.info("TRAINED_CASE_TYPE_MODEL_VALIDATED path=%s", task_dir)
    elif zip_found:
        logger.warning("TRAINED_CASE_TYPE_MODEL_INVALID reason=%s", reason)
    else:
        logger.info("TRAINED_CASE_TYPE_MODEL_NOT_FOUND")
    return discovery


def reset_imported_case_type_runtime() -> None:
    global _IMPORTED_CASE_TYPE_RUNTIME
    _IMPORTED_CASE_TYPE_RUNTIME = None


def _load_imported_case_type_runtime() -> ImportedCaseTypeRuntime:
    global _IMPORTED_CASE_TYPE_RUNTIME
    if _IMPORTED_CASE_TYPE_RUNTIME and _IMPORTED_CASE_TYPE_RUNTIME.model is not None:
        return _IMPORTED_CASE_TYPE_RUNTIME

    discovery = discover_imported_case_type_model()
    manifest = _read_json(discovery.manifest_path)
    metrics = _read_json(discovery.metrics_path)
    label_mapping = _read_json(discovery.label_mapping_path)

    if not discovery.found or not discovery.model_dir or not discovery.tokenizer_dir:
        return ImportedCaseTypeRuntime(
            discovery=discovery,
            label_mapping=label_mapping,
            manifest=manifest,
            metrics=metrics,
            status="trained_imported_invalid" if discovery.zip_found else "trained_imported_not_found",
        )

    try:
        ensure_text_only_transformers_runtime()
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(str(discovery.tokenizer_dir))
        model = AutoModelForSequenceClassification.from_pretrained(str(discovery.model_dir))
        model.eval()
        _IMPORTED_CASE_TYPE_RUNTIME = ImportedCaseTypeRuntime(
            discovery=discovery,
            tokenizer=tokenizer,
            model=model,
            label_mapping=label_mapping,
            manifest=manifest,
            metrics=metrics,
            status="trained_imported_loaded",
        )
        logger.info("TRAINED_CASE_TYPE_MODEL_LOADED path=%s", discovery.task_dir)
        return _IMPORTED_CASE_TYPE_RUNTIME
    except Exception as exc:
        logger.warning("TRAINED_CASE_TYPE_MODEL_LOAD_FAILED_FALLING_BACK error=%s", exc)
        return ImportedCaseTypeRuntime(
            discovery=discovery,
            label_mapping=label_mapping,
            manifest=manifest,
            metrics=metrics,
            status="trained_imported_load_failed",
        )


def _compact_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    dataset = manifest.get("dataset") if isinstance(manifest.get("dataset"), dict) else {}
    return {
        "task": manifest.get("task"),
        "baseModel": manifest.get("base_model"),
        "createdAtUtc": manifest.get("created_at_utc"),
        "dataset": {
            "sourceDataset": dataset.get("source_dataset"),
            "splits": dataset.get("splits"),
            "labels": dataset.get("labels"),
        },
    }


def _compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    validation = metrics.get("validation") if isinstance(metrics.get("validation"), dict) else {}
    test = metrics.get("test") if isinstance(metrics.get("test"), dict) else {}
    return {
        "labels": metrics.get("labels"),
        "validation": {
            "accuracy": validation.get("eval_accuracy"),
            "macroF1": validation.get("eval_f1_macro"),
            "weightedF1": validation.get("eval_f1_weighted"),
        },
        "test": {
            "accuracy": test.get("eval_accuracy"),
            "macroF1": test.get("eval_f1_macro"),
            "weightedF1": test.get("eval_f1_weighted"),
        },
    }


def get_case_type_model_health() -> dict[str, Any]:
    discovery = discover_imported_case_type_model()
    cached_loaded = _IMPORTED_CASE_TYPE_RUNTIME is not None and _IMPORTED_CASE_TYPE_RUNTIME.model is not None
    status = "trained_imported_loaded" if cached_loaded else (
        "trained_imported_loaded" if discovery.found else ("trained_imported_invalid" if discovery.zip_found else "trained_imported_not_found")
    )
    return {
        "task": "case_type",
        "available": discovery.found,
        "model_source": "trained_imported" if discovery.found else "demo_fallback",
        "model_status": status if discovery.found else "demo_fallback",
        "zip_found": discovery.zip_found,
        "extracted": discovery.extracted,
        "bundle_root": str(discovery.bundle_root or ""),
        "model_dir_exists": discovery.model_dir_exists,
        "tokenizer_dir_exists": discovery.tokenizer_dir_exists,
        "label_mapping_loaded": discovery.label_mapping_loaded,
        "metrics_loaded": discovery.metrics_loaded,
        "manifest_loaded": discovery.manifest_loaded,
        "required_files_valid": discovery.required_files_valid,
        "reason": discovery.reason,
        "legal_authority_warning": LEGAL_AUTHORITY_WARNING,
    }


def _imported_label_schema(discovery: CaseTypeModelDiscovery) -> list[str]:
    metrics = _read_json(discovery.metrics_path)
    labels = metrics.get("labels")
    if isinstance(labels, list) and all(isinstance(label, str) for label in labels):
        return labels
    mapping = _read_json(discovery.label_mapping_path).get("id2label", {}) if discovery.label_mapping_path else {}
    if isinstance(mapping, dict):
        return [str(mapping[key]) for key in sorted(mapping, key=lambda item: int(item))]
    return []


def _imported_primary_metric(discovery: CaseTypeModelDiscovery) -> float:
    metrics = _read_json(discovery.metrics_path)
    test_metrics = metrics.get("test", {})
    if isinstance(test_metrics, dict):
        for key in ["eval_f1_macro", "eval_accuracy", "eval_f1_weighted"]:
            if isinstance(test_metrics.get(key), int | float):
                return float(test_metrics[key])
    validation_metrics = metrics.get("validation", {})
    if isinstance(validation_metrics, dict):
        for key in ["eval_f1_macro", "eval_accuracy", "eval_f1_weighted"]:
            if isinstance(validation_metrics.get(key), int | float):
                return float(validation_metrics[key])
    return 0.0


def _write_imported_reference_dataset(discovery: CaseTypeModelDiscovery, label_schema: list[str]) -> Path:
    manifest = _read_json(discovery.manifest_path)
    manifest_dataset = manifest.get("dataset", {}) if isinstance(manifest.get("dataset"), dict) else {}
    split_counts = manifest_dataset.get("splits", {}) if isinstance(manifest_dataset.get("splits"), dict) else {}
    rows: list[dict[str, Any]] = []
    labels = label_schema or ["unknown"]
    for split, count in split_counts.items():
        if split not in {"train", "validation", "test"}:
            continue
        for index in range(max(int(count), 1)):
            label = labels[index % len(labels)]
            rows.append(
                {
                    "id": f"imported-colab-case-type:{split}:{index}",
                    "case_id": f"imported-colab-case-type:{split}:{index}",
                    "task_name": MlTaskName.CASE_TYPE.value,
                    "label": label,
                    "label_source": "imported_colab_manifest",
                    "label_confidence": 0.75,
                    "split": split,
                    "language": "English",
                    "source_view": "imported_model_reference",
                    "text": (
                        "Reference row for the imported Colab case_type model. "
                        "Use the original Tier 1 export or Colab dataset for retraining."
                    ),
                    "normalized_text": (
                        "reference row for imported colab case_type model "
                        "use original tier 1 export or colab dataset for retraining"
                    ),
                    "structured_features": {
                        "source_quality": "imported_model_reference",
                        "is_external_model_registry_row": True,
                    },
                }
            )
    if not rows:
        rows = [
            {
                "id": f"imported-colab-case-type:{index}",
                "case_id": f"imported-colab-case-type:{index}",
                "task_name": MlTaskName.CASE_TYPE.value,
                "label": label,
                "label_source": "imported_colab_manifest",
                "label_confidence": 0.75,
                "split": "train" if index == 0 else "test",
                "language": "English",
                "source_view": "imported_model_reference",
                "text": "Reference row for the imported Colab case_type model.",
                "normalized_text": "reference row for imported colab case_type model",
                "structured_features": {"is_external_model_registry_row": True},
            }
            for index, label in enumerate(labels)
        ]
    path = datasets_root() / "imported_case_type_colab_reference" / "records.jsonl"
    write_jsonl(path, rows)
    return path


def ensure_imported_case_type_model_record(db: Session) -> MlModel | None:
    discovery = discover_imported_case_type_model()
    if not discovery.found or not discovery.task_dir:
        return None

    dataset = db.scalar(
        select(MlDataset).where(
            MlDataset.task_name == MlTaskName.CASE_TYPE,
            MlDataset.version == IMPORTED_DATASET_VERSION,
        )
    )
    manifest = _read_json(discovery.manifest_path)
    metrics = _read_json(discovery.metrics_path)
    manifest_dataset = manifest.get("dataset", {}) if isinstance(manifest.get("dataset"), dict) else {}
    split_counts = manifest_dataset.get("splits", {}) if isinstance(manifest_dataset.get("splits"), dict) else {}
    record_count = sum(int(value) for value in split_counts.values() if isinstance(value, int | float))
    label_schema = _imported_label_schema(discovery)
    reference_dataset_path = _write_imported_reference_dataset(discovery, label_schema)

    if not dataset:
        dataset = MlDataset(
            task_name=MlTaskName.CASE_TYPE,
            name="Imported Colab Case Type Dataset",
            version=IMPORTED_DATASET_VERSION,
            status=MlDatasetStatus.READY,
            record_count=record_count,
            label_strategy="Imported Colab model labels; dataset-derived and not legally authoritative.",
            split_strategy="Imported train/validation/test split from Colab manifest.",
            data_path=str(reference_dataset_path),
            report_path=str(discovery.metrics_path or ""),
            report_json={
                "labels": label_schema,
                "splits": split_counts,
                "sourceDataset": manifest_dataset.get("source_dataset", ""),
            },
            notes="Read-only registry row for an externally trained case_type model.",
            metadata_json={
                "importedCaseTypeDataset": True,
                "source": "colab_trained_bundle",
                "manifest": manifest,
            },
        )
        db.add(dataset)
        db.flush()
    else:
        dataset.data_path = str(reference_dataset_path)
        dataset.record_count = record_count or dataset.record_count
        dataset.report_json = {
            **(dataset.report_json or {}),
            "labels": label_schema,
            "splits": split_counts,
            "sourceDataset": manifest_dataset.get("source_dataset", ""),
        }
        db.add(dataset)
        db.flush()

    existing_model = db.scalar(
        select(MlModel).where(
            MlModel.task_name == MlTaskName.CASE_TYPE,
            MlModel.name == IMPORTED_MODEL_NAME,
        )
    )
    if existing_model:
        existing_model.dataset_id = dataset.id
        existing_model.artifact_path = str(discovery.model_dir or "")
        existing_model.metrics_path = str(discovery.metrics_path or "")
        existing_model.metrics_json = {
            **metrics,
            "primaryMetric": round(_imported_primary_metric(discovery), 4),
        }
        existing_model.label_schema = label_schema
        existing_model.config_json = {
            **(existing_model.config_json or {}),
            "modelSource": "trained_imported",
            "modelStatus": "trained_imported_loaded",
            "legalAuthorityWarning": LEGAL_AUTHORITY_WARNING,
        }
        existing_model.metadata_json = {
            **(existing_model.metadata_json or {}),
            "importedCaseTypeModel": True,
            "modelSource": "trained_imported",
            "manifestPath": str(discovery.manifest_path or ""),
            "caseTypeDir": str(discovery.task_dir),
            "legalAuthorityWarning": LEGAL_AUTHORITY_WARNING,
        }
        db.add(existing_model)
        db.commit()
        db.refresh(existing_model)
        return existing_model

    model = MlModel(
        dataset_id=dataset.id,
        task_name=MlTaskName.CASE_TYPE,
        model_family=MlModelFamily.TRANSFORMER,
        name=IMPORTED_MODEL_NAME,
        status=MlModelStatus.READY,
        artifact_path=str(discovery.model_dir or ""),
        metrics_path=str(discovery.metrics_path or ""),
        metrics_json={
            **metrics,
            "primaryMetric": round(_imported_primary_metric(discovery), 4),
        },
        config_json={
            "modelSource": "trained_imported",
            "modelStatus": "trained_imported_loaded",
            "legalAuthorityWarning": LEGAL_AUTHORITY_WARNING,
        },
        label_schema=label_schema,
        training_summary=(
            "Imported Colab-trained DistilBERT multilingual case_type classifier. "
            "Experimental and not legally authoritative."
        ),
        metadata_json={
            "importedCaseTypeModel": True,
            "modelSource": "trained_imported",
            "manifestPath": str(discovery.manifest_path or ""),
            "caseTypeDir": str(discovery.task_dir),
            "legalAuthorityWarning": LEGAL_AUTHORITY_WARNING,
        },
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def _fallback_case_type_prediction(text: str, status: str = "demo_fallback") -> dict[str, Any]:
    logger.info("CASE_TYPE_DEMO_FALLBACK_USED status=%s", status)
    normalized = text.lower()
    scores = {label: 0.02 for label in CASE_TYPE_LABELS}
    keyword_map = {
        "constitutional": ["article 199", "writ", "constitutional petition", "fundamental right"],
        "criminal": ["fir", "bail", "crpc", "criminal", "conviction", "sentence"],
        "civil": ["cpc", "civil suit", "plaint", "decree", "declaration", "injunction"],
        "family": ["khula", "maintenance", "guardian", "custody", "family"],
        "tax": ["income tax", "sales tax", "tax", "customs", "assessment"],
        "service": ["service", "employee", "department", "tribunal", "promotion"],
        "property": ["property", "possession", "sale deed", "specific performance"],
        "revenue": ["mutation", "revenue", "land record", "patwari"],
        "customs": ["customs", "seizure", "fbr", "import duty"],
        "commercial": ["company", "contract", "commercial", "arbitration"],
    }
    for label, keywords in keyword_map.items():
        scores[label] += sum(0.2 for keyword in keywords if keyword in normalized)
    if max(scores.values()) <= 0.02:
        scores["unknown"] = 0.6
    total = sum(scores.values()) or 1.0
    probabilities = {
        label: round(score / total, 4)
        for label, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    }
    predicted_label = next(iter(probabilities))
    return {
        "task": "case_type",
        "predicted_label": predicted_label,
        "confidence": probabilities[predicted_label],
        "probabilities": probabilities,
        "model_source": "demo_fallback",
        "model_status": status if status != "trained_imported_loaded" else "demo_fallback",
        "model_name": "Demo heuristic case type classifier",
        "bundle_manifest": {},
        "metrics": {},
        "legal_authority_warning": LEGAL_AUTHORITY_WARNING,
    }


def _max_length_from_manifest(manifest: dict[str, Any]) -> int:
    training = manifest.get("training") if isinstance(manifest.get("training"), dict) else {}
    value = training.get("max_length")
    if isinstance(value, int) and 32 <= value <= 1024:
        return value
    return 384


def predict_case_type_text(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return _fallback_case_type_prediction("", status="demo_fallback")

    runtime = _load_imported_case_type_runtime()
    if runtime.model is None or runtime.tokenizer is None:
        return _fallback_case_type_prediction(text, status=runtime.status)

    try:
        import torch

        encoded = runtime.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=_max_length_from_manifest(runtime.manifest or {}),
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = runtime.model(**encoded).logits
            probabilities_tensor = torch.softmax(logits, dim=1).squeeze(0)
        id2label = (runtime.label_mapping or {}).get("id2label") or getattr(runtime.model.config, "id2label", {})
        labels = [str(id2label.get(str(index), id2label.get(index, index))) for index in range(len(probabilities_tensor))]
        paired = sorted(
            zip(labels, probabilities_tensor.tolist(), strict=False),
            key=lambda item: item[1],
            reverse=True,
        )
        probabilities = {label: round(float(score), 4) for label, score in paired}
        predicted_label, confidence = paired[0]
        return {
            "task": "case_type",
            "predicted_label": predicted_label,
            "confidence": round(float(confidence), 4),
            "probabilities": probabilities,
            "model_source": "trained_imported",
            "model_status": runtime.status,
            "model_name": IMPORTED_MODEL_NAME,
            "bundle_manifest": _compact_manifest(runtime.manifest or {}),
            "metrics": _compact_metrics(runtime.metrics or {}),
            "legal_authority_warning": LEGAL_AUTHORITY_WARNING,
        }
    except Exception as exc:
        logger.warning("TRAINED_CASE_TYPE_MODEL_LOAD_FAILED_FALLING_BACK inference_error=%s", exc)
        return _fallback_case_type_prediction(text, status="trained_imported_load_failed")
