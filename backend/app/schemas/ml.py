from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enums import MlDatasetStatus, MlModelFamily, MlModelStatus, MlTaskName
from app.schemas.base import APIModel


class MlDatasetBuildRequest(APIModel):
    task_name: MlTaskName | None = None
    rebuild: bool = True


class MlDatasetRead(APIModel):
    id: str
    task_name: MlTaskName
    name: str
    version: str
    status: MlDatasetStatus
    record_count: int
    label_strategy: str
    split_strategy: str
    data_path: str
    report_path: str
    report_json: dict[str, Any]
    notes: str
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MlTrainRequest(APIModel):
    dataset_id: str
    model_family: MlModelFamily
    model_name: str | None = None
    hyperparameters: dict[str, Any] = Field(default_factory=dict)


class MlModelRead(APIModel):
    id: str
    dataset_id: str
    task_name: MlTaskName
    model_family: MlModelFamily
    name: str
    status: MlModelStatus
    artifact_path: str
    metrics_path: str
    metrics_json: dict[str, Any]
    config_json: dict[str, Any]
    label_schema: list[str]
    training_summary: str
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MlPredictRequest(APIModel):
    case_id: str
    task_name: MlTaskName | None = None
    model_id: str | None = None


class CaseTypeTextPredictRequest(APIModel):
    text: str = Field(min_length=1)
    include_probabilities: bool = True
    include_metadata: bool = True


class CaseTypeTextPredictionRead(APIModel):
    task: str
    predicted_label: str
    confidence: float
    probabilities: dict[str, float]
    model_source: str
    model_status: str
    model_name: str
    bundle_manifest: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    legal_authority_warning: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LegalIssuePredictionRequest(APIModel):
    text: str = Field(min_length=1)
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    top_k: int | None = Field(default=10, ge=1)
    include_probabilities: bool = True
    include_metadata: bool = True


class LegalIssueItem(APIModel):
    label: str
    probability: float
    threshold: float


class LegalIssuePredictionRead(APIModel):
    task: str
    selected_issues: list[LegalIssueItem]
    top_issues: list[LegalIssueItem]
    probabilities: dict[str, float]
    model_source: str
    model_status: str
    threshold_used: float
    model_name: str
    legal_authority_warning: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MlRuntimeHealthRead(APIModel):
    task: str
    available: bool
    model_source: str
    model_status: str
    zip_found: bool
    extracted: bool
    bundle_root: str
    model_dir_exists: bool
    tokenizer_dir_exists: bool
    label_mapping_loaded: bool
    metrics_loaded: bool
    manifest_loaded: bool
    required_files_valid: bool
    reason: str
    legal_authority_warning: str


class LegalIssueModelHealthRead(APIModel):
    task: str
    available: bool
    model_source: str
    model_status: str
    zip_found: bool
    extracted: bool
    bundle_root: str
    model_dir_exists: bool
    tokenizer_dir_exists: bool
    label_mapping_loaded: bool
    threshold_config_loaded: bool
    metrics_loaded: bool
    manifest_loaded: bool
    required_files_valid: bool
    labels_count: int
    reason: str
    legal_authority_warning: str


class CasePredictionRead(APIModel):
    id: str
    case_id: str
    model_id: str
    task_name: MlTaskName
    predicted_label: str
    confidence: float
    probabilities_json: dict[str, float]
    input_summary: str
    warning_text: str
    metadata_json: dict[str, Any]
    created_at: datetime
    model_name: str
    model_family: MlModelFamily
    dataset_id: str


class MlLeaderboardEntry(APIModel):
    model_id: str
    name: str
    model_family: MlModelFamily
    primary_metric: float
    metrics_json: dict[str, Any]
    created_at: datetime


class MlTaskLeaderboardRead(APIModel):
    task_name: MlTaskName
    entries: list[MlLeaderboardEntry]


class MlModelDiagnosticsRead(APIModel):
    model_id: str = Field(serialization_alias="modelId")
    task_name: MlTaskName = Field(serialization_alias="taskName")
    model_family: MlModelFamily = Field(serialization_alias="modelFamily")
    model_name: str = Field(serialization_alias="modelName")
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class PredictionExplanationRead(APIModel):
    prediction_id: str = Field(serialization_alias="predictionId")
    task_name: MlTaskName = Field(serialization_alias="taskName")
    predicted_label: str = Field(serialization_alias="predictedLabel")
    confidence: float
    model_family: str = Field(serialization_alias="modelFamily")
    model_name: str = Field(serialization_alias="modelName")
    explanation_note: str = Field(serialization_alias="explanationNote")
    top_probabilities: list[dict[str, Any]] = Field(default_factory=list, serialization_alias="topProbabilities")
    structured_signals: dict[str, Any] = Field(default_factory=dict, serialization_alias="structuredSignals")
    diagnostics: dict[str, Any] = Field(default_factory=dict)
