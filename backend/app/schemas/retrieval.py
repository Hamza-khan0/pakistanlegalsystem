from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enums import EmbeddingIndexStatus, RetrievalMode
from app.schemas.base import APIModel
from app.schemas.legal_sources import GroundingSourceRead


class EmbeddingIndexRead(APIModel):
    id: str
    name: str
    retrieval_mode: RetrievalMode = Field(serialization_alias="retrievalMode")
    model_name: str = Field(serialization_alias="modelName")
    status: EmbeddingIndexStatus
    corpus_version: str = Field(serialization_alias="corpusVersion")
    index_path: str = Field(serialization_alias="indexPath")
    vector_dimension: int = Field(serialization_alias="vectorDimension")
    source_count: int = Field(serialization_alias="sourceCount")
    metadata_json: dict[str, Any] = Field(default_factory=dict, serialization_alias="metadataJson")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class RetrievalBuildRequest(APIModel):
    model_name: str | None = Field(default=None, serialization_alias="modelName")


class RetrievalSearchRequest(APIModel):
    query: str
    task_type: str | None = Field(default=None, serialization_alias="taskType")
    case_id: str | None = Field(default=None, serialization_alias="caseId")
    language: str | None = None
    limit: int = 8


class RetrievalSearchRead(APIModel):
    query: str
    mode: RetrievalMode
    status: str
    summary: str
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    sources: list[GroundingSourceRead] = Field(default_factory=list)


class RetrievalLeaderboardEntry(APIModel):
    mode: str
    query: str
    top_labels: list[str] = Field(default_factory=list, serialization_alias="topLabels")
    source_type_mix: dict[str, int] = Field(default_factory=dict, serialization_alias="sourceTypeMix")
    average_score: float = Field(serialization_alias="averageScore")
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class RetrievalLeaderboardRead(APIModel):
    generated_at: datetime = Field(serialization_alias="generatedAt")
    entries: list[RetrievalLeaderboardEntry] = Field(default_factory=list)


class RunGroundingDiagnosticsRead(APIModel):
    run_id: str = Field(serialization_alias="runId")
    retrieval_mode: str = Field(serialization_alias="retrievalMode")
    grounding_status: str = Field(serialization_alias="groundingStatus")
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    sources: list[GroundingSourceRead] = Field(default_factory=list)
