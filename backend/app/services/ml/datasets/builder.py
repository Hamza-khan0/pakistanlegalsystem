from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.case import Case
from app.models.chamber_run import ChamberRun
from app.models.enums import MlDatasetStatus, MlTaskName
from app.models.intelligence_artifact import IntelligenceArtifact
from app.models.ml_dataset import MlDataset
from app.services.corpus.normalization import detect_language, normalize_text
from app.services.ml.datasets.features import build_case_text, build_structured_features
from app.services.ml.datasets.labeling import get_case_label
from app.services.ml.datasets.reports import build_dataset_report
from app.services.ml.datasets.splits import deterministic_split
from app.services.ml.registry import dataset_dir, write_json, write_jsonl

SUPERVISED_PREDICTION_TASKS = [
    MlTaskName.CASE_OUTCOME,
    MlTaskName.MAINTAINABILITY,
    MlTaskName.RISK_SCORING,
    MlTaskName.CASE_TYPE,
]


@dataclass(slots=True)
class DatasetBuildResult:
    dataset: MlDataset
    records: list[dict[str, Any]]


def _dataset_query():
    return (
        select(Case)
        .where(Case.archived.is_(False))
        .options(
            selectinload(Case.documents),
            selectinload(Case.notes),
            selectinload(Case.research_entries),
            selectinload(Case.drafts),
            selectinload(Case.intelligence_artifacts).selectinload(IntelligenceArtifact.grounding_links),
            selectinload(Case.chamber_runs).selectinload(ChamberRun.grounding_links),
        )
    )


def _variant_rows(case: Case) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("case_core", build_case_text(case))]

    for document in case.documents:
        text = "\n".join(
            part for part in [
                document.name,
                document.summary,
                document.extracted_text or document.extracted_text_preview,
                " ".join(document.tags),
            ]
            if part
        ).strip()
        if text:
            rows.append((f"document:{document.id}", text))

    for note in case.notes:
        text = "\n".join([note.title, note.note_type.value, note.content]).strip()
        if text:
            rows.append((f"note:{note.id}", text))

    for entry in case.research_entries:
        text = "\n".join(
            part
            for part in [
                entry.title,
                entry.query,
                entry.summary,
                " ".join(entry.citations),
                entry.next_question,
            ]
            if part
        ).strip()
        if text:
            rows.append((f"research:{entry.id}", text))

    for draft in case.drafts:
        text = "\n".join(
            part for part in [draft.title, draft.summary, draft.content] if part
        ).strip()
        if text:
            rows.append((f"draft:{draft.id}", text))

    for artifact in case.intelligence_artifacts:
        text = "\n".join(part for part in [artifact.title, artifact.content] if part).strip()
        if text:
            rows.append((f"artifact:{artifact.id}", text))

    for run in case.chamber_runs:
        text = "\n".join(
            part for part in [run.user_instruction, run.final_summary, run.final_output] if part
        ).strip()
        if text:
            rows.append((f"run:{run.id}", text))

    return [(source_view, text) for source_view, text in rows if text.strip()]


def _build_records_for_task(case: Case, task_name: MlTaskName) -> list[dict[str, Any]]:
    label_info = get_case_label(case.id, task_name)
    if label_info is None:
        return []

    base_structured = build_structured_features(case)
    records: list[dict[str, Any]] = []
    for index, (source_view, raw_text) in enumerate(_variant_rows(case), start=1):
        normalized_text = normalize_text(raw_text)
        record_id = f"{task_name.value}:{case.id}:{source_view}:{index}"
        records.append(
            {
                "id": record_id,
                "case_id": case.id,
                "task_name": task_name.value,
                "label": label_info.label,
                "label_source": label_info.label_source,
                "label_confidence": label_info.confidence,
                "source_view": source_view,
                "language": detect_language(raw_text),
                "split": deterministic_split(record_id).value,
                "text": raw_text,
                "normalized_text": normalized_text,
                "structured_features": {
                    **base_structured,
                    "source_view": source_view.split(":")[0],
                    "text_length": len(raw_text),
                    "normalized_length": len(normalized_text),
                },
                "metadata": {
                    "caseNumber": case.case_number,
                    "forum": case.forum,
                    "matterType": case.matter_type,
                    "priority": case.priority.value,
                    "status": case.status.value,
                },
            }
        )
    return records


def _dataset_name(task_name: MlTaskName) -> str:
    return {
        MlTaskName.CASE_OUTCOME: "Case Outcome Prediction Dataset",
        MlTaskName.MAINTAINABILITY: "Maintainability Prediction Dataset",
        MlTaskName.RISK_SCORING: "Risk Scoring Dataset",
        MlTaskName.CASE_TYPE: "Case Type Classification Dataset",
        MlTaskName.LEGAL_ISSUE_CLASSIFIER: "Legal Issue Multi-Label Classifier Reference Dataset",
    }[task_name]


def _upsert_dataset(
    db: Session,
    *,
    task_name: MlTaskName,
    records: list[dict[str, Any]],
) -> MlDataset:
    dataset = db.scalar(select(MlDataset).where(MlDataset.task_name == task_name))
    if dataset is None:
        dataset = MlDataset(
            task_name=task_name,
            name=_dataset_name(task_name),
            version="pending",
        )
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
    dataset.label_strategy = "Manual case seed labels projected across case-linked supervised views"
    dataset.split_strategy = "Deterministic record hashing with case id tracked for leakage review"
    dataset.data_path = str(data_path)
    dataset.report_path = str(report_path)
    dataset.report_json = report_json
    dataset.notes = (
        "Labels originate from seeded case-level supervision. Records are generated from case summaries, "
        "documents, notes, research, drafts, intelligence artifacts, and chamber runs."
    )
    dataset.metadata_json = {
        "tasksSupported": [task_name.value],
        "caseIds": sorted({record["case_id"] for record in records}),
        "hasWeakSupervision": False,
        "hasProjectedLabels": True,
    }
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def build_single_dataset(db: Session, task_name: MlTaskName) -> DatasetBuildResult:
    cases = list(db.scalars(_dataset_query()).all())
    records: list[dict[str, Any]] = []
    for case in cases:
        records.extend(_build_records_for_task(case, task_name))
    dataset = _upsert_dataset(db, task_name=task_name, records=records)
    return DatasetBuildResult(dataset=dataset, records=records)


def build_ml_datasets(db: Session, task_name: MlTaskName | None = None) -> list[MlDataset]:
    tasks = [task_name] if task_name else SUPERVISED_PREDICTION_TASKS
    datasets: list[MlDataset] = []
    for next_task in tasks:
        result = build_single_dataset(db, next_task)
        datasets.append(result.dataset)
    return datasets
