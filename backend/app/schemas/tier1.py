from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.enums import MlTaskName
from app.schemas.base import APIModel


class Tier1ImportResult(APIModel):
    status: str
    message: str
    source_type: str
    source_name: str
    imported_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    label_count: int = 0
    warnings: list[str] = []
    metadata_json: dict[str, Any] = {}


class Tier1DocumentRead(APIModel):
    id: str
    source_type: str
    source_name: str
    external_id: str
    file_path: str
    title: str
    raw_text: str
    normalized_text: str
    language: str
    document_type: str
    court: str
    date: str
    citation: str
    case_number: str
    parties: str
    metadata_json: dict[str, Any]
    import_status: str
    created_at: datetime
    updated_at: datetime


class Tier1LabelRead(APIModel):
    id: str
    document_id: str
    document_title: str
    task_name: MlTaskName
    label: str
    label_source: str
    confidence_score: float
    evidence_text: str
    rule_name: str
    needs_review: bool
    reviewed: bool
    reviewer_note: str
    created_at: datetime
    updated_at: datetime


class Tier1LabelUpdate(APIModel):
    label: str | None = None
    reviewed: bool | None = None
    needs_review: bool | None = None
    reviewer_note: str | None = None


class Tier1DatasetBuildResult(APIModel):
    status: str
    message: str
    datasets: list[dict[str, Any]]
    warnings: list[str] = []


class Tier1ReadinessRead(APIModel):
    task_name: MlTaskName
    status: str
    total_labels: int
    reviewed_labels: int
    weak_labels: int
    usable_labels: int
    class_distribution: dict[str, int]
    split_counts: dict[str, int]
    warnings: list[str]
    recommendations: list[str]


class Tier1ExportResult(APIModel):
    status: str
    message: str
    export_dir: str
    zip_path: str
    dataset_counts: dict[str, dict[str, int]]
    warnings: list[str] = []


class Tier1ReportRead(APIModel):
    generated_at: str
    document_count: int
    label_count: int
    source_type_counts: dict[str, int]
    language_counts: dict[str, int]
    review_counts: dict[str, int]
    readiness: list[Tier1ReadinessRead]
