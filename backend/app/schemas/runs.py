from datetime import datetime

from pydantic import Field

from app.models.enums import ChamberRunStatus, ChamberRunStepStatus, ChamberTaskType
from app.schemas.base import APIModel
from app.schemas.legal_sources import GroundingSourceRead


class MemorySourceRead(APIModel):
    source_id: str = Field(serialization_alias="sourceId")
    source_type: str = Field(serialization_alias="sourceType")
    title: str
    detail: str = ""
    excerpt: str = ""


class ChamberRunStepRead(APIModel):
    id: str
    run_id: str = Field(serialization_alias="runId")
    step_order: int = Field(serialization_alias="stepOrder")
    agent_name: str = Field(serialization_alias="agentName")
    task_label: str = Field(serialization_alias="taskLabel")
    input_summary: str = Field(serialization_alias="inputSummary")
    output_summary: str = Field(serialization_alias="outputSummary")
    full_output: str = Field(serialization_alias="fullOutput")
    structured_json: dict = Field(default_factory=dict, serialization_alias="structuredJson")
    status: ChamberRunStepStatus
    confidence_score: float | None = Field(default=None, serialization_alias="confidenceScore")
    source_artifact_ids: list[str] = Field(
        default_factory=list,
        serialization_alias="sourceArtifactIds",
    )
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")
    created_at: datetime = Field(serialization_alias="createdAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class ChamberRunCreate(APIModel):
    instruction: str
    task_type: ChamberTaskType | None = Field(default=None, serialization_alias="taskType")
    selected_workflow: str | None = Field(default=None, serialization_alias="selectedWorkflow")


class ChamberRunSummaryRead(APIModel):
    id: str
    case_id: str = Field(serialization_alias="caseId")
    task_type: ChamberTaskType = Field(serialization_alias="taskType")
    user_instruction: str = Field(serialization_alias="userInstruction")
    selected_workflow: str = Field(serialization_alias="selectedWorkflow")
    status: ChamberRunStatus
    final_summary: str = Field(serialization_alias="finalSummary")
    confidence_score: float | None = Field(default=None, serialization_alias="confidenceScore")
    agent_names: list[str] = Field(default_factory=list, serialization_alias="agentNames")
    memory_sources: list[MemorySourceRead] = Field(
        default_factory=list,
        serialization_alias="memorySources",
    )
    critic_summary: str = Field(default="", serialization_alias="criticSummary")
    final_artifact_id: str | None = Field(default=None, serialization_alias="finalArtifactId")
    linked_draft_id: str | None = Field(default=None, serialization_alias="linkedDraftId")
    linked_research_entry_id: str | None = Field(
        default=None,
        serialization_alias="linkedResearchEntryId",
    )
    grounding_status: str = Field(default="Retrieval not used", serialization_alias="groundingStatus")
    retrieval_mode: str = Field(default="Lexical", serialization_alias="retrievalMode")
    retrieval_diagnostics: dict = Field(default_factory=dict, serialization_alias="retrievalDiagnostics")
    legal_retrieval_query: str = Field(default="", serialization_alias="legalRetrievalQuery")
    legal_source_count: int = Field(default=0, serialization_alias="legalSourceCount")
    legal_sources: list[GroundingSourceRead] = Field(
        default_factory=list,
        serialization_alias="legalSources",
    )
    started_at: datetime = Field(serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class ChamberRunRead(ChamberRunSummaryRead):
    final_output: str = Field(serialization_alias="finalOutput")
    steps: list[ChamberRunStepRead] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")


class AgentActivityRead(APIModel):
    step_id: str = Field(serialization_alias="stepId")
    run_id: str = Field(serialization_alias="runId")
    case_id: str = Field(serialization_alias="caseId")
    case_title: str = Field(serialization_alias="caseTitle")
    agent_name: str = Field(serialization_alias="agentName")
    task_label: str = Field(serialization_alias="taskLabel")
    status: ChamberRunStepStatus
    output_summary: str = Field(serialization_alias="outputSummary")
    confidence_score: float | None = Field(default=None, serialization_alias="confidenceScore")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
