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
from app.services.ml.training.imported_case_type import LEGAL_AUTHORITY_WARNING
from app.services.ml.training.transformer_runtime import ensure_text_only_transformers_runtime

logger = logging.getLogger(__name__)

BACKEND_DIR = PROJECT_ROOT / "backend"
TRAINED_MODELS_DIR = BACKEND_DIR / "trainedmodels"
IMPORTED_DIR = TRAINED_MODELS_DIR / "imported"
EXTRACTED_DIR = TRAINED_MODELS_DIR / "extracted"
IMPORTED_ZIP_PATH = IMPORTED_DIR / "trained_model_bundle_legal_issue_classifier_xlmr_pk_kaggle_10_epoch.zip"

TASK_DIR_NAME = "legal_issue_classifier"
IMPORTED_DATASET_VERSION = "kaggle-imported-legal-issue-xlmr-v1"
IMPORTED_MODEL_NAME = "Imported XLM-R Legal Issue Classifier"

FALLBACK_ISSUE_RULES: dict[str, list[str]] = {
    "constitutional_petition": [
        "article 199",
        "writ",
        "constitutional petition",
        "fundamental rights",
        "public authority",
    ],
    "maintainability": [
        "maintainability",
        "maintainable",
        "not maintainable",
        "preliminary objection",
        "barred",
        "locus standi",
    ],
    "alternate_remedy": [
        "alternate remedy",
        "alternative remedy",
        "statutory remedy",
        "departmental appeal",
        "efficacious remedy",
    ],
    "limitation": [
        "limitation",
        "time barred",
        "barred by time",
        "delay",
        "laches",
        "article 120",
        "limitation act",
    ],
    "jurisdiction": [
        "jurisdiction",
        "territorial jurisdiction",
        "pecuniary jurisdiction",
        "coram non judice",
        "forum",
    ],
    "injunction": [
        "injunction",
        "stay order",
        "restraining order",
        "temporary injunction",
        "order xxxix",
        "prima facie",
        "balance of convenience",
    ],
    "property_dispute": [
        "property",
        "land",
        "allotment",
        "possession",
        "title",
        "mutation",
        "sale deed",
        "transfer",
        "specific performance",
    ],
    "contract_breach": ["contract", "agreement", "breach", "damages", "specific performance", "consideration"],
    "criminal_bail": ["bail", "fir", "arrest", "accused", "offence", "crpc", "section 497", "challan"],
    "criminal_appeal": ["conviction", "sentence", "appeal against conviction", "acquittal", "prosecution"],
    "service_matter": [
        "service tribunal",
        "employee",
        "appointment",
        "promotion",
        "dismissal from service",
        "department",
    ],
    "tax_customs": ["income tax", "sales tax", "customs", "fbr", "tax", "duty"],
    "family_matter": ["khula", "maintenance", "custody", "guardian", "dissolution of marriage", "family court"],
    "evidence_issue": ["evidence", "witness", "cross examination", "qanun-e-shahadat", "admissibility", "exhibit"],
    "pre_emption": ["pre-emption", "shufa", "talb-i-ishhad", "talb-i-muwathibat", "vendee", "pre-emptor"],
    "natural_justice": ["notice", "opportunity of hearing", "audi alteram partem", "natural justice", "without hearing"],
    "administrative_law": ["administrative order", "authority", "department", "public functionary", "notification"],
    "civil_revision": ["civil revision", "revisional jurisdiction", "section 115 cpc"],
    "execution": ["execution", "decree holder", "judgment debtor", "executing court"],
}


@dataclass(frozen=True)
class LegalIssueModelDiscovery:
    found: bool
    task: str
    zip_path: Path
    extract_dir: Path
    bundle_root: Path | None
    task_dir: Path | None
    model_dir: Path | None
    tokenizer_dir: Path | None
    label_mapping_path: Path | None
    metrics_path: Path | None
    threshold_config_path: Path | None
    manifest_path: Path | None
    reason: str
    zip_found: bool
    extracted: bool
    model_dir_exists: bool
    tokenizer_dir_exists: bool
    label_mapping_loaded: bool
    threshold_config_loaded: bool
    metrics_loaded: bool
    manifest_loaded: bool
    required_files_valid: bool
    labels_count: int


@dataclass
class ImportedLegalIssueRuntime:
    discovery: LegalIssueModelDiscovery
    tokenizer: Any | None = None
    model: Any | None = None
    labels: list[str] | None = None
    label_mapping: dict[str, Any] | None = None
    thresholds: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    status: str = "demo_fallback"


_IMPORTED_LEGAL_ISSUE_RUNTIME: ImportedLegalIssueRuntime | None = None


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
        logger.info("TRAINED_LEGAL_ISSUE_MODEL_NOT_FOUND zip_path=%s", zip_path)
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
        logger.info("TRAINED_LEGAL_ISSUE_MODEL_EXTRACTED path=%s", extract_dir)
        return True
    except Exception as exc:
        logger.warning("TRAINED_LEGAL_ISSUE_MODEL_LOAD_FAILED_FALLING_BACK zip_extract_failed=%s", exc)
        return False


def _has_model_weight(model_dir: Path) -> bool:
    return any((model_dir / filename).exists() for filename in ["model.safetensors", "pytorch_model.bin", "tf_model.h5"])


def _has_tokenizer_file(tokenizer_dir: Path) -> bool:
    tokenizers = ["sentencepiece.bpe.model", "tokenizer.json", "spiece.model", "tokenizer_config.json"]
    if any((tokenizer_dir / filename).exists() for filename in tokenizers):
        return True
    return (tokenizer_dir / "vocab.json").exists() and (tokenizer_dir / "merges.txt").exists()


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
    legacy_imported = BACKEND_DIR / "trained_models" / "imported"
    return [extract_dir, IMPORTED_DIR, legacy_imported]


def _discover_task_dir(search_roots: list[Path]) -> tuple[Path | None, Path | None]:
    candidates: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for label_mapping in root.rglob("label_mapping.json"):
            task_dir = label_mapping.parent
            if task_dir.name == TASK_DIR_NAME:
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


def _parse_label_mapping(payload: dict[str, Any], model_config: Any | None = None) -> tuple[list[str], dict[str, int], dict[int, str]]:
    labels: list[str] = []
    if isinstance(payload.get("labels"), list):
        labels = [str(label) for label in payload["labels"]]
    elif isinstance(payload.get("issue_labels"), list):
        labels = [str(label) for label in payload["issue_labels"]]
    elif isinstance(payload.get("id2label"), dict):
        id2label = payload["id2label"]
        try:
            labels = [str(id2label[str(index)] if str(index) in id2label else id2label[index]) for index in sorted(int(key) for key in id2label)]
        except Exception:
            labels = [str(value) for _, value in sorted(id2label.items(), key=lambda item: str(item[0]))]
    elif isinstance(payload.get("label2id"), dict):
        label2id = payload["label2id"]
        labels = [str(label) for label, _ in sorted(label2id.items(), key=lambda item: int(item[1]))]

    if not labels and model_config is not None:
        raw_id2label = getattr(model_config, "id2label", {}) or {}
        if isinstance(raw_id2label, dict) and raw_id2label:
            labels = [str(raw_id2label[index]) for index in sorted(raw_id2label)]

    labels = [label for label in labels if label]
    label2id = {label: index for index, label in enumerate(labels)}
    id2label = {index: label for label, index in label2id.items()}
    return labels, label2id, id2label


def _parse_thresholds(payload: dict[str, Any]) -> dict[str, Any]:
    default_threshold = 0.5
    if isinstance(payload.get("default_threshold"), int | float):
        default_threshold = float(payload["default_threshold"])
    elif isinstance(payload.get("threshold"), int | float):
        default_threshold = float(payload["threshold"])

    raw_thresholds = payload.get("per_label_thresholds")
    if not isinstance(raw_thresholds, dict):
        raw_thresholds = payload.get("thresholds")
    per_label_thresholds = {
        str(label): max(0.0, min(1.0, float(value)))
        for label, value in (raw_thresholds or {}).items()
        if isinstance(value, int | float)
    }
    return {
        "default_threshold": max(0.0, min(1.0, default_threshold)),
        "per_label_thresholds": per_label_thresholds,
    }


def _validate_discovery(task_dir: Path | None, bundle_root: Path | None) -> tuple[bool, str, dict[str, bool], int]:
    if not task_dir or not bundle_root:
        return False, "legal_issue_classifier task folder not discovered", {}, 0

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
    labels, _, _ = _parse_label_mapping(_read_json(task_dir / "label_mapping.json"))
    if not labels:
        missing.append("parseable_label_mapping")
    if missing:
        return False, f"missing required model files: {', '.join(missing)}", checks, len(labels)
    return True, "trained imported legal issue model discovered and validated", checks, len(labels)


def discover_imported_legal_issue_model(reset_cache: bool = False) -> LegalIssueModelDiscovery:
    if reset_cache:
        reset_imported_legal_issue_runtime()

    _ensure_model_dirs()
    zip_found = IMPORTED_ZIP_PATH.exists()
    if zip_found:
        logger.info("TRAINED_LEGAL_ISSUE_MODEL_ZIP_FOUND path=%s", IMPORTED_ZIP_PATH)

    extract_dir = EXTRACTED_DIR / IMPORTED_ZIP_PATH.stem
    extracted = _safe_extract_zip(IMPORTED_ZIP_PATH, extract_dir) if zip_found else False
    task_dir, bundle_root = _discover_task_dir(_candidate_search_roots(extract_dir))
    valid, reason, checks, labels_count = _validate_discovery(task_dir, bundle_root)

    model_dir = task_dir / "model" if task_dir else None
    tokenizer_dir = task_dir / "tokenizer" if task_dir else None
    label_mapping_path = task_dir / "label_mapping.json" if task_dir else None
    metrics_path = task_dir / "metrics.json" if task_dir else None
    threshold_config_path = task_dir / "threshold_config.json" if task_dir and (task_dir / "threshold_config.json").exists() else None
    manifest_path = _find_manifest(task_dir, bundle_root) if task_dir and bundle_root else None

    discovery = LegalIssueModelDiscovery(
        found=valid,
        task=TASK_DIR_NAME,
        zip_path=IMPORTED_ZIP_PATH,
        extract_dir=extract_dir,
        bundle_root=bundle_root,
        task_dir=task_dir,
        model_dir=model_dir,
        tokenizer_dir=tokenizer_dir,
        label_mapping_path=label_mapping_path,
        metrics_path=metrics_path,
        threshold_config_path=threshold_config_path,
        manifest_path=manifest_path,
        reason=reason,
        zip_found=zip_found,
        extracted=extracted,
        model_dir_exists=bool(checks.get("model_dir_exists")),
        tokenizer_dir_exists=bool(checks.get("tokenizer_dir_exists")),
        label_mapping_loaded=bool(_read_json(label_mapping_path)),
        threshold_config_loaded=bool(_read_json(threshold_config_path)),
        metrics_loaded=bool(_read_json(metrics_path)),
        manifest_loaded=bool(_read_json(manifest_path)),
        required_files_valid=valid,
        labels_count=labels_count,
    )

    if valid:
        logger.info("TRAINED_LEGAL_ISSUE_MODEL_DISCOVERED path=%s", task_dir)
        logger.info("TRAINED_LEGAL_ISSUE_MODEL_VALIDATED path=%s", task_dir)
    elif zip_found:
        logger.warning("TRAINED_LEGAL_ISSUE_MODEL_INVALID reason=%s", reason)
    else:
        logger.info("TRAINED_LEGAL_ISSUE_MODEL_NOT_FOUND")
    return discovery


def reset_imported_legal_issue_runtime() -> None:
    global _IMPORTED_LEGAL_ISSUE_RUNTIME
    _IMPORTED_LEGAL_ISSUE_RUNTIME = None


def _load_imported_legal_issue_runtime() -> ImportedLegalIssueRuntime:
    global _IMPORTED_LEGAL_ISSUE_RUNTIME
    if _IMPORTED_LEGAL_ISSUE_RUNTIME and _IMPORTED_LEGAL_ISSUE_RUNTIME.model is not None:
        return _IMPORTED_LEGAL_ISSUE_RUNTIME

    discovery = discover_imported_legal_issue_model()
    manifest = _read_json(discovery.manifest_path)
    metrics = _read_json(discovery.metrics_path)
    label_mapping = _read_json(discovery.label_mapping_path)
    thresholds = _parse_thresholds(_read_json(discovery.threshold_config_path))
    labels, label2id, id2label = _parse_label_mapping(label_mapping)
    normalized_label_mapping = {"labels": labels, "label2id": label2id, "id2label": id2label}

    if not discovery.found or not discovery.model_dir or not discovery.tokenizer_dir or not labels:
        return ImportedLegalIssueRuntime(
            discovery=discovery,
            labels=labels,
            label_mapping=normalized_label_mapping,
            thresholds=thresholds,
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
        labels, label2id, id2label = _parse_label_mapping(label_mapping, model.config)
        if not labels:
            raise ValueError("Unable to parse legal issue label mapping.")
        _IMPORTED_LEGAL_ISSUE_RUNTIME = ImportedLegalIssueRuntime(
            discovery=discovery,
            tokenizer=tokenizer,
            model=model,
            labels=labels,
            label_mapping={"labels": labels, "label2id": label2id, "id2label": id2label},
            thresholds=thresholds,
            manifest=manifest,
            metrics=metrics,
            status="trained_imported_loaded",
        )
        logger.info("TRAINED_LEGAL_ISSUE_MODEL_LOADED path=%s", discovery.task_dir)
        return _IMPORTED_LEGAL_ISSUE_RUNTIME
    except Exception as exc:
        logger.warning("TRAINED_LEGAL_ISSUE_MODEL_LOAD_FAILED_FALLING_BACK error=%s", exc)
        return ImportedLegalIssueRuntime(
            discovery=discovery,
            labels=labels,
            label_mapping=normalized_label_mapping,
            thresholds=thresholds,
            manifest=manifest,
            metrics=metrics,
            status="trained_imported_load_failed",
        )


def _compact_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    dataset = manifest.get("dataset") if isinstance(manifest.get("dataset"), dict) else {}
    training = manifest.get("training") if isinstance(manifest.get("training"), dict) else {}
    return {
        "task": manifest.get("task") or TASK_DIR_NAME,
        "baseModel": manifest.get("base_model") or manifest.get("baseModel"),
        "createdAtUtc": manifest.get("created_at_utc") or manifest.get("createdAtUtc"),
        "dataset": {
            "sourceDataset": dataset.get("source_dataset") or dataset.get("sourceDataset"),
            "splits": dataset.get("splits"),
            "labels": dataset.get("labels"),
        },
        "training": {
            "maxLength": training.get("max_length") or training.get("maxLength"),
            "epochs": training.get("epochs") or training.get("num_train_epochs"),
        },
    }


def _compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    validation = metrics.get("validation") if isinstance(metrics.get("validation"), dict) else {}
    test = metrics.get("test") if isinstance(metrics.get("test"), dict) else {}
    if not validation:
        validation = metrics.get("validation_default_threshold_0_5", {}) if isinstance(metrics.get("validation_default_threshold_0_5"), dict) else {}
    if not test:
        test = metrics.get("test_tuned_threshold", {}) if isinstance(metrics.get("test_tuned_threshold"), dict) else {}
    if not test:
        test = metrics.get("test_default_threshold_0_5", {}) if isinstance(metrics.get("test_default_threshold_0_5"), dict) else {}
    return {
        "labels": metrics.get("labels"),
        "validation": {
            "microF1": validation.get("eval_micro_f1") or validation.get("eval_f1_micro") or validation.get("micro_f1"),
            "macroF1": validation.get("eval_macro_f1") or validation.get("eval_f1_macro") or validation.get("macro_f1"),
            "subsetAccuracy": validation.get("eval_subset_accuracy") or validation.get("subset_accuracy"),
        },
        "test": {
            "microF1": test.get("eval_micro_f1") or test.get("eval_f1_micro") or test.get("micro_f1"),
            "macroF1": test.get("eval_macro_f1") or test.get("eval_f1_macro") or test.get("macro_f1"),
            "subsetAccuracy": test.get("eval_subset_accuracy") or test.get("subset_accuracy"),
        },
    }


def _max_length_from_manifest(manifest: dict[str, Any]) -> int:
    training = manifest.get("training") if isinstance(manifest.get("training"), dict) else {}
    for key in ["max_length", "maxLength"]:
        value = training.get(key)
        if isinstance(value, int) and 32 <= value <= 1024:
            return value
    return 384


def _threshold_for_label(label: str, thresholds: dict[str, Any], override: float | None) -> float:
    if override is not None:
        return max(0.0, min(1.0, float(override)))
    per_label = thresholds.get("per_label_thresholds", {}) if isinstance(thresholds, dict) else {}
    if isinstance(per_label, dict) and isinstance(per_label.get(label), int | float):
        return max(0.0, min(1.0, float(per_label[label])))
    default = thresholds.get("default_threshold", 0.5) if isinstance(thresholds, dict) else 0.5
    return max(0.0, min(1.0, float(default)))


def _issue_items(probabilities: dict[str, float], thresholds: dict[str, Any], threshold: float | None) -> list[dict[str, Any]]:
    return [
        {
            "label": label,
            "probability": round(float(probability), 4),
            "threshold": round(_threshold_for_label(label, thresholds, threshold), 4),
        }
        for label, probability in sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    ]


def _fallback_legal_issue_prediction(
    text: str,
    *,
    status: str = "demo_fallback",
    top_k: int | None = 10,
    threshold: float | None = None,
) -> dict[str, Any]:
    logger.info("LEGAL_ISSUE_DEMO_FALLBACK_USED status=%s", status)
    normalized = text.lower()
    scores: dict[str, float] = {}
    for label, keywords in FALLBACK_ISSUE_RULES.items():
        matches = sum(1 for keyword in keywords if keyword in normalized)
        scores[label] = min(0.95, 0.08 + (matches * 0.18))
    thresholds = {"default_threshold": 0.5, "per_label_thresholds": {}}
    items = _issue_items(scores, thresholds, threshold)
    if top_k is not None:
        items = items[: max(1, top_k)]
    selected = [item for item in items if item["probability"] >= item["threshold"]]
    return {
        "task": TASK_DIR_NAME,
        "selected_issues": selected,
        "top_issues": items,
        "probabilities": {item["label"]: item["probability"] for item in items},
        "model_source": "demo_fallback",
        "model_status": status if status != "trained_imported_loaded" else "demo_fallback",
        "threshold_used": round(_threshold_for_label("", thresholds, threshold), 4),
        "model_name": "Demo rule-based legal issue detector",
        "metadata": {
            "modelSource": "demo_fallback",
            "modelStatus": status,
            "thresholdConfigLoaded": False,
            "labelsCount": len(FALLBACK_ISSUE_RULES),
        },
        "legal_authority_warning": LEGAL_AUTHORITY_WARNING,
    }


def predict_legal_issues(
    text: str,
    *,
    top_k: int | None = 10,
    threshold: float | None = None,
    include_probabilities: bool = True,
    include_metadata: bool = True,
) -> dict[str, Any]:
    if not text or not text.strip():
        return _fallback_legal_issue_prediction("", status="demo_fallback", top_k=top_k, threshold=threshold)

    runtime = _load_imported_legal_issue_runtime()
    if runtime.model is None or runtime.tokenizer is None or not runtime.labels:
        result = _fallback_legal_issue_prediction(text, status=runtime.status, top_k=top_k, threshold=threshold)
        if not include_probabilities:
            result["probabilities"] = {}
        if not include_metadata:
            result["metadata"] = {}
        return result

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
            logits = runtime.model(**encoded).logits.squeeze(0)
            probabilities_tensor = torch.sigmoid(logits)

        values = probabilities_tensor.tolist()
        labels = list(runtime.labels)
        if len(values) != len(labels):
            raise ValueError(f"Label/logit mismatch: {len(labels)} labels for {len(values)} logits.")

        probabilities = {
            label: round(float(score), 4)
            for label, score in sorted(zip(labels, values, strict=False), key=lambda item: item[1], reverse=True)
        }
        thresholds = runtime.thresholds or {"default_threshold": 0.5, "per_label_thresholds": {}}
        all_items = _issue_items(probabilities, thresholds, threshold)
        selected_issues = [item for item in all_items if item["probability"] >= item["threshold"]]
        top_issues = all_items[: max(1, top_k)] if top_k is not None else all_items
        default_threshold = _threshold_for_label("", thresholds, threshold)
        metadata = {
            "modelSource": "trained_imported",
            "modelStatus": runtime.status,
            "modelName": IMPORTED_MODEL_NAME,
            "bundleManifest": _compact_manifest(runtime.manifest or {}),
            "metrics": _compact_metrics(runtime.metrics or {}),
            "thresholdConfigLoaded": runtime.discovery.threshold_config_loaded,
            "labelsCount": len(labels),
        }
        return {
            "task": TASK_DIR_NAME,
            "selected_issues": selected_issues,
            "top_issues": top_issues,
            "probabilities": probabilities if include_probabilities else {},
            "model_source": "trained_imported",
            "model_status": runtime.status,
            "threshold_used": round(default_threshold, 4),
            "model_name": IMPORTED_MODEL_NAME,
            "metadata": metadata if include_metadata else {},
            "legal_authority_warning": LEGAL_AUTHORITY_WARNING,
        }
    except Exception as exc:
        logger.warning("TRAINED_LEGAL_ISSUE_MODEL_LOAD_FAILED_FALLING_BACK inference_error=%s", exc)
        return _fallback_legal_issue_prediction(text, status="trained_imported_load_failed", top_k=top_k, threshold=threshold)


def get_legal_issue_model_health() -> dict[str, Any]:
    discovery = discover_imported_legal_issue_model()
    cached_loaded = _IMPORTED_LEGAL_ISSUE_RUNTIME is not None and _IMPORTED_LEGAL_ISSUE_RUNTIME.model is not None
    status = "trained_imported_loaded" if cached_loaded else (
        "trained_imported_loaded" if discovery.found else ("trained_imported_invalid" if discovery.zip_found else "trained_imported_not_found")
    )
    return {
        "task": TASK_DIR_NAME,
        "available": discovery.found,
        "model_source": "trained_imported" if discovery.found else "demo_fallback",
        "model_status": status if discovery.found else "demo_fallback",
        "zip_found": discovery.zip_found,
        "extracted": discovery.extracted,
        "bundle_root": str(discovery.bundle_root or ""),
        "model_dir_exists": discovery.model_dir_exists,
        "tokenizer_dir_exists": discovery.tokenizer_dir_exists,
        "label_mapping_loaded": discovery.label_mapping_loaded,
        "threshold_config_loaded": discovery.threshold_config_loaded,
        "metrics_loaded": discovery.metrics_loaded,
        "manifest_loaded": discovery.manifest_loaded,
        "required_files_valid": discovery.required_files_valid,
        "labels_count": discovery.labels_count,
        "reason": discovery.reason,
        "legal_authority_warning": LEGAL_AUTHORITY_WARNING,
    }


def _imported_primary_metric(discovery: LegalIssueModelDiscovery) -> float:
    metrics = _read_json(discovery.metrics_path)
    for group_name in ["test_tuned_threshold", "test_default_threshold_0_5", "validation_default_threshold_0_5", "test", "validation"]:
        group = metrics.get(group_name, {})
        if isinstance(group, dict):
            for key in ["micro_f1", "eval_micro_f1", "eval_f1_micro", "macro_f1", "eval_macro_f1", "eval_f1_macro", "eval_subset_accuracy"]:
                if isinstance(group.get(key), int | float):
                    return float(group[key])
    for key in ["primaryMetric", "primary_metric", "f1_micro", "micro_f1"]:
        if isinstance(metrics.get(key), int | float):
            return float(metrics[key])
    return 0.0


def _write_imported_reference_dataset(discovery: LegalIssueModelDiscovery, labels: list[str]) -> Path:
    rows = [
        {
            "id": f"imported-legal-issue:{index}",
            "case_id": f"imported-legal-issue:{index}",
            "task_name": MlTaskName.LEGAL_ISSUE_CLASSIFIER.value,
            "labels": [label],
            "label_source": "imported_colab_manifest",
            "label_confidence": 0.75,
            "split": "train" if index % 5 else "test",
            "language": "English/Urdu",
            "source_view": "imported_model_reference",
            "text": "Reference row for the imported XLM-R legal issue classifier.",
            "normalized_text": "reference row for imported xlmr legal issue classifier",
            "structured_features": {"is_external_model_registry_row": True, "multi_label": True},
        }
        for index, label in enumerate(labels or ["unknown"])
    ]
    path = datasets_root() / "imported_legal_issue_xlmr_reference" / "records.jsonl"
    write_jsonl(path, rows)
    return path


def ensure_imported_legal_issue_model_record(db: Session) -> MlModel | None:
    discovery = discover_imported_legal_issue_model()
    if not discovery.found or not discovery.task_dir:
        return None

    label_mapping = _read_json(discovery.label_mapping_path)
    labels, _, _ = _parse_label_mapping(label_mapping)
    metrics = _read_json(discovery.metrics_path)
    manifest = _read_json(discovery.manifest_path)
    reference_dataset_path = _write_imported_reference_dataset(discovery, labels)
    dataset = db.scalar(
        select(MlDataset).where(
            MlDataset.task_name == MlTaskName.LEGAL_ISSUE_CLASSIFIER,
            MlDataset.version == IMPORTED_DATASET_VERSION,
        )
    )
    if dataset is None:
        dataset = MlDataset(
            task_name=MlTaskName.LEGAL_ISSUE_CLASSIFIER,
            name="Imported XLM-R Legal Issue Reference Dataset",
            version=IMPORTED_DATASET_VERSION,
            status=MlDatasetStatus.READY,
            record_count=len(labels),
            label_strategy="Imported multi-label issue labels; weak/dataset-derived and not legally authoritative.",
            split_strategy="Imported Colab training bundle reference; final training data remains external.",
            data_path=str(reference_dataset_path),
            report_path=str(discovery.metrics_path or ""),
            report_json={"labels": labels, "metrics": _compact_metrics(metrics)},
            notes="Read-only registry row for an externally trained multi-label legal issue classifier.",
            metadata_json={"importedLegalIssueDataset": True, "source": "colab_trained_bundle", "manifest": manifest},
        )
        db.add(dataset)
        db.flush()
    else:
        dataset.record_count = len(labels) or dataset.record_count
        dataset.data_path = str(reference_dataset_path)
        dataset.report_path = str(discovery.metrics_path or "")
        dataset.report_json = {"labels": labels, "metrics": _compact_metrics(metrics)}
        db.add(dataset)
        db.flush()

    existing_model = db.scalar(
        select(MlModel).where(
            MlModel.task_name == MlTaskName.LEGAL_ISSUE_CLASSIFIER,
            MlModel.name == IMPORTED_MODEL_NAME,
        )
    )
    common_metrics = {**metrics, "primaryMetric": round(_imported_primary_metric(discovery), 4)}
    common_config = {
        "modelSource": "trained_imported",
        "modelStatus": "trained_imported_loaded",
        "multiLabel": True,
        "activation": "sigmoid",
        "thresholdConfigLoaded": discovery.threshold_config_loaded,
        "legalAuthorityWarning": LEGAL_AUTHORITY_WARNING,
    }
    common_metadata = {
        "importedLegalIssueModel": True,
        "modelSource": "trained_imported",
        "manifestPath": str(discovery.manifest_path or ""),
        "legalIssueDir": str(discovery.task_dir),
        "labelsCount": len(labels),
        "legalAuthorityWarning": LEGAL_AUTHORITY_WARNING,
    }
    if existing_model:
        existing_model.dataset_id = dataset.id
        existing_model.artifact_path = str(discovery.model_dir or "")
        existing_model.metrics_path = str(discovery.metrics_path or "")
        existing_model.metrics_json = common_metrics
        existing_model.config_json = {**(existing_model.config_json or {}), **common_config}
        existing_model.label_schema = labels
        existing_model.metadata_json = {**(existing_model.metadata_json or {}), **common_metadata}
        db.add(existing_model)
        db.commit()
        db.refresh(existing_model)
        return existing_model

    model = MlModel(
        dataset_id=dataset.id,
        task_name=MlTaskName.LEGAL_ISSUE_CLASSIFIER,
        model_family=MlModelFamily.TRANSFORMER,
        name=IMPORTED_MODEL_NAME,
        status=MlModelStatus.READY,
        artifact_path=str(discovery.model_dir or ""),
        metrics_path=str(discovery.metrics_path or ""),
        metrics_json=common_metrics,
        config_json=common_config,
        label_schema=labels,
        training_summary=(
            "Imported Colab-trained XLM-RoBERTa multi-label legal issue classifier. "
            "Experimental signal for research triage, not legal authority."
        ),
        metadata_json=common_metadata,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
