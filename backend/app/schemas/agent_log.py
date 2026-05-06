from datetime import datetime

from pydantic import Field

from app.models.enums import AgentRunStatus
from app.schemas.base import APIModel


class AgentRunLogBase(APIModel):
    agent_name: str = Field(serialization_alias="agentName")
    title: str = ""
    task_type: str = Field(serialization_alias="taskType")
    input_summary: str = Field(default="", serialization_alias="inputSummary")
    output_summary: str = Field(default="", serialization_alias="outputSummary")
    status: AgentRunStatus
    confidence_score: float | None = Field(default=None, serialization_alias="confidenceScore")
    citations: list[str] = Field(default_factory=list)
    next_action: str = Field(default="", serialization_alias="nextAction")
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")


class AgentRunLogCreate(AgentRunLogBase):
    started_at: datetime | None = Field(default=None, serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class AgentRunLogRead(AgentRunLogBase):
    id: str
    case_id: str = Field(serialization_alias="caseId")
    started_at: datetime = Field(serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    confidence: str = ""
