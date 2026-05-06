from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import APIModel


class DatasetReadinessRead(APIModel):
    dataset_id: str = Field(serialization_alias="datasetId")
    task_name: str = Field(serialization_alias="taskName")
    dataset_name: str = Field(serialization_alias="datasetName")
    dataset_version: str = Field(serialization_alias="datasetVersion")
    status: str
    score: int
    total_examples: int = Field(serialization_alias="totalExamples")
    unique_cases: int = Field(serialization_alias="uniqueCases")
    class_distribution: dict[str, int] = Field(default_factory=dict, serialization_alias="classDistribution")
    class_imbalance_ratio: float = Field(serialization_alias="classImbalanceRatio")
    split_counts: dict[str, int] = Field(default_factory=dict, serialization_alias="splitCounts")
    label_source_distribution: dict[str, int] = Field(default_factory=dict, serialization_alias="labelSourceDistribution")
    language_distribution: dict[str, int] = Field(default_factory=dict, serialization_alias="languageDistribution")
    source_view_distribution: dict[str, int] = Field(default_factory=dict, serialization_alias="sourceViewDistribution")
    missing_text_examples: int = Field(serialization_alias="missingTextExamples")
    near_empty_examples: int = Field(serialization_alias="nearEmptyExamples")
    duplicate_examples: int = Field(serialization_alias="duplicateExamples")
    weak_label_percentage: float = Field(serialization_alias="weakLabelPercentage")
    low_ocr_confidence_percentage: float = Field(serialization_alias="lowOcrConfidencePercentage")
    leakage_case_count: int = Field(serialization_alias="leakageCaseCount")
    leakage_case_ids: list[str] = Field(default_factory=list, serialization_alias="leakageCaseIds")
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class EvaluationReportRead(APIModel):
    id: str
    report_type: str = Field(serialization_alias="reportType")
    title: str
    task_name: str | None = Field(default=None, serialization_alias="taskName")
    dataset_id: str | None = Field(default=None, serialization_alias="datasetId")
    model_id: str | None = Field(default=None, serialization_alias="modelId")
    payload_json: dict[str, Any] = Field(default_factory=dict, serialization_alias="payloadJson")
    markdown_path: str | None = Field(default=None, serialization_alias="markdownPath")
    created_at: datetime = Field(serialization_alias="createdAt")


class RetrievalBenchmarkResultRead(APIModel):
    query: str
    task_type: str = Field(serialization_alias="taskType")
    mode: str
    top_k: int = Field(serialization_alias="topK")
    expected_labels: list[str] = Field(default_factory=list, serialization_alias="expectedLabels")
    metrics_json: dict[str, Any] = Field(default_factory=dict, serialization_alias="metricsJson")
    results_json: list[dict[str, Any]] = Field(default_factory=list, serialization_alias="resultsJson")
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class RetrievalBenchmarkRunRead(APIModel):
    id: str
    name: str
    retrieval_modes_compared: list[str] = Field(default_factory=list, serialization_alias="retrievalModesCompared")
    query_count: int = Field(serialization_alias="queryCount")
    metrics_json: dict[str, Any] = Field(default_factory=dict, serialization_alias="metricsJson")
    created_at: datetime = Field(serialization_alias="createdAt")
    results: list[RetrievalBenchmarkResultRead] = Field(default_factory=list)


class CalibrationRecordRead(APIModel):
    model_id: str = Field(serialization_alias="modelId")
    task_name: str = Field(serialization_alias="taskName")
    calibration_method: str = Field(serialization_alias="calibrationMethod")
    sample_count: int = Field(serialization_alias="sampleCount")
    has_calibrated_scores: bool = Field(serialization_alias="hasCalibratedScores")
    supported_methods: list[str] = Field(default_factory=list, serialization_alias="supportedMethods")
    metrics_json: dict[str, Any] = Field(default_factory=dict, serialization_alias="metricsJson")
    reliability_json: dict[str, Any] = Field(default_factory=dict, serialization_alias="reliabilityJson")
    notes: str
    created_at: datetime = Field(serialization_alias="createdAt")


class ChamberRunQualityRead(APIModel):
    run_id: str = Field(serialization_alias="runId")
    case_id: str = Field(serialization_alias="caseId")
    status: str
    retrieval_mode: str = Field(serialization_alias="retrievalMode")
    source_count_retrieved: int = Field(serialization_alias="sourceCountRetrieved")
    source_count_relied_on: int = Field(serialization_alias="sourceCountReliedOn")
    grounding_strength: str = Field(serialization_alias="groundingStrength")
    critic_flags: list[str] = Field(default_factory=list, serialization_alias="criticFlags")
    unsupported_claim_warnings: list[str] = Field(default_factory=list, serialization_alias="unsupportedClaimWarnings")
    procedural_dependencies: list[str] = Field(default_factory=list, serialization_alias="proceduralDependencies")
    memory_usage_count: int = Field(serialization_alias="memoryUsageCount")
    final_confidence_score: float | None = Field(default=None, serialization_alias="finalConfidenceScore")
    recommendations: list[str] = Field(default_factory=list)


class CaseQualitySummaryRead(APIModel):
    case_id: str = Field(serialization_alias="caseId")
    recent_run_count: int = Field(serialization_alias="recentRunCount")
    average_run_confidence: float | None = Field(default=None, serialization_alias="averageRunConfidence")
    latest_run_quality: ChamberRunQualityRead | None = Field(default=None, serialization_alias="latestRunQuality")
    grounded_run_count: int = Field(serialization_alias="groundedRunCount")
    critical_warning_count: int = Field(serialization_alias="criticalWarningCount")
    quality_warnings: list[str] = Field(default_factory=list, serialization_alias="qualityWarnings")
