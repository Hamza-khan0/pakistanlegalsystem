from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import MlDatasetStatus, MlTaskName
from app.models.ml_dataset import MlDataset
from app.models.tier1_document import Tier1Document
from app.models.tier1_label import Tier1Label
from app.services.ml.datasets.reports import build_dataset_report
from app.services.ml.datasets.splits import deterministic_split
from app.services.ml.registry import dataset_dir, write_json, write_jsonl


TASK_LABELS = {
    MlTaskName.CASE_OUTCOME: {"allowed", "dismissed", "partly_allowed", "remanded", "disposed", "withdrawn"},
    MlTaskName.MAINTAINABILITY: {"likely_maintainable", "objection_prone", "not_maintainable", "uncertain"},
    MlTaskName.RISK_SCORING: {"low", "medium", "high"},
    MlTaskName.CASE_TYPE: {
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
    },
}

TIER1_SUPPORTED_TASKS = (
    MlTaskName.CASE_OUTCOME,
    MlTaskName.MAINTAINABILITY,
    MlTaskName.RISK_SCORING,
    MlTaskName.CASE_TYPE,
)


def _dataset_name(task_name: MlTaskName) -> str:
    return {
        MlTaskName.CASE_OUTCOME: "Tier 1 Case Outcome Dataset",
        MlTaskName.MAINTAINABILITY: "Tier 1 Maintainability Dataset",
        MlTaskName.RISK_SCORING: "Tier 1 Risk Scoring Dataset",
        MlTaskName.CASE_TYPE: "Tier 1 Case Type Dataset",
    }.get(task_name, f"Tier 1 {task_name.value.replace('_', ' ').title()} Dataset")


def _structured_features(document: Tier1Document, label: Tier1Label) -> dict[str, Any]:
    missing_fields = sum(
        1
        for value in [document.court, document.date, document.citation, document.case_number, document.parties]
        if not value.strip()
    )
    return {
        "forum": document.court or "Unknown",
        "matter_type": document.document_type or "Judgment",
        "status": "Tier1",
        "priority": "Medium",
        "filing_stage": "judgment",
        "source_view": "tier1_document",
        "tag_count": 0,
        "issue_count": 0,
        "risk_flag_count": 1 if label.needs_review else 0,
        "procedural_alert_count": 0,
        "document_count": 1,
        "note_count": 0,
        "research_count": 0,
        "draft_count": 0,
        "artifact_count": 0,
        "run_count": 0,
        "grounded_artifact_count": 0,
        "grounded_run_count": 0,
        "grounding_link_count": 0,
        "avg_document_ocr_confidence": float(document.metadata_json.get("ocr_confidence") or 1.0),
        "has_hearing_date": 0,
        "text_length": len(document.raw_text),
        "normalized_length": len(document.normalized_text),
        "missing_metadata_count": missing_fields,
        "label_confidence": label.confidence_score,
        "is_reviewed_label": 1 if label.reviewed else 0,
    }


def _query_documents(db: Session) -> list[Tier1Document]:
    return list(
        db.scalars(
            select(Tier1Document)
            .options(selectinload(Tier1Document.labels))
            .order_by(Tier1Document.created_at.desc())
        ).all()
    )


def build_records_for_task(db: Session, task_name: MlTaskName) -> list[dict[str, Any]]:
    allowed = TASK_LABELS.get(task_name)
    if allowed is None:
        return []
    records: list[dict[str, Any]] = []
    for document in _query_documents(db):
        labels = [label for label in document.labels if label.task_name == task_name]
        if not labels:
            continue
        label = sorted(labels, key=lambda item: (not item.reviewed, item.needs_review, -item.confidence_score))[0]
        if label.label == "unknown" or label.label not in allowed:
            continue
        split = deterministic_split(document.id).value
        records.append(
            {
                "id": f"tier1:{task_name.value}:{document.id}",
                "case_id": document.id,
                "document_id": document.id,
                "task_name": task_name.value,
                "label": label.label,
                "label_source": "manual_review" if label.reviewed else label.label_source,
                "label_confidence": label.confidence_score,
                "source_view": "tier1_document",
                "language": document.language,
                "split": split,
                "text": document.raw_text,
                "normalized_text": document.normalized_text,
                "structured_features": _structured_features(document, label),
                "metadata": {
                    "sourceType": document.source_type,
                    "sourceName": document.source_name,
                    "title": document.title,
                    "court": document.court,
                    "citation": document.citation,
                    "caseNumber": document.case_number,
                    "evidenceText": label.evidence_text,
                    "ruleName": label.rule_name,
                    "needsReview": label.needs_review,
                    "reviewed": label.reviewed,
                },
            }
        )
    return records


def _upsert_dataset(db: Session, task_name: MlTaskName, records: list[dict[str, Any]]) -> MlDataset:
    task_datasets = list(db.scalars(select(MlDataset).where(MlDataset.task_name == task_name)).all())
    dataset = next((item for item in task_datasets if item.metadata_json.get("tier1") is True), None)
    if dataset is None:
        dataset = MlDataset(task_name=task_name, name=_dataset_name(task_name), version="pending")
        db.add(dataset)
        db.flush()

    artifact_dir = dataset_dir(dataset.id)
    data_path = artifact_dir / "records.jsonl"
    report_path = artifact_dir / "report.json"
    report_json = build_dataset_report(records)
    write_jsonl(data_path, records)
    write_json(report_path, report_json)

    dataset.name = _dataset_name(task_name)
    dataset.version = datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M%S")
    dataset.status = MlDatasetStatus.READY
    dataset.record_count = len(records)
    dataset.label_strategy = "Tier 1 reviewed labels preferred, weak-supervision labels included when not reviewed"
    dataset.split_strategy = "Deterministic 70/15/15 split by document id hash to avoid duplicate document leakage"
    dataset.data_path = str(data_path)
    dataset.report_path = str(report_path)
    dataset.report_json = report_json
    dataset.notes = "Tier 1 dataset built from imported legal documents and auditable weak labels."
    dataset.metadata_json = {
        "tier1": True,
        "tasksSupported": [task_name.value],
        "documentIds": sorted({record["document_id"] for record in records}),
        "hasWeakSupervision": any(record["label_source"] == "weak_supervision" for record in records),
        "reviewedLabelCount": sum(1 for record in records if record["metadata"].get("reviewed")),
    }
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def build_tier1_datasets(db: Session, task_name: MlTaskName | None = None) -> dict[str, Any]:
    tasks = [task_name] if task_name else list(TIER1_SUPPORTED_TASKS)
    datasets: list[dict[str, Any]] = []
    warnings: list[str] = []
    for task in tasks:
        records = build_records_for_task(db, task)
        dataset = _upsert_dataset(db, task, records)
        if not records:
            warnings.append(f"No usable non-unknown Tier 1 labels found for {task.value}.")
        datasets.append(
            {
                "id": dataset.id,
                "taskName": dataset.task_name.value,
                "name": dataset.name,
                "recordCount": dataset.record_count,
                "dataPath": dataset.data_path,
                "reportPath": dataset.report_path,
                "reportJson": dataset.report_json,
            }
        )
    return {
        "status": "success",
        "message": f"Built {len(datasets)} Tier 1 datasets.",
        "datasets": datasets,
        "warnings": warnings,
    }


def tier1_readiness(db: Session) -> list[dict[str, Any]]:
    labels = list(db.scalars(select(Tier1Label).options(selectinload(Tier1Label.document))).all())
    by_task: dict[MlTaskName, list[Tier1Label]] = defaultdict(list)
    for label in labels:
        by_task[label.task_name].append(label)

    readiness: list[dict[str, Any]] = []
    for task in TIER1_SUPPORTED_TASKS:
        task_labels = by_task.get(task, [])
        usable = [label for label in task_labels if label.label != "unknown"]
        reviewed = [label for label in usable if label.reviewed]
        weak = [label for label in usable if not label.reviewed]
        class_distribution = Counter(label.label for label in usable)
        split_counts = Counter(deterministic_split(label.document_id).value for label in usable)
        warnings: list[str] = []
        recommendations: list[str] = []
        if len(usable) < 20:
            warnings.append("Fewer than 20 usable labels; this is import-ready but not final-training strong.")
            recommendations.append("Import more Tier 1 documents and audit labels before cloud/GPU training.")
        if len(class_distribution) < 2:
            warnings.append("Only one class is represented after excluding unknown labels.")
            recommendations.append("Add more examples for missing classes.")
        if weak and len(weak) / max(len(usable), 1) > 0.5:
            warnings.append("Most usable labels are still weak supervision.")
            recommendations.append("Review and approve labels in the audit queue.")
        status = "ready_for_manual_training" if len(usable) >= 50 and len(reviewed) >= 20 else "ready_for_import"
        readiness.append(
            {
                "taskName": task.value,
                "status": status,
                "totalLabels": len(task_labels),
                "reviewedLabels": len(reviewed),
                "weakLabels": len(weak),
                "usableLabels": len(usable),
                "classDistribution": dict(class_distribution),
                "splitCounts": dict(split_counts),
                "warnings": warnings,
                "recommendations": recommendations,
            }
        )
    return readiness
